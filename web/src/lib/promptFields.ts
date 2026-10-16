import type { NoteType, SmartField } from "@/types/api"

export interface ValidPromptFieldsArgs {
  deckId: number
  globalDeckId: number
  // The Smart Field being edited: its current binding goes away when it saves.
  ignoreFieldId?: string | null
  noteType: NoteType | undefined
  smartFields: SmartField[]
  targetFieldName?: string
}

interface MediaFieldNamesArgs {
  deckId: number
  globalDeckId: number
  ignoreFieldId?: string | null
  noteTypeId: number
  smartFields: SmartField[]
}

/** The {{Field}} references in a prompt, skipping cloze deletions. Mirrors the Python `get_prompt_fields`. */
export const getPromptFieldNames = (prompt: string): string[] =>
  [...prompt.matchAll(/\{\{(?!c\d+::)(.+?)\}\}/g)].map((match) => match[1]!)

/**
 * The fields that voice or image Smart Fields fill for a note type in a deck, keyed by
 * lowercased name. Like generation, the deck's own Smart Fields override global ones on
 * the same field.
 */
export const getMediaFieldNames = ({
  deckId,
  globalDeckId,
  ignoreFieldId,
  noteTypeId,
  smartFields,
}: MediaFieldNamesArgs): Map<string, string> => {
  const effectiveFields = new Map<string, SmartField>()
  for (const layerDeckId of [globalDeckId, deckId]) {
    for (const smartField of smartFields) {
      if (
        smartField.id !== ignoreFieldId &&
        smartField.noteTypeId === noteTypeId &&
        smartField.deckId === layerDeckId
      ) {
        effectiveFields.set(
          smartField.targetFieldName.toLowerCase(),
          smartField,
        )
      }
    }
  }
  return new Map(
    [...effectiveFields]
      .filter(([, smartField]) => smartField.fieldType !== "chat")
      .map(([key, smartField]) => [key, smartField.targetFieldName]),
  )
}

/**
 * The fields a prompt or voice field may read. Mirrors the Python
 * `get_valid_fields_for_prompt`: every field on the note type, minus the field being
 * generated, minus fields filled by voice or image Smart Fields — those hold media,
 * not text a prompt can read.
 */
export const getValidPromptFields = ({
  deckId,
  globalDeckId,
  ignoreFieldId,
  noteType,
  smartFields,
  targetFieldName,
}: ValidPromptFieldsArgs): string[] => {
  if (noteType === undefined) return []

  const mediaFieldNames = getMediaFieldNames({
    deckId,
    globalDeckId,
    ignoreFieldId,
    noteTypeId: noteType.id,
    smartFields,
  })

  return noteType.fields.filter(
    (fieldName) =>
      fieldName !== targetFieldName &&
      !mediaFieldNames.has(fieldName.toLowerCase()),
  )
}
