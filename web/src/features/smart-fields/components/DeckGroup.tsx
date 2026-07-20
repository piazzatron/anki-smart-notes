import { NoteTypeCard } from "./NoteTypeCard"

import type { DeckGroup as DeckGroupModel } from "../groupSmartFields"
import type { SmartField } from "../types"

interface DeckGroupProps {
  group: DeckGroupModel
  onDelete: (field: SmartField) => Promise<void>
  onToggleEnabled: (field: SmartField) => Promise<void>
  onError: (message: string) => void
}

export const DeckGroup = ({
  group,
  onDelete,
  onToggleEnabled,
  onError,
}: DeckGroupProps) => (
  <section>
    <div className="mb-2.5 flex items-center gap-2 px-0.5 text-[10px] font-semibold tracking-[0.08em] text-ink-muted uppercase">
      <span>{group.isGlobal ? "All decks" : group.deck.name}</span>
      {!group.isGlobal && (
        <span className="rounded border border-amber/15 bg-amber/[0.07] px-1.5 py-0.5 text-[9px] font-medium tracking-normal text-amber normal-case">
          deck-specific override
        </span>
      )}
    </div>

    {group.noteTypes.map((noteTypeGroup) => (
      <NoteTypeCard
        group={noteTypeGroup}
        key={noteTypeGroup.noteType.id}
        onDelete={onDelete}
        onError={onError}
        onToggleEnabled={onToggleEnabled}
      />
    ))}
  </section>
)
