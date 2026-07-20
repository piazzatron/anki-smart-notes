import { AlertCircle, Plus, Sparkles, X } from "lucide-react"
import { useMemo, useState } from "react"

import { DeckGroup } from "./components/DeckGroup"
import { FieldsEmptyState } from "./components/FieldsEmptyState"
import { FieldsSkeleton } from "./components/FieldsSkeleton"
import { groupSmartFields } from "./groupSmartFields"
import type { SmartField } from "./types"

import { Button } from "@/components/ui/Button"
import { deleteSmartField, setSmartFieldEnabled } from "@/services/commands"
import type { AppState } from "@/store/appStore"

interface SmartFieldsScreenProps {
  state: AppState | null
}

export const SmartFieldsScreen = ({ state }: SmartFieldsScreenProps) => {
  const [error, setError] = useState<string | null>(null)
  const groups = useMemo(
    () => (state === null ? [] : groupSmartFields(state)),
    [state],
  )

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
          aria-describedby="new-field-status"
          className="shrink-0"
          disabled
          title="The field editor is the next rebuild slice"
          variant="primary"
        >
          <Plus aria-hidden className="size-3.5" />
          New Smart Field
        </Button>
        <span className="sr-only" id="new-field-status">
          The field editor is not available in this build yet.
        </span>
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
          <FieldsEmptyState />
        ) : (
          <div className="px-6 py-5">
            {groups.map((group) => (
              <DeckGroup
                group={group}
                key={group.deck.id}
                onDelete={deleteSmartField}
                onError={setError}
                onToggleEnabled={toggleEnabled}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
