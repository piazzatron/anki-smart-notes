import type { AppState } from "@/store/appStore"

import type { SmartField } from "./types"

type Deck = AppState["decks"][number]
type NoteType = AppState["noteTypes"][number]

export interface NoteTypeGroup {
  noteType: NoteType
  fields: SmartField[]
}

export interface DeckGroup {
  deck: Deck
  isGlobal: boolean
  noteTypes: NoteTypeGroup[]
}

export const groupSmartFields = (state: AppState): DeckGroup[] => {
  const decksById = new Map(state.decks.map((deck) => [deck.id, deck]))
  const noteTypesById = new Map(
    state.noteTypes.map((noteType) => [noteType.id, noteType]),
  )
  const noteTypeOrder = new Map(
    state.noteTypes.map((noteType, index) => [noteType.id, index]),
  )
  const groups = new Map<number, Map<number, SmartField[]>>()

  for (const field of state.smartFields) {
    if (!decksById.has(field.deckId)) {
      throw new Error(
        `Smart Field ${field.id} references missing deck ${field.deckId}`,
      )
    }
    if (!noteTypesById.has(field.noteTypeId)) {
      throw new Error(
        `Smart Field ${field.id} references missing note type ${field.noteTypeId}`,
      )
    }

    const deckFields =
      groups.get(field.deckId) ?? new Map<number, SmartField[]>()
    const noteTypeFields = deckFields.get(field.noteTypeId) ?? []
    groups.set(field.deckId, deckFields)
    deckFields.set(field.noteTypeId, [...noteTypeFields, field])
  }

  return [...groups.entries()]
    .map(([deckId, noteTypeFields]) => ({
      deck: decksById.get(deckId)!,
      isGlobal: deckId === state.globalDeckId,
      noteTypes: [...noteTypeFields.entries()]
        .map(([noteTypeId, fields]) => ({
          noteType: noteTypesById.get(noteTypeId)!,
          fields,
        }))
        .sort(
          (left, right) =>
            noteTypeOrder.get(left.noteType.id)! -
            noteTypeOrder.get(right.noteType.id)!,
        ),
    }))
    .sort((left, right) => {
      if (left.isGlobal) return -1
      if (right.isGlobal) return 1
      return left.deck.name.localeCompare(right.deck.name)
    })
}
