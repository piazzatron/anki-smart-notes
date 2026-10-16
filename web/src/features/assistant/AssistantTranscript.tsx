import { ChevronRight, Eye, Loader2 } from "lucide-react"
import ReactMarkdown from "react-markdown"
import type { TFunction } from "i18next"
import { useTranslation } from "react-i18next"
import remarkGfm from "remark-gfm"

import type { AssistantRecord } from "@/types/api"

import { recordKey, type TurnReasoning } from "./useAssistantSession"

interface AssistantTranscriptProps {
  records: AssistantRecord[]
  streamingText: string | null
  streamingReasoning: string | null
  reasoningByRecord: Record<string, TurnReasoning>
  creditsByRecord: Record<string, number>
  showCreditUsage: boolean
}

/**
 * The conversation, oldest first. Sessions are per card, so the scroll is
 * broken by a card separator rather than being split into separate views.
 */
export const AssistantTranscript = ({
  records,
  streamingText,
  streamingReasoning,
  reasoningByRecord,
  creditsByRecord,
  showCreditUsage,
}: AssistantTranscriptProps) => {
  // A tool call with no output yet is still in flight — the read is the wait,
  // so it has to read as live rather than as a line printed afterwards.
  const answered = new Set(
    records.flatMap((record) =>
      "type" in record.message && record.message.type === "function_call_output"
        ? [record.message.call_id]
        : [],
    ),
  )

  return (
    <>
      {records.map((record, index) => {
        const key = recordKey(record)
        return (
          <TranscriptEntry
            answered={answered}
            credits={showCreditUsage ? creditsByRecord[key] : undefined}
            isNewSession={
              index > 0 && records[index - 1].sessionId !== record.sessionId
            }
            key={key}
            reasoning={reasoningByRecord[key]}
            record={record}
          />
        )
      })}
      {streamingReasoning !== null && (
        <ReasoningRail isStreaming text={streamingReasoning} />
      )}
      {streamingText !== null && (
        <AssistantReply isStreaming text={streamingText} />
      )}
    </>
  )
}

interface TranscriptEntryProps {
  record: AssistantRecord
  isNewSession: boolean
  answered: Set<string>
  reasoning?: TurnReasoning
  credits?: number
}

const TranscriptEntry = ({
  record,
  isNewSession,
  answered,
  reasoning,
  credits,
}: TranscriptEntryProps) => {
  const { t } = useTranslation()
  const { message } = record

  // Tool output is machinery, not conversation — only the call itself shows.
  if ("type" in message) {
    if (message.type === "function_call_output") return null

    return (
      <>
        {isNewSession && <CardSeparator />}
        <ToolPill
          isRunning={!answered.has(message.call_id)}
          label={describeToolCall(
            message.name,
            message.arguments,
            !answered.has(message.call_id),
            t,
          )}
        />
      </>
    )
  }

  return (
    <>
      {isNewSession && <CardSeparator />}
      {message.role === "user" ? (
        <div className="flex justify-end">
          <div className="max-w-[84%] rounded-[10px] bg-indigo-deep px-3 py-2 text-[13px] leading-normal whitespace-pre-wrap text-white">
            {message.content}
          </div>
        </div>
      ) : (
        <>
          {reasoning !== undefined && (
            <ReasoningRail seconds={reasoning.seconds} text={reasoning.text} />
          )}
          <AssistantReply credits={credits} text={message.content} />
        </>
      )}
    </>
  )
}

interface AssistantReplyProps {
  text: string
  credits?: number
  isStreaming?: boolean
}

/** Full width behind a ✨ gutter mark, so long explanations get the column. */
const AssistantReply = ({
  text,
  credits,
  isStreaming,
}: AssistantReplyProps) => {
  const { t } = useTranslation()
  return (
    <div className="flex gap-[9px]">
      <span
        aria-hidden
        className="w-[17px] shrink-0 pt-px text-xs leading-[1.55] opacity-90"
      >
        ✨
      </span>
      <div className="min-w-0 flex-1 text-[13px] leading-[1.62] text-ink">
        <div className="assistant-markdown">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
        </div>
        {isStreaming === true && text.length === 0 && (
          <span className="text-ink-faint">{t("assistant.pending")}</span>
        )}
        {credits !== undefined && (
          <div className="mt-[7px] text-[10.5px] text-ink-faint tabular-nums">
            {t("assistant.credits", { count: credits })}
          </div>
        )}
      </div>
    </div>
  )
}

interface ReasoningRailProps {
  text: string
  seconds?: number
  isStreaming?: boolean
}

/**
 * A sub-conversation, railed off in indigo so it never competes with the
 * answer. Open while it streams, collapsed to its duration once the reply lands.
 */
const ReasoningRail = ({ text, seconds, isStreaming }: ReasoningRailProps) => {
  const { t } = useTranslation()
  return (
    <details
      className="assistant-reasoning ms-[26px] border-s-2 border-indigo/40 ps-[11px]"
      open={isStreaming}
    >
      <summary className="flex cursor-pointer list-none items-center gap-1.5 text-[11.5px] font-semibold text-indigo-soft select-none">
        <ChevronRight className="assistant-reasoning-caret" size={9} />
        {isStreaming === true
          ? t("assistant.reasoningStreaming")
          : t("assistant.reasoningDone", { seconds })}
      </summary>
      <div className="mt-1.5 text-[11.5px] leading-[1.62] whitespace-pre-wrap text-ink-faint italic">
        {text}
      </div>
    </details>
  )
}

const ToolPill = ({
  label,
  isRunning,
}: {
  label: string
  isRunning: boolean
}) => (
  <div
    className={`ms-[26px] inline-flex items-center gap-[7px] self-start rounded-full py-1 ps-2 pe-2.5 text-[11.5px] ${
      isRunning
        ? "bg-indigo/[0.18] text-indigo-soft"
        : "bg-white/[0.045] text-ink-faint"
    }`}
  >
    {isRunning ? (
      <Loader2 className="shrink-0 animate-spin" size={12} />
    ) : (
      <Eye className="shrink-0" size={12} />
    )}
    {label}
  </div>
)

const CardSeparator = () => {
  const { t } = useTranslation()
  return (
    <div className="my-1 flex items-center gap-2.5 text-[10px] font-bold tracking-[0.11em] text-ink-faint uppercase before:h-px before:flex-1 before:bg-white/[0.075] before:content-[''] after:h-px after:flex-1 after:bg-white/[0.075] after:content-['']">
      {t("assistant.newCard")}
    </div>
  )
}

const describeToolCall = (
  name: string,
  args: string,
  isRunning: boolean,
  t: TFunction,
): string => {
  const suffix = isRunning ? "Running" : "Done"
  try {
    const parsed = JSON.parse(args) as { fieldName?: string; deck?: string }
    if (name === "get_field")
      return t(`assistant.tool.getField${suffix}`, { field: parsed.fieldName })
    if (name === "update_field")
      return t(`assistant.tool.updateField${suffix}`, {
        field: parsed.fieldName,
      })
    if (name === "create_note")
      return t(`assistant.tool.createNote${suffix}`, { deck: parsed.deck })
  } catch {
    // Fall through to the stable tool name.
  }
  if (name === "list_note_types")
    return t(`assistant.tool.listNoteTypes${suffix}`)
  if (name === "list_decks") return t(`assistant.tool.listDecks${suffix}`)
  return name
}
