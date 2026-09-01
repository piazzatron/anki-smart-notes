import { useState, type FormEvent, type KeyboardEvent } from "react"
import type { TFunction } from "i18next"
import { useTranslation } from "react-i18next"

import {
  MessageScroller,
  MessageScrollerContent,
  MessageScrollerProvider,
  MessageScrollerViewport,
} from "@/components/shadcn/message-scroller"
import { Button } from "@/components/ui/Button"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { Toggle } from "@/components/ui/Toggle"
import { ChatModelSelect } from "@/features/text-generation/ChatModelSelect"
import { ReasoningLevelSelect } from "@/features/text-generation/ReasoningLevelSelect"
import { useAppStore } from "@/store/appStore"
import type { AssistantActiveTarget } from "@/types/api"

import { AssistantTranscript } from "./AssistantTranscript"
import {
  useAssistantSession,
  type AssistantSessionUsage,
} from "./useAssistantSession"

/**
 * The chat assistant conversation, shown in its own window. Its settings live
 * on the Chat page in the main window.
 */
export const AssistantScreen = () => {
  const { t } = useTranslation()
  const catalog = useAppStore((store) => store.catalog)
  const activeTarget = useAppStore((store) => store.activeTarget)
  const state = useAppStore((store) => store.state)

  // Deliberately independent of the smart-field generation defaults, and not
  // persisted in v0.1.
  const [model, setModel] = useState("auto")
  const [reasoningLevel, setReasoningLevel] = useState("off")
  const [showReasoning, setShowReasoning] = useState(false)
  const [draft, setDraft] = useState("")

  const isReasoning = reasoningLevel !== "off"
  const session = useAssistantSession(
    model,
    reasoningLevel,
    showReasoning && isReasoning,
  )

  const submit = (text: string) => {
    session.send(text)
    setDraft("")
  }

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    submit(draft)
  }

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      submit(draft)
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col bg-canvas text-ink">
      {/* Two rows: the window is narrow enough that the pickers and the card
          title cannot share one without the model label being clipped. */}
      <header className="shrink-0 border-b border-white/[0.08] px-3 py-2">
        <div className="flex items-center gap-2 pb-2">
          <div className="min-w-0 flex-1 truncate text-xs font-semibold text-ink-muted">
            {describeActiveTarget(activeTarget, t)}
          </div>
          <label className="flex shrink-0 items-center gap-1.5 text-xs text-ink-faint">
            {t("assistant.thinking")}
            <Toggle
              aria-label={t("assistant.showThinkingAriaLabel")}
              checked={showReasoning && isReasoning}
              disabled={!isReasoning}
              onCheckedChange={setShowReasoning}
            />
          </label>
        </div>
        {catalog !== null && (
          <div className="flex gap-2">
            <div className="min-w-0 flex-1">
              <ChatModelSelect
                ariaLabel={t("assistant.modelAriaLabel")}
                catalog={catalog.chat}
                onValueChange={(next) => setModel(next.id)}
                value={model}
              />
            </div>
            <div className="w-28 shrink-0">
              <ReasoningLevelSelect
                ariaLabel={t("assistant.reasoningAriaLabel")}
                levels={catalog.chat.reasoningLevels}
                onValueChange={setReasoningLevel}
                value={reasoningLevel}
              />
            </div>
          </div>
        )}
      </header>

      <MessageScrollerProvider autoScroll>
        <MessageScroller className="flex-1">
          <MessageScrollerViewport className="px-3 py-4">
            <MessageScrollerContent>
              {session.hasMoreHistory && (
                <div className="flex justify-center">
                  <Button
                    disabled={session.isLoadingHistory}
                    onClick={session.loadOlder}
                  >
                    {session.isLoadingHistory
                      ? t("assistant.loading")
                      : t("assistant.loadEarlier")}
                  </Button>
                </div>
              )}
              {session.records.length === 0 &&
                session.streamingText === null && <EmptyState />}
              <AssistantTranscript
                records={session.records}
                streamingReasoning={session.streamingReasoning}
                streamingText={session.streamingText}
              />
            </MessageScrollerContent>
          </MessageScrollerViewport>
        </MessageScroller>
      </MessageScrollerProvider>

      <div className="shrink-0 border-t border-white/[0.08] px-3 py-3">
        {session.error !== null && (
          <div className="mb-2">
            <ErrorBanner
              message={session.error}
              onDismiss={session.dismissError}
            />
          </div>
        )}
        {state?.account.authToken === null ? (
          <p className="text-xs text-ink-muted">{t("assistant.signIn")}</p>
        ) : (
          <>
            {/* Edited on the Chat settings page, not here. */}
            <div className="mb-2 flex flex-wrap gap-1.5">
              {(state?.assistantPrompts ?? []).map((prompt) => (
                <Button
                  disabled={!session.canSend}
                  key={prompt.id}
                  onClick={() => submit(prompt.prompt)}
                  title={prompt.prompt}
                >
                  {prompt.label}
                </Button>
              ))}
            </div>
            <form className="flex items-end gap-2" onSubmit={onSubmit}>
              <textarea
                className="max-h-40 min-h-[38px] flex-1 resize-none rounded-md border border-white/10 bg-white/[0.035] px-3 py-2 text-sm text-ink placeholder:text-ink-faint focus:border-white/20 focus:outline-none"
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={onKeyDown}
                placeholder={t("assistant.placeholder")}
                rows={1}
                value={draft}
              />
              <Button
                disabled={!session.canSend || draft.trim().length === 0}
                type="submit"
                variant="primary"
              >
                {session.isRunning
                  ? t("assistant.sending")
                  : t("assistant.send")}
              </Button>
            </form>
            {import.meta.env.DEV && <UsageMeter t={t} usage={session.usage} />}
          </>
        )}
      </div>
    </div>
  )
}

const EmptyState = () => {
  const { t } = useTranslation()
  return (
    <div className="px-2 py-8 text-center text-xs text-ink-muted">
      {t("assistant.empty")}
    </div>
  )
}

/** Mirrors USD_PER_CREDIT in the server's `utils/credits.ts`. */
const USD_PER_CREDIT = 0.00009

/** What this window has spent since it opened. Dev builds only. */
const UsageMeter = ({
  usage,
  t,
}: {
  usage: AssistantSessionUsage
  t: TFunction
}) => (
  <p className="mt-2 font-mono text-[10px] text-ink-faint">
    {t("assistant.usage", {
      input: usage.inputTokens.toLocaleString(),
      output: usage.outputTokens.toLocaleString(),
      thinking:
        usage.reasoningTokens > 0
          ? t("assistant.usageThinking", {
              count: usage.reasoningTokens.toLocaleString(),
            })
          : "",
      credits: Math.round(usage.credits).toLocaleString(),
      usd: (usage.credits * USD_PER_CREDIT).toFixed(4),
    })}
  </p>
)

// Anki fields hold HTML; the header shows a plain-text preview of the front.
const stripHtml = (value: string): string =>
  value
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim()

const describeActiveTarget = (
  target: AssistantActiveTarget | null,
  t: TFunction,
): string => {
  if (target === null) return t("assistant.binding.none")
  const preview =
    stripHtml(target.firstFieldValue) ||
    target.noteTypeName ||
    t("assistant.binding.untitled")
  return t(`assistant.binding.${target.handle.mode}`, { target: preview })
}
