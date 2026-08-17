/*
 * Copyright (C) 2024 Michael Piazza
 *
 * This file is part of Smart Notes.
 *
 * Smart Notes is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Smart Notes is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Smart Notes. If not, see <https://www.gnu.org/licenses/>.
 */

import { hasGenerationAccess } from "@/components/shared/planPresentation"
import { useAppStore } from "@/store/appStore"
import type { AccountState, Deck, NoteType, SelectedNote } from "@/types/api"

import type { PromptTester } from "./usePromptTester"

export const FIELD_REFERENCE_PATTERN = /\{\{([^{}]+)\}\}/g

// Fields the prompt references that the note doesn't have — the run would substitute
// nothing, so it is blocked before it costs a generation.
export const getMissingPromptFieldNames = (
  prompt: string,
  note: SelectedNote,
): string[] =>
  [
    ...new Set(
      [...prompt.matchAll(FIELD_REFERENCE_PATTERN)].map((match) => match[1]!),
    ),
  ].filter((fieldName) => !(fieldName in note.fields))

export interface PromptTestCardState {
  deckName: string
  missingFieldNames: string[]
  noteTypeName: string
  referencedFieldNames: Set<string>
  requiredNoteTypeName: string | undefined
  runDisabled: boolean
}

interface PromptTestCardArgs {
  account: AccountState | null
  decks: Deck[] | null
  noteTypes: NoteType[] | null
  tester: PromptTester
}

// What both tester layouts need to know about the card a run would use: how to name it,
// and whether the run may happen at all.
export const getPromptTestCardState = ({
  account,
  decks,
  noteTypes,
  tester,
}: PromptTestCardArgs): PromptTestCardState => {
  const selectedNote = tester.selectedNote
  const referencedFieldNames = new Set(
    [...tester.prompt.matchAll(FIELD_REFERENCE_PATTERN)].map(
      (match) => match[1]!,
    ),
  )

  const missingFieldNames =
    selectedNote === null
      ? []
      : getMissingPromptFieldNames(tester.prompt, selectedNote)

  return {
    deckName:
      decks?.find((deck) => deck.id === selectedNote?.deckId)?.name ??
      "Selected deck",
    missingFieldNames,
    noteTypeName:
      noteTypes?.find((noteType) => noteType.id === selectedNote?.noteTypeId)
        ?.name ?? "Selected note type",
    referencedFieldNames,
    requiredNoteTypeName: noteTypes?.find(
      (noteType) => noteType.id === tester.requiredNoteTypeId,
    )?.name,
    // A card is needed only when the prompt reads fields off one.
    runDisabled:
      (selectedNote === null && referencedFieldNames.size > 0) ||
      tester.hasNoteTypeMismatch ||
      missingFieldNames.length > 0 ||
      account === null ||
      !hasGenerationAccess(account) ||
      tester.isTesting ||
      tester.prompt.trim() === "",
  }
}

export interface SaveTestResultTarget {
  cardId: number
  fieldName: string
  token: string
}

// A result can be saved to the tested card only if that card actually has the field
// the editor is authoring for — the note type may have changed since the run.
export const getSaveTestResultTarget = ({
  fieldName,
  selectedNote,
  token,
}: {
  fieldName: string
  selectedNote: SelectedNote
  token: string
}): SaveTestResultTarget | null => {
  if (!(fieldName in selectedNote.fields)) return null

  return { cardId: selectedNote.cardId, fieldName, token }
}

export const usePromptTestCardState = (
  tester: PromptTester,
): PromptTestCardState => {
  const account = useAppStore((store) => store.state?.account ?? null)
  const decks = useAppStore((store) => store.state?.decks ?? null)
  const noteTypes = useAppStore((store) => store.state?.noteTypes ?? null)

  return getPromptTestCardState({ account, decks, noteTypes, tester })
}
