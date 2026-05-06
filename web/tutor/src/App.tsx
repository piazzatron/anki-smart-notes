import { useEffect, useRef, useState } from "react"
import { config } from "./config"
import { parseSSE } from "./sse"

type Role = "user" | "assistant"
type Message = { role: Role; content: string; error?: boolean }

export function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [streaming, setStreaming] = useState(false)
  const logRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Autoscroll to bottom whenever the message list grows or the last
  // message's content changes (streaming token in).
  const lastContent = messages[messages.length - 1]?.content ?? ""
  useEffect(() => {
    const el = logRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages.length, lastContent])

  useEffect(() => {
    inputRef.current?.focus()
  }, [streaming])

  const send = async () => {
    const text = input.trim()
    if (!text || streaming) return
    setInput("")

    const next: Message[] = [
      ...messages,
      { role: "user", content: text },
      { role: "assistant", content: "" },
    ]
    setMessages(next)
    setStreaming(true)

    const history = next
      .slice(0, -1)
      .map(({ role, content }) => ({ role, content }))

    try {
      const res = await fetch(config.serverUrl + "/api/tutor", {
        method: "POST",
        headers: {
          Authorization: "Bearer " + config.jwt,
          "Content-Type": "application/json",
          "x-sn-source": "anki-plugin",
        },
        body: JSON.stringify({ messages: history }),
      })

      if (!res.ok || !res.body) {
        const err = await res.text().catch(() => "")
        setMessages((m) =>
          patchLast(m, {
            content: `Request failed (${res.status}). ${err}`,
            error: true,
          })
        )
        return
      }

      let assistant = ""
      for await (const ev of parseSSE(res.body)) {
        if (ev.event === "delta") {
          assistant += ev.data
          setMessages((m) => patchLast(m, { content: assistant }))
        } else if (ev.event === "error") {
          setMessages((m) =>
            patchLast(m, {
              content: assistant + `\n[error] ${ev.data}`,
              error: true,
            })
          )
        }
      }
    } catch (e) {
      setMessages((m) =>
        patchLast(m, {
          content: `Network error: ${e instanceof Error ? e.message : String(e)}`,
          error: true,
        })
      )
    } finally {
      setStreaming(false)
    }
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="app">
      <header>
        <span className="title">AI Tutor</span>
        <span className="badge">alpha</span>
      </header>

      <div className="log" ref={logRef} aria-live="polite">
        {messages.length === 0 && (
          <div className="empty">
            <div className="empty-title">Ask me anything.</div>
            <div className="empty-sub">
              I'm here to help you study. Try a definition, a comparison, or a
              "quiz me on…".
            </div>
          </div>
        )}
        {messages.map((m, i) => {
          const isLast = i === messages.length - 1
          const isStreaming =
            streaming && isLast && m.role === "assistant" && !m.error
          return (
            <div className={`row ${m.role}`} key={i}>
              <div
                className={[
                  "bubble",
                  m.error ? "error" : "",
                  isStreaming ? "streaming" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {m.content || (isStreaming ? "" : " ")}
              </div>
            </div>
          )
        })}
      </div>

      <footer>
        <textarea
          ref={inputRef}
          value={input}
          rows={1}
          onChange={(e) => {
            setInput(e.target.value)
            const el = e.currentTarget
            el.style.height = "auto"
            el.style.height = Math.min(el.scrollHeight, 160) + "px"
          }}
          onKeyDown={onKeyDown}
          placeholder="Ask anything…"
          disabled={streaming}
        />
        <button onClick={send} disabled={streaming || !input.trim()}>
          {streaming ? "…" : "Send"}
        </button>
      </footer>
      <div className="hint">Enter to send · Shift+Enter for newline</div>
    </div>
  )
}

const patchLast = (m: Message[], patch: Partial<Message>): Message[] =>
  m.map((msg, i) => (i === m.length - 1 ? { ...msg, ...patch } : msg))
