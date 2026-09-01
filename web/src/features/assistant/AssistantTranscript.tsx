import ReactMarkdown from "react-markdown"
import type { TFunction } from "i18next"
import { useTranslation } from "react-i18next"
import remarkGfm from "remark-gfm"

import { Bubble, BubbleContent } from "@/components/shadcn/bubble"
import { Marker, MarkerContent } from "@/components/shadcn/marker"
import {
  Message,
  MessageContent,
  MessageGroup,
} from "@/components/shadcn/message"
import type { AssistantRecord } from "@/types/api"

interface AssistantTranscriptProps {
  records: AssistantRecord[]
  streamingText: string | null
  streamingReasoning: string | null
}

/**
 * The conversation, oldest first. Sessions are separated by a marker so the
 * continuous scroll still reads as one conversation per card.
 */
export const AssistantTranscript = ({
  records,
  streamingText,
  streamingReasoning,
}: AssistantTranscriptProps) => (
  <>
    {records.map((record, index) => (
      <TranscriptEntry
        isNewSession={
          index > 0 && records[index - 1].sessionId !== record.sessionId
        }
        key={`${record.sessionId}-${record.seq}`}
        record={record}
      />
    ))}
    {streamingReasoning !== null && <ThinkingBlock text={streamingReasoning} />}
    {streamingText !== null && (
      <AssistantBubble text={streamingText} isStreaming />
    )}
  </>
)

/**
 * The model's reasoning while it is being produced. Open by default so the
 * point of turning it on is visible, and collapsible once it gets long.
 */
const ThinkingBlock = ({ text }: { text: string }) => {
  const { t } = useTranslation()
  return (
    <MessageGroup>
      <Message>
        <MessageContent>
          <details
            className="rounded-md border border-white/[0.08] bg-white/[0.02] px-3 py-2"
            open
          >
            <summary className="cursor-pointer text-xs font-semibold text-ink-faint select-none">
              {t("assistant.thinking")}
            </summary>
            <div className="mt-1.5 max-h-56 overflow-y-auto text-xs leading-5 whitespace-pre-wrap text-ink-muted">
              {text}
            </div>
          </details>
        </MessageContent>
      </Message>
    </MessageGroup>
  )
}

interface TranscriptEntryProps {
  record: AssistantRecord
  isNewSession: boolean
}

const TranscriptEntry = ({ record, isNewSession }: TranscriptEntryProps) => {
  const { t } = useTranslation()
  const { message } = record

  // Tool output is machinery, not conversation — the call itself is shown as a
  // status line so the user can see the assistant reading their card.
  if ("type" in message) {
    if (message.type === "function_call_output") return null

    return (
      <>
        {isNewSession && <SessionSeparator />}
        <Marker>
          <MarkerContent className="text-xs text-ink-faint">
            {describeToolCall(message.name, message.arguments, t)}
          </MarkerContent>
        </Marker>
      </>
    )
  }

  return (
    <>
      {isNewSession && <SessionSeparator />}
      {message.role === "user" ? (
        <MessageGroup>
          <Message align="end">
            <MessageContent>
              <Bubble align="end">
                <BubbleContent className="text-sm whitespace-pre-wrap">
                  {message.content}
                </BubbleContent>
              </Bubble>
            </MessageContent>
          </Message>
        </MessageGroup>
      ) : (
        <AssistantBubble text={message.content} />
      )}
    </>
  )
}

interface AssistantBubbleProps {
  text: string
  isStreaming?: boolean
}

const AssistantBubble = ({ text, isStreaming }: AssistantBubbleProps) => {
  const { t } = useTranslation()
  return (
    <MessageGroup>
      <Message>
        <MessageContent>
          <Bubble variant="ghost">
            <BubbleContent className="text-sm leading-6 text-ink">
              <div className="assistant-markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {text}
                </ReactMarkdown>
              </div>
              {isStreaming === true && text.length === 0 && (
                <span className="text-ink-faint">
                  {t("assistant.thinkingPending")}
                </span>
              )}
            </BubbleContent>
          </Bubble>
        </MessageContent>
      </Message>
    </MessageGroup>
  )
}

const SessionSeparator = () => {
  const { t } = useTranslation()
  return (
    <Marker>
      <MarkerContent className="text-[11px] tracking-wide text-ink-faint uppercase">
        {t("assistant.newTarget")}
      </MarkerContent>
    </Marker>
  )
}

const describeToolCall = (name: string, args: string, t: TFunction): string => {
  try {
    const parsed = JSON.parse(args) as {
      fieldName?: string
      deck?: string
    }
    if (name === "get_field")
      return t("assistant.tool.getField", { field: parsed.fieldName })
    if (name === "update_field")
      return t("assistant.tool.updateField", { field: parsed.fieldName })
    if (name === "create_note")
      return t("assistant.tool.createNote", { deck: parsed.deck })
  } catch {
    // Fall through to the stable tool name.
  }
  if (name === "list_note_types") return t("assistant.tool.listNoteTypes")
  if (name === "list_decks") return t("assistant.tool.listDecks")
  return name
}
