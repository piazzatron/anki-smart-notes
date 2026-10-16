import {
  ArrowUp,
  ChevronDown,
  Lightbulb,
  Loader2,
  Pencil,
  Settings,
} from "lucide-react"
import { useState, type FormEvent, type KeyboardEvent } from "react"
import type { TFunction } from "i18next"
import { useTranslation } from "react-i18next"

import {
  MessageScroller,
  MessageScrollerContent,
  MessageScrollerProvider,
  MessageScrollerViewport,
} from "@/components/shadcn/message-scroller"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/DropdownMenu"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { modelLabel } from "@/lib/catalog"
import { openChatSettings } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AssistantActiveTarget } from "@/types/api"

import { describeAssistantTarget } from "./assistantHeader"
import { AssistantTranscript } from "./AssistantTranscript"
import { useAssistantSession } from "./useAssistantSession"

/**
 * The chat assistant conversation, shown in its own window. Its defaults and
 * quick actions live on the Chat page in the main window.
 */
export const AssistantScreen = () => {
  const { t } = useTranslation()
  const catalog = useAppStore((store) => store.catalog)
  const activeTarget = useAppStore((store) => store.activeTarget)
  const state = useAppStore((store) => store.state)
  const settings = state?.assistantSettings ?? null

  // Null follows whatever the Chat settings page has saved; picking from a
  // chip overrides it for this window only, and is never persisted back.
  const [model, setModel] = useState<string | null>(null)
  const [reasoningLevel, setReasoningLevel] = useState<string | null>(null)
  const [draft, setDraft] = useState("")
  const [isComposerFocused, setIsComposerFocused] = useState(false)

  const activeModel = model ?? settings?.model ?? "auto"
  const activeReasoning = reasoningLevel ?? settings?.reasoningLevel ?? "off"
  const session = useAssistantSession(
    activeModel,
    activeReasoning,
    (settings?.showReasoning ?? false) && activeReasoning !== "off",
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

  const isEmpty = session.records.length === 0 && session.streamingText === null

  return (
    <div className="flex h-full min-h-0 flex-col bg-canvas text-ink">
      <ContextHeader target={activeTarget} />

      {/* The scroller stays mounted through the empty state: remounting it when
          the first message lands would drop the autoscroll subscription with it. */}
      <MessageScrollerProvider autoScroll>
        <MessageScroller className="flex-1">
          <MessageScrollerViewport className="px-3.5 pt-4 pb-[18px]">
            <MessageScrollerContent className="gap-4">
              {isEmpty ? (
                <AssistantEmptyState />
              ) : (
                <>
                  {session.hasMoreHistory && (
                    <button
                      className="self-center rounded-full bg-white/[0.055] px-3 py-1.5 text-[11.5px] font-semibold text-ink-muted transition hover:bg-white/[0.085] hover:text-ink"
                      disabled={session.isLoadingHistory}
                      onClick={session.loadOlder}
                      type="button"
                    >
                      {session.isLoadingHistory
                        ? t("assistant.loading")
                        : t("assistant.loadEarlierCards")}
                    </button>
                  )}
                  <AssistantTranscript
                    creditsByRecord={session.creditsByRecord}
                    reasoningByRecord={session.reasoningByRecord}
                    records={session.records}
                    showCreditUsage={settings?.showCreditUsage ?? false}
                    streamingReasoning={session.streamingReasoning}
                    streamingText={session.streamingText}
                  />
                </>
              )}
            </MessageScrollerContent>
          </MessageScrollerViewport>
        </MessageScroller>
      </MessageScrollerProvider>

      <div className="shrink-0 px-3 pb-3">
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
            <div className="mb-2 flex items-start gap-1.5">
              {/* Two rows of quick actions, then scroll — the edit button sits
                  outside the wrap so it never moves. */}
              <div className="flex max-h-[62px] min-w-0 flex-1 [scrollbar-width:none] flex-wrap gap-1.5 overflow-y-auto [&::-webkit-scrollbar]:hidden">
                {(state?.assistantPrompts ?? []).map((prompt) => (
                  <button
                    className="shrink-0 rounded-full bg-white/[0.055] px-2.5 py-1.5 text-[11.5px] font-medium text-zinc-300 transition hover:bg-white/[0.085] hover:text-white disabled:opacity-45"
                    disabled={!session.canSend}
                    key={prompt.id}
                    onClick={() => submit(prompt.prompt)}
                    title={prompt.prompt}
                    type="button"
                  >
                    {prompt.label}
                  </button>
                ))}
              </div>
              <button
                aria-label={t("assistant.editQuickActions")}
                className="shrink-0 rounded-full bg-white/[0.055] p-[7px] text-ink-faint transition hover:bg-white/[0.085] hover:text-ink"
                onClick={() => void openChatSettings()}
                title={t("assistant.editQuickActions")}
                type="button"
              >
                <Pencil size={12} />
              </button>
            </div>

            <form
              className={`rounded-xl bg-panel-raised ${
                isComposerFocused ? "outline-2 outline-indigo" : ""
              }`}
              onSubmit={onSubmit}
            >
              <textarea
                className="max-h-40 min-h-[38px] w-full resize-none bg-transparent px-3 pt-2.5 text-[13px] text-ink placeholder:text-ink-faint focus:outline-none"
                onBlur={() => setIsComposerFocused(false)}
                onChange={(event) => setDraft(event.target.value)}
                onFocus={() => setIsComposerFocused(true)}
                onKeyDown={onKeyDown}
                placeholder={t("assistant.placeholder")}
                rows={1}
                value={draft}
              />
              <div className="flex items-center gap-1.5 px-2 pt-1 pb-2">
                {catalog !== null && (
                  <>
                    <ComposerChip
                      label={`✨ ${modelLabel(activeModel)}`}
                      onSelect={setModel}
                      options={catalog.chat.models.map((option) => ({
                        label: modelLabel(option.id),
                        value: option.id,
                      }))}
                      value={activeModel}
                    />
                    <ComposerChip
                      icon={<Lightbulb size={12} />}
                      isActive={activeReasoning !== "off"}
                      label={t("assistant.reasoningChip", {
                        level: reasoningLabel(activeReasoning, t),
                      })}
                      onSelect={setReasoningLevel}
                      options={catalog.chat.reasoningLevels.map((level) => ({
                        label: reasoningLabel(level, t),
                        value: level,
                      }))}
                      value={activeReasoning}
                    />
                  </>
                )}
                <span className="flex-1" />
                <button
                  aria-label={
                    session.isRunning
                      ? t("assistant.working")
                      : t("assistant.send")
                  }
                  className="flex size-[30px] shrink-0 items-center justify-center rounded-lg border border-[#1fd47d]/60 bg-gradient-to-b from-[#4cf0a8] to-[#1fd47d] text-[#06281a] shadow-[inset_0_1px_0_rgba(255,255,255,0.34)] transition hover:brightness-110 disabled:border-white/[0.08] disabled:bg-white/[0.055] disabled:bg-none disabled:text-ink-faint disabled:shadow-none"
                  disabled={!session.canSend || draft.trim().length === 0}
                  type="submit"
                >
                  {session.isRunning ? (
                    <Loader2 className="animate-spin" size={14} />
                  ) : (
                    <ArrowUp size={15} strokeWidth={2.4} />
                  )}
                </button>
              </div>
            </form>
            {import.meta.env.DEV && (
              <UsageMeter credits={session.creditsUsed} t={t} />
            )}
          </>
        )}
      </div>
    </div>
  )
}

/**
 * What the assistant is looking at. Mode gates what it can do, so it is stated
 * rather than inferred, and stays flat neutral — the icon carries the
 * difference and the send button keeps the screen's one saturated element.
 */
const ContextHeader = ({
  target,
}: {
  target: AssistantActiveTarget | null
}) => {
  const { t } = useTranslation()
  const copy = describeAssistantTarget(target, t)

  return (
    <header className="flex shrink-0 items-center gap-2.5 border-b border-white/[0.075] px-3 py-2.5">
      <div className="min-w-0 flex-1">
        <div
          className={`flex min-w-0 items-center gap-[7px] text-[13px] font-semibold ${
            copy.mode === null ? "text-ink-muted" : "text-ink"
          }`}
        >
          {copy.mode !== null && (
            <span className="shrink-0 rounded-[5px] bg-white/[0.085] px-1.5 py-0.5 text-[9.5px] font-bold tracking-[0.07em] text-zinc-400 uppercase">
              {copy.mode}
            </span>
          )}
          <span className="truncate">{copy.target}</span>
        </div>
        {copy.subline !== "" && (
          <div className="mt-0.5 truncate text-[11.5px] text-ink-faint">
            {copy.subline}
          </div>
        )}
      </div>
      <button
        aria-label={t("assistant.chatSettings")}
        className="shrink-0 rounded-md p-1.5 text-ink-muted transition hover:bg-white/[0.06] hover:text-ink"
        onClick={() => void openChatSettings()}
        title={t("assistant.chatSettings")}
        type="button"
      >
        <Settings size={15} />
      </button>
    </header>
  )
}

interface ComposerChipProps {
  label: string
  icon?: React.ReactNode
  isActive?: boolean
  options: { label: string; value: string }[]
  value: string
  onSelect: (value: string) => void
}

/** Model and reasoning are per-message decisions, so they sit by the message. */
const ComposerChip = ({
  label,
  icon,
  isActive = false,
  options,
  value,
  onSelect,
}: ComposerChipProps) => (
  <DropdownMenu>
    <DropdownMenuTrigger
      className={`inline-flex shrink-0 items-center gap-1.5 rounded-md px-2 py-1 text-[11.5px] font-medium transition ${
        isActive
          ? "bg-indigo/[0.16] text-indigo-soft"
          : "text-ink-muted hover:bg-white/[0.06] hover:text-ink"
      }`}
    >
      {icon}
      {label}
      <ChevronDown className="opacity-70" size={10} />
    </DropdownMenuTrigger>
    <DropdownMenuContent align="start" side="top">
      {options.map((option) => (
        <DropdownMenuItem
          className={option.value === value ? "text-ink" : ""}
          key={option.value}
          onSelect={() => onSelect(option.value)}
        >
          {option.label}
        </DropdownMenuItem>
      ))}
    </DropdownMenuContent>
  </DropdownMenu>
)

/**
 * The only empty state there is: after the first conversation the scroll always
 * has history above the card separator.
 */
const AssistantEmptyState = () => {
  const { t } = useTranslation()
  return (
    <div className="assistant-empty">
      <div aria-hidden className="assistant-empty-art">
        <span className="assistant-empty-spark assistant-empty-spark-one">
          {SPARK}
        </span>
        <span className="assistant-empty-spark assistant-empty-spark-two">
          {SPARK}
        </span>
        <div className="assistant-empty-card">
          <div className="assistant-empty-card-top">
            {t("assistant.emptyState.exampleField")}
            <span className="assistant-empty-card-dot" />
          </div>
          <div className="assistant-empty-card-front">
            {t("assistant.emptyState.exampleFront")}
          </div>
          <div className="assistant-empty-card-question">
            {t("assistant.emptyState.exampleQuestion")}
            <span className="assistant-empty-caret" />
          </div>
        </div>
        <span className="assistant-empty-bubble">💬</span>
      </div>
      <h2 className="assistant-empty-title">
        {t("assistant.emptyState.title")}
      </h2>
      <p className="assistant-empty-copy">
        {t("assistant.emptyState.description")}
      </p>
      <div className="assistant-empty-caps">
        <div className="assistant-empty-cap">
          <span aria-hidden>{CAPABILITY_ICONS.explain}</span>
          {t("assistant.emptyState.explain")}
        </div>
        <div className="assistant-empty-cap">
          <span aria-hidden>{CAPABILITY_ICONS.edit}</span>
          {t("assistant.emptyState.edit")}
        </div>
        <div className="assistant-empty-cap">
          <span aria-hidden>{CAPABILITY_ICONS.create}</span>
          {t("assistant.emptyState.create")}
        </div>
      </div>
    </div>
  )
}

const SPARK = "✦"
const CAPABILITY_ICONS = { create: "🗂️", edit: "✏️", explain: "💡" }

/** What this window has spent since it opened. Dev builds only. */
const UsageMeter = ({ credits, t }: { credits: number; t: TFunction }) => (
  <p className="mt-2 font-mono text-[10px] text-ink-faint">
    {t("assistant.credits", { count: Math.round(credits) })}
  </p>
)

const reasoningLabel = (level: string, t: TFunction): string =>
  t(`defaults.text.reasoningValues.${level}`)
