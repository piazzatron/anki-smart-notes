import { useState } from "react"

import { Button } from "@/components/ui/Button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/Dialog"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { saveAssistantPrompts } from "@/services/commands"
import type { AssistantPrompt } from "@/types/api"

interface AssistantPromptButtonsProps {
  prompts: AssistantPrompt[]
  disabled: boolean
  onSend: (prompt: string) => void
}

/**
 * The saved-prompt shortcuts above the composer, and the dialog that edits
 * them. Prompts live in the add-on config, so edits go through a command and
 * come back on the next state event.
 */
export const AssistantPromptButtons = ({
  prompts,
  disabled,
  onSend,
}: AssistantPromptButtonsProps) => {
  const [isEditing, setIsEditing] = useState(false)

  return (
    <div className="mb-2 flex flex-wrap items-center gap-1.5">
      {prompts.map((prompt) => (
        <Button
          disabled={disabled}
          key={prompt.id}
          onClick={() => onSend(prompt.prompt)}
          title={prompt.prompt}
        >
          {prompt.label}
        </Button>
      ))}
      <Dialog onOpenChange={setIsEditing} open={isEditing}>
        <DialogTrigger asChild>
          <Button aria-label="Edit saved prompts">⋯</Button>
        </DialogTrigger>
        <DialogContent className="w-[min(440px,92vw)]">
          <PromptEditor onClose={() => setIsEditing(false)} prompts={prompts} />
        </DialogContent>
      </Dialog>
    </div>
  )
}

interface PromptEditorProps {
  prompts: AssistantPrompt[]
  onClose: () => void
}

// Mounted only while the dialog is open, so the draft starts from the saved
// prompts every time it is reopened.
const PromptEditor = ({ prompts, onClose }: PromptEditorProps) => {
  const [draft, setDraft] = useState<AssistantPrompt[]>(prompts)
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  const update = (id: string, changes: Partial<AssistantPrompt>) =>
    setDraft((current) =>
      current.map((prompt) =>
        prompt.id === id ? { ...prompt, ...changes } : prompt,
      ),
    )

  const save = async () => {
    const cleaned = draft.map((prompt) => ({
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
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <>
      <header className="shrink-0 border-b border-white/[0.07] py-3.5 pr-10 pl-5">
        <DialogTitle className="text-[13px] font-bold text-ink">
          Saved prompts
        </DialogTitle>
        <DialogDescription className="mt-1 text-xs text-ink-muted">
          Each one becomes a button above the message box.
        </DialogDescription>
      </header>

      <div className="max-h-[50vh] space-y-3 overflow-y-auto px-5 py-4">
        {draft.length === 0 && (
          <p className="text-xs text-ink-muted">No saved prompts yet.</p>
        )}
        {draft.map((prompt) => (
          <div
            className="space-y-1.5 rounded-md border border-white/[0.08] p-2.5"
            key={prompt.id}
          >
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
                  setDraft((current) =>
                    current.filter((item) => item.id !== prompt.id),
                  )
                }
                variant="danger"
              >
                Remove
              </Button>
            </div>
            <textarea
              aria-label="Prompt text"
              className={`${FIELD_CLASSES} min-h-[56px] resize-none`}
              onChange={(event) =>
                update(prompt.id, { prompt: event.target.value })
              }
              placeholder="What to send when the button is pressed"
              rows={2}
              value={prompt.prompt}
            />
          </div>
        ))}
        <Button
          onClick={() =>
            setDraft((current) => [
              ...current,
              { id: crypto.randomUUID(), label: "", prompt: "" },
            ])
          }
        >
          Add prompt
        </Button>
      </div>

      <div className="space-y-2 border-t border-white/[0.08] px-5 py-4">
        {error !== null && (
          <ErrorBanner message={error} onDismiss={() => setError(null)} />
        )}
        <div className="flex justify-end gap-2">
          <Button onClick={onClose}>Cancel</Button>
          <Button
            disabled={isSaving}
            onClick={() => void save()}
            variant="primary"
          >
            {isSaving ? "Saving…" : "Save"}
          </Button>
        </div>
      </div>
    </>
  )
}

const FIELD_CLASSES =
  "w-full rounded-md border border-white/10 bg-white/[0.035] px-2.5 py-1.5 text-xs text-ink placeholder:text-ink-faint focus:border-white/20 focus:outline-none"
