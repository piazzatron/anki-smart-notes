import { useEffect, useState } from "react"

import { PageLayout } from "@/components/shared/PageLayout"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import {
  saveAssistantPrompts,
  saveAssistantSettings,
} from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AssistantPrompt } from "@/types/api"

import { ASSISTANT_LANGUAGES } from "./assistantLanguages"

interface ChatSettingsScreenProps {
  onDirtyChange?: (isDirty: boolean) => void
}

/**
 * Configuration for the chat assistant. v0.1 configures the saved prompt
 * buttons; custom system prompts land here later.
 */
export const ChatSettingsScreen = ({
  onDirtyChange,
}: ChatSettingsScreenProps) => {
  const saved = useAppStore((store) => store.state?.assistantPrompts)
  const settings = useAppStore((store) => store.state?.assistantSettings)
  const [draft, setDraft] = useState<AssistantPrompt[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  const prompts = draft ?? saved ?? []
  const isDirty = draft !== null

  useEffect(() => onDirtyChange?.(isDirty), [isDirty, onDirtyChange])

  const update = (id: string, changes: Partial<AssistantPrompt>) =>
    setDraft(
      prompts.map((prompt) =>
        prompt.id === id ? { ...prompt, ...changes } : prompt,
      ),
    )

  const save = async () => {
    const cleaned = prompts.map((prompt) => ({
      ...prompt,
      label: prompt.label.trim(),
      prompt: prompt.prompt.trim(),
    }))
    if (cleaned.some((prompt) => prompt.label === "" || prompt.prompt === "")) {
      setError("Every button needs a label and a prompt.")
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
            {isSaving ? "Saving…" : "Save changes"}
          </Button>
        )
      }
      icon={
        <span aria-hidden className="text-lg leading-none">
          🤖
        </span>
      }
      subtitle="Configure the chat assistant"
      testId="chat-settings-screen"
      title="Chat"
    >
      <h2 className="mb-1 text-[17px] leading-tight font-bold text-zinc-100">
        Response language
      </h2>
      <p className="mb-3 text-xs text-ink-muted">
        The assistant replies in this language whatever the card is written in.
      </p>
      <div className="mb-8 w-72">
        <Select
          onValueChange={(language) => {
            // A single value with an obvious result, so it saves on change —
            // the same as the toggles on the Settings page.
            void saveAssistantSettings({ responseLanguage: language }).catch(
              (e: unknown) =>
                setError(e instanceof Error ? e.message : String(e)),
            )
          }}
          value={settings?.responseLanguage ?? "auto"}
        >
          <SelectTrigger aria-label="Assistant response language">
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

      <h2 className="mb-1 text-[17px] leading-tight font-bold text-zinc-100">
        Saved prompts
      </h2>
      <p className="mb-4 text-xs text-ink-muted">
        Each one becomes a button above the message box in the chat window.
      </p>

      {error !== null && (
        <div className="mb-3">
          <ErrorBanner message={error} onDismiss={() => setError(null)} />
        </div>
      )}

      <div className="space-y-3">
        {prompts.length === 0 && (
          <p className="text-xs text-ink-muted">No saved prompts yet.</p>
        )}
        {prompts.map((prompt) => (
          <Card className="w-full space-y-2 p-4" key={prompt.id}>
            <div className="flex items-center gap-2">
              <input
                aria-label="Button label"
                className={FIELD_CLASSES}
                onChange={(event) =>
                  update(prompt.id, { label: event.target.value })
                }
                placeholder="Button label"
                value={prompt.label}
              />
              <Button
                onClick={() =>
                  setDraft(prompts.filter((item) => item.id !== prompt.id))
                }
                variant="danger"
              >
                Remove
              </Button>
            </div>
            <textarea
              aria-label="Prompt text"
              className={`${FIELD_CLASSES} min-h-[72px] resize-y`}
              onChange={(event) =>
                update(prompt.id, { prompt: event.target.value })
              }
              placeholder="What to send when the button is pressed"
              rows={3}
              value={prompt.prompt}
            />
          </Card>
        ))}
        <Button
          onClick={() =>
            setDraft([
              ...prompts,
              { id: crypto.randomUUID(), label: "", prompt: "" },
            ])
          }
        >
          Add prompt
        </Button>
      </div>
    </PageLayout>
  )
}

const FIELD_CLASSES =
  "w-full rounded-md border border-white/10 bg-white/[0.035] px-3 py-2 text-sm text-ink placeholder:text-ink-faint focus:border-white/20 focus:outline-none"
