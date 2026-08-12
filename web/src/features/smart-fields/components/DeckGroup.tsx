import { NoteTypeCard } from "./NoteTypeCard"

import type { SmartField } from "@/types/api"

import type { DeckGroup as DeckGroupModel } from "../groupSmartFields"

interface DeckGroupProps {
  group: DeckGroupModel
  onCreate: () => void
  onDelete: (field: SmartField) => Promise<void>
  onDuplicate: (field: SmartField) => void
  onEdit: (field: SmartField) => void
  onToggleEnabled: (field: SmartField) => Promise<void>
  onError: (message: string) => void
}

export const DeckGroup = ({
  group,
  onCreate,
  onDelete,
  onDuplicate,
  onEdit,
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
        onCreate={onCreate}
        onDelete={onDelete}
        onDuplicate={onDuplicate}
        onEdit={onEdit}
        onError={onError}
        onToggleEnabled={onToggleEnabled}
      />
    ))}
  </section>
)
