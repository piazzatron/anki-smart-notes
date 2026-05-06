export type SSEEvent = { event: string; data: string }

// Yields one parsed SSE event per chunk. Handles multi-line `data:` payloads
// and the optional single leading space after the colon.
export async function* parseSSE(
  body: ReadableStream<Uint8Array>
): AsyncGenerator<SSEEvent> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buf = ""

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })

    let idx: number
    while ((idx = buf.indexOf("\n\n")) >= 0) {
      const block = buf.slice(0, idx)
      buf = buf.slice(idx + 2)
      if (!block.trim()) continue

      let event = "message"
      const dataLines: string[] = []
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim()
        else if (line.startsWith("data:")) {
          const v = line.slice(5)
          dataLines.push(v.startsWith(" ") ? v.slice(1) : v)
        }
      }
      yield { event, data: dataLines.join("\n") }
    }
  }
}
