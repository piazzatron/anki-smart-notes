import { Plus } from "lucide-react"
import { useMemo, useState } from "react"

import { selectBannerPrompt } from "./bannerPrompt"
import { DeckGroup } from "./components/DeckGroup"
import { DiscordPrompt } from "./components/DiscordPrompt"
import { FieldsEmptyState } from "./components/FieldsEmptyState"
import { FieldsSkeleton } from "./components/FieldsSkeleton"
import { ReviewPrompt } from "./components/ReviewPrompt"
import { groupSmartFields } from "./groupSmartFields"

import { PageLayout } from "@/components/shared/PageLayout"
import { Button } from "@/components/ui/Button"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import {
  FieldEditorScreen,
  type FieldEditorRequest,
} from "@/features/field-editor/FieldEditorScreen"
import {
  deleteSmartField,
  saveSettings,
  setSmartFieldEnabled,
} from "@/services/commands"
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
  const [reviewPromptHidden, setReviewPromptHidden] = useState(false)
  const [discordPromptHidden, setDiscordPromptHidden] = useState(false)
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

  const bannerPrompt = selectBannerPrompt({
    hasState: state !== null,
    didDismissReviewPrompt: state?.settings.didDismissReviewPrompt ?? false,
    didDismissDiscordPrompt: state?.settings.didDismissDiscordPrompt ?? false,
    reviewDismissedThisSession: reviewPromptHidden,
    discordDismissedThisSession: discordPromptHidden,
  })

  const toggleEnabled = (field: SmartField) =>
    setSmartFieldEnabled(field, !field.enabled)

  const dismissDiscordPrompt = () => {
    if (state === null) return

    setDiscordPromptHidden(true)
    void saveSettings({
      ...state.settings,
      didDismissDiscordPrompt: true,
    })
  }

  const completeReviewPrompt = () => {
    if (state === null) return

    setReviewPromptHidden(true)
    void saveSettings({
      ...state.settings,
      didDismissReviewPrompt: true,
    })
  }

  return (
    <>
      <PageLayout
        actions={
          <Button
            className="h-auto shrink-0 self-center !rounded-lg !border-[#1fd47d]/60 !bg-gradient-to-b !from-[#4cf0a8] !to-[#1fd47d] !px-[18px] !py-2.5 !text-[13px] !font-extrabold !text-[#06281a] shadow-[inset_0_1px_0_rgba(255,255,255,0.34),0_10px_24px_-8px_rgba(31,212,125,0.55)] hover:!border-[#1fd47d]/60 hover:brightness-105"
            onClick={() => setEditorState({ mode: "create" })}
            variant="success"
          >
            <Plus aria-hidden className="size-4" />
            New Smart Field
          </Button>
        }
        subtitle="Add automatically generated text, voice, and images to your notes."
        testId="smart-fields-screen"
        title="✨ Smart Fields"
      >
        {error !== null && (
          <ErrorBanner
            className="mb-4"
            message={error}
            onDismiss={() => setError(null)}
          />
        )}

        {bannerPrompt === "review" && (
          <ReviewPrompt onComplete={completeReviewPrompt} />
        )}
        {bannerPrompt === "discord" && (
          <DiscordPrompt onDismiss={dismissDiscordPrompt} />
        )}

        {state === null ? (
          <FieldsSkeleton />
        ) : state.smartFields.length === 0 ? (
          <FieldsEmptyState />
        ) : (
          <div>
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
      </PageLayout>
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
    </>
  )
}
