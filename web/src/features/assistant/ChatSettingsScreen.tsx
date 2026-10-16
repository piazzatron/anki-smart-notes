import { GripVertical, Plus, X } from "lucide-react"
import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"

import { PageLayout } from "@/components/shared/PageLayout"
import { ScreenSkeleton } from "@/components/shared/ScreenSkeleton"
import { Button } from "@/components/ui/Button"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { Toggle } from "@/components/ui/Toggle"
import { ChatModelSelect } from "@/features/text-generation/ChatModelSelect"
import { ReasoningLevelSelect } from "@/features/text-generation/ReasoningLevelSelect"
import {
  saveAssistantPrompts,
  saveAssistantSettings,
} from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AssistantPrompt, AssistantSettings } from "@/types/api"

import { ASSISTANT_LANGUAGES } from "./assistantLanguages"

interface ChatSettingsScreenProps {
  onDirtyChange?: (isDirty: boolean) => void
}

export const ChatSettingsScreen = ({
  onDirtyChange,
}: ChatSettingsScreenProps) => {
  const { t } = useTranslation()
  const state = useAppStore((store) => store.state)

  if (state === null)
    return (
      <ScreenSkeleton
        ariaLabel={t("chatSettings.loading")}
        className="max-w-[800px]"
        contentClassName="h-56 max-w-[700px]"
        title={t("chatSettings.title")}
      />
    )

  return (
    <LoadedChatSettingsScreen
      onDirtyChange={onDirtyChange}
      prompts={state.assistantPrompts}
      settings={state.assistantSettings}
    />
  )
}

interface LoadedChatSettingsScreenProps extends ChatSettingsScreenProps {
  prompts: AssistantPrompt[]
  settings: AssistantSettings
}

/**
 * Configuration for the chat assistant: the quick actions above the message
 * box, and the defaults the chat window answers with.
 */
const LoadedChatSettingsScreen = ({
  onDirtyChange,
  prompts: saved,
  settings,
}: LoadedChatSettingsScreenProps) => {
  const { t } = useTranslation()
  const catalog = useAppStore((store) => store.catalog)
  const [draft, setDraft] = useState<AssistantPrompt[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  const prompts = draft ?? saved
  const isDirty = draft !== null

  useEffect(() => onDirtyChange?.(isDirty), [isDirty, onDirtyChange])

  const update = (id: string, changes: Partial<AssistantPrompt>) =>
    setDraft(
      prompts.map((prompt) =>
        prompt.id === id ? { ...prompt, ...changes } : prompt,
      ),
    )

  // Every control here has one value and an obvious result, so it saves on
  // change — the same as the toggles on the Settings page. Only the quick
  // action list, which is edited as a whole, waits for Save changes.
  const updateSettings = (changes: Partial<AssistantSettings>) =>
    void saveAssistantSettings({ ...settings, ...changes }).catch(
      (e: unknown) => setError(e instanceof Error ? e.message : String(e)),
    )

  const save = async () => {
    const cleaned = prompts.map((prompt) => ({
      ...prompt,
      label: prompt.label.trim(),
      prompt: prompt.prompt.trim(),
    }))
    if (cleaned.some((prompt) => prompt.label === "" || prompt.prompt === "")) {
      setError(t("chatSettings.invalidPrompt"))
      return
    }

    setIsSaving(true)
    setError(null)
    try {
      await saveAssistantPrompts(cleaned)
      setDraft(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <PageLayout
      actions={
        isDirty && (
          <Button
            disabled={isSaving}
            onClick={() => void save()}
            variant="primary"
          >
            {isSaving ? t("chatSettings.saving") : t("chatSettings.save")}
          </Button>
        )
      }
      className="max-w-[800px]"
      icon={
        <span aria-hidden className="text-lg leading-none">
          🤖
        </span>
      }
      subtitle={t("chatSettings.subtitle")}
      testId="chat-settings-screen"
      title={t("chatSettings.title")}
    >
      {error !== null && (
        <ErrorBanner
          className="mb-5"
          message={error}
          onDismiss={() => setError(null)}
        />
      )}

      <SectionLabel>{t("chatSettings.quickActions")}</SectionLabel>
      <p className="mt-1 mb-3 max-w-[60ch] text-[12.5px] leading-relaxed text-ink-muted">
        {t("chatSettings.quickActionsDescription")}
      </p>

      <QuickActionList
        onChange={setDraft}
        onUpdate={update}
        prompts={prompts}
      />

      <SectionLabel className="mt-8">
        {t("chatSettings.otherSettings")}
      </SectionLabel>
      <div>
        <SettingRow
          description={t("chatSettings.modelDescription")}
          label={t("chatSettings.model")}
        >
          {catalog !== null && (
            <div className="w-64">
              <ChatModelSelect
                ariaLabel={t("chatSettings.modelAriaLabel")}
                catalog={catalog.chat}
                onValueChange={(model) => updateSettings({ model: model.id })}
                value={settings.model}
              />
            </div>
          )}
        </SettingRow>
        <SettingRow
          description={t("chatSettings.reasoningDescription")}
          label={t("chatSettings.reasoning")}
        >
          {catalog !== null && (
            <div className="w-44">
              <ReasoningLevelSelect
                ariaLabel={t("chatSettings.reasoningAriaLabel")}
                levels={catalog.chat.reasoningLevels}
                onValueChange={(reasoningLevel) =>
                  updateSettings({ reasoningLevel })
                }
                value={settings.reasoningLevel}
              />
            </div>
          )}
        </SettingRow>
        <SettingRow
          description={t("chatSettings.replyLanguageDescription")}
          label={t("chatSettings.replyLanguage")}
        >
          <div className="w-56">
            <Select
              onValueChange={(responseLanguage) =>
                updateSettings({ responseLanguage })
              }
              value={settings.responseLanguage}
            >
              <SelectTrigger
                aria-label={t("chatSettings.replyLanguageAriaLabel")}
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ASSISTANT_LANGUAGES.map((language) => (
                  <SelectItem key={language.code} value={language.code}>
                    <span className="text-zinc-100">
                      <span aria-hidden className="mr-2">
                        {language.flag}
                      </span>
                      {language.label}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </SettingRow>
        <SettingRow
          description={t("chatSettings.showReasoningDescription")}
          label={t("chatSettings.showReasoning")}
        >
          <Toggle
            aria-label={t("chatSettings.showReasoning")}
            checked={settings.showReasoning}
            onCheckedChange={(showReasoning) =>
              updateSettings({ showReasoning })
            }
          />
        </SettingRow>
        <SettingRow
          description={t("chatSettings.showCreditUsageDescription")}
          label={t("chatSettings.showCreditUsage")}
          last
        >
          <Toggle
            aria-label={t("chatSettings.showCreditUsage")}
            checked={settings.showCreditUsage}
            onCheckedChange={(showCreditUsage) =>
              updateSettings({ showCreditUsage })
            }
          />
        </SettingRow>
      </div>
    </PageLayout>
  )
}

interface QuickActionListProps {
  prompts: AssistantPrompt[]
  onChange: (prompts: AssistantPrompt[]) => void
  onUpdate: (id: string, changes: Partial<AssistantPrompt>) => void
}

/**
 * The quick action rows, reorderable by dragging the grip. Order is the only
 * thing position means — the plugin writes it from list order on save.
 */
const QuickActionList = ({
  prompts,
  onChange,
  onUpdate,
}: QuickActionListProps) => {
  const { t } = useTranslation()
  // Rows are only draggable while their grip is held, so the two text inputs
  // stay selectable with the mouse.
  const [grabbedIndex, setGrabbedIndex] = useState<number | null>(null)
  const [dragIndex, setDragIndex] = useState<number | null>(null)

  const moveTo = (index: number) => {
    if (dragIndex === null || dragIndex === index) return
    const reordered = [...prompts]
    reordered.splice(index, 0, ...reordered.splice(dragIndex, 1))
    onChange(reordered)
    setDragIndex(index)
  }

  return (
    <>
      {prompts.length === 0 && (
        <p className="text-xs text-ink-muted">
          {t("chatSettings.emptyQuickActions")}
        </p>
      )}
      <div className="flex flex-col gap-[7px]">
        {prompts.map((prompt, index) => (
          <div
            className={`flex items-center gap-2.5 rounded-[10px] bg-panel-raised py-2 ps-1.5 pe-2.5 ${
              dragIndex === index ? "opacity-50" : ""
            }`}
            draggable={grabbedIndex === index}
            key={prompt.id}
            onDragEnd={() => {
              setDragIndex(null)
              setGrabbedIndex(null)
            }}
            onDragOver={(event) => {
              event.preventDefault()
              moveTo(index)
            }}
            onDragStart={() => setDragIndex(index)}
          >
            <span
              aria-hidden
              className="shrink-0 cursor-grab text-ink-faint/70"
              onMouseDown={() => setGrabbedIndex(index)}
              onMouseUp={() => setGrabbedIndex(null)}
              title={t("chatSettings.reorderQuickAction")}
            >
              <GripVertical size={14} />
            </span>
            <input
              aria-label={t("chatSettings.buttonLabel")}
              className="w-[172px] shrink-0 truncate rounded-[7px] bg-white/[0.055] px-2.5 py-1.5 text-xs font-semibold text-ink placeholder:text-ink-faint focus:outline-none"
              onChange={(event) =>
                onUpdate(prompt.id, { label: event.target.value })
              }
              placeholder={t("chatSettings.buttonLabel")}
              value={prompt.label}
            />
            <input
              aria-label={t("chatSettings.promptTextAriaLabel")}
              className="min-w-0 flex-1 truncate rounded-[7px] bg-transparent px-2.5 py-1.5 text-xs text-ink-muted transition placeholder:text-ink-faint hover:bg-white/[0.055] focus:bg-white/[0.055] focus:text-ink focus:outline-none"
              onChange={(event) =>
                onUpdate(prompt.id, { prompt: event.target.value })
              }
              placeholder={t("chatSettings.promptPlaceholder")}
              value={prompt.prompt}
            />
            <button
              aria-label={t("chatSettings.removeQuickAction")}
              className="shrink-0 rounded-md p-1 text-ink-faint transition hover:bg-white/[0.06] hover:text-ink"
              onClick={() =>
                onChange(prompts.filter((item) => item.id !== prompt.id))
              }
              type="button"
            >
              <X size={13} />
            </button>
          </div>
        ))}
      </div>
      <button
        className="mt-3 inline-flex items-center gap-1.5 self-start rounded-lg bg-white/[0.055] px-3 py-2 text-xs font-semibold text-zinc-300 transition hover:bg-white/[0.085] hover:text-ink"
        onClick={() =>
          onChange([
            ...prompts,
            { id: crypto.randomUUID(), label: "", prompt: "" },
          ])
        }
        type="button"
      >
        <Plus size={13} />
        {t("chatSettings.addQuickAction")}
      </button>
    </>
  )
}

interface SettingRowProps {
  children: React.ReactNode
  description: string
  label: string
  last?: boolean
}

const SettingRow = ({
  children,
  description,
  label,
  last = false,
}: SettingRowProps) => (
  <div
    className={`flex min-h-[58px] items-center gap-5 py-[11px] ${
      last ? "" : "border-b border-white/[0.065]"
    }`}
  >
    <div className="min-w-0 flex-1">
      <p className="text-sm font-semibold text-zinc-100">{label}</p>
      <p className="mt-0.5 text-[12.5px] leading-5 text-ink-muted">
        {description}
      </p>
    </div>
    {children}
  </div>
)

const SectionLabel = ({
  children,
  className = "",
}: {
  children: string
  className?: string
}) => (
  <h2 className={`text-[15px] font-semibold text-zinc-400 ${className}`}>
    {children}
  </h2>
)
