import { AlertCircle, Plus, Sparkles, X } from "lucide-react"
import { useMemo, useState } from "react"

import { DeckGroup } from "./components/DeckGroup"
import { FieldsEmptyState } from "./components/FieldsEmptyState"
import { FieldsSkeleton } from "./components/FieldsSkeleton"
import { groupSmartFields } from "./groupSmartFields"

import { Button } from "@/components/ui/Button"
import {
  FieldEditorModal,
  type FieldEditorRequest,
} from "@/features/field-editor/FieldEditorModal"
import { deleteSmartField, setSmartFieldEnabled } from "@/services/commands"
import type { AppState, SmartField } from "@/types/api"

export interface SmartFieldsScreenProps {
  initialEditor?: FieldEditorRequest
  state: AppState | null
}

export const SmartFieldsScreen = ({
  initialEditor,
  state,
}: SmartFieldsScreenProps) => {
  const [error, setError] = useState<string | null>(null)
  const [editorState, setEditorState] = useState<FieldEditorRequest | null>(
    null,
  )
  const [initialEditorDismissed, setInitialEditorDismissed] = useState(false)
  const groups = useMemo(
    () => (state === null ? [] : groupSmartFields(state)),
    [state],
  )

  const initialField =
    initialEditor?.mode === "create" ? undefined : state?.smartFields[0]
  const resolvedInitialEditor =
    !initialEditorDismissed &&
    initialEditor !== undefined &&
    state !== null &&
    (initialEditor.mode === "create" || initialField !== undefined)
      ? { ...initialEditor, field: initialField }
      : null
  const activeEditor = editorState ?? resolvedInitialEditor

  const toggleEnabled = (field: SmartField) =>
    setSmartFieldEnabled(field, !field.enabled)

  return (
    <section
      className="flex min-h-0 flex-1 flex-col"
      data-testid="smart-fields-screen"
    >
      <header className="flex shrink-0 items-center justify-between gap-6 border-b border-white/[0.065] px-6 py-5">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <Sparkles aria-hidden className="size-5 text-amber" />
            <h1 className="truncate text-[21px] leading-tight font-bold tracking-[-0.025em] text-zinc-100">
              Smart Fields
            </h1>
          </div>
          <p className="mt-1.5 truncate text-xs text-ink-muted">
            Text, voice, and images — generated on your cards, automatically.
          </p>
        </div>
        <Button
          className="shrink-0"
          onClick={() => setEditorState({ mode: "create" })}
          variant="primary"
        >
          <Plus aria-hidden className="size-3.5" />
          New Smart Field
        </Button>
      </header>

      {error !== null && (
        <div className="mx-6 mt-4 flex items-start gap-2 rounded-lg border border-red-300/15 bg-red-300/[0.06] px-3 py-2.5 text-xs text-danger">
          <AlertCircle aria-hidden className="mt-0.5 size-3.5 shrink-0" />
          <p className="min-w-0 flex-1">{error}</p>
          <button aria-label="Dismiss error" onClick={() => setError(null)}>
            <X aria-hidden className="size-3.5" />
          </button>
        </div>
      )}

      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
        {state === null ? (
          <FieldsSkeleton />
        ) : state.smartFields.length === 0 ? (
          <FieldsEmptyState
            onCreate={() => setEditorState({ mode: "create" })}
          />
        ) : (
          <div className="px-6 py-5">
            {groups.map((group) => (
              <DeckGroup
                group={group}
                key={group.deck.id}
                onDelete={deleteSmartField}
                onDuplicate={(field) =>
                  setEditorState({ field, mode: "duplicate" })
                }
                onEdit={(field) => setEditorState({ field, mode: "edit" })}
                onError={setError}
                onToggleEnabled={toggleEnabled}
              />
            ))}
          </div>
        )}
      </div>
      {state !== null && activeEditor !== null && (
        <FieldEditorModal
          {...activeEditor}
          onClose={() => {
            setEditorState(null)
            setInitialEditorDismissed(true)
          }}
          state={state}
        />
      )}
    </section>
  )
}
