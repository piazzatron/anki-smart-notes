import { Plus, Sparkles } from "lucide-react"
import { useMemo, useState } from "react"

import { DeckGroup } from "./components/DeckGroup"
import { FieldsEmptyState } from "./components/FieldsEmptyState"
import { FieldsSkeleton } from "./components/FieldsSkeleton"
import { groupSmartFields } from "./groupSmartFields"

import { Button } from "@/components/ui/Button"
import { ScreenHeader } from "@/components/shared/ScreenHeader"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import {
  FieldEditorScreen,
  type FieldEditorRequest,
} from "@/features/field-editor/FieldEditorScreen"
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
      <ScreenHeader
        accessory={
          <Button
            className="shrink-0"
            onClick={() => setEditorState({ mode: "create" })}
            variant="primary"
          >
            <Plus aria-hidden className="size-3.5" />
            New Smart Field
          </Button>
        }
        icon={<Sparkles aria-hidden className="size-5 text-amber" />}
        subtitle="Add automatically generated text, voice, and images to your notes."
        title="Smart Fields"
      />

      {error !== null && (
        <ErrorBanner
          className="mx-6 mt-4"
          message={error}
          onDismiss={() => setError(null)}
        />
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
                onCreate={(initialNoteTypeId) =>
                  setEditorState({ initialNoteTypeId, mode: "create" })
                }
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
        <FieldEditorScreen
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
