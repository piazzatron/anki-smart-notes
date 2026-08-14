import { NoteTypeCard } from "./NoteTypeCard"

import type { SmartField } from "@/types/api"

import type { DeckGroup as DeckGroupModel } from "../groupSmartFields"

interface DeckGroupProps {
  group: DeckGroupModel
  onCreate: (noteTypeId: number) => void
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
    {group.noteTypes.map((noteTypeGroup) => (
      <NoteTypeCard
        deckName={group.isGlobal ? "All decks" : group.deck.name}
        group={noteTypeGroup}
        isDeckOverride={!group.isGlobal}
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
