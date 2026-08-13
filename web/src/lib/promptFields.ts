import type { NoteType, SmartField } from "@/types/api"

interface ValidPromptFieldsArgs {
  deckId: number
  noteType: NoteType | undefined
  smartFields: SmartField[]
  targetFieldName?: string
}

/**
 * The fields a prompt may reference as {{Field}}. Mirrors the Python
 * `get_valid_fields_for_prompt`: every field on the note type, minus the field being
 * generated, minus fields filled by voice or image Smart Fields — those hold media,
 * not text a prompt can read.
 */
export const getValidPromptFields = ({
  deckId,
  noteType,
  smartFields,
  targetFieldName,
}: ValidPromptFieldsArgs): string[] => {
  if (noteType === undefined) return []

  const mediaFieldNames = new Set(
    smartFields
      .filter(
        (smartField) =>
          smartField.noteTypeId === noteType.id &&
          smartField.deckId === deckId &&
          smartField.fieldType !== "chat",
      )
      .map((smartField) => smartField.targetFieldName),
  )

  return noteType.fields.filter(
    (fieldName) =>
      fieldName !== targetFieldName && !mediaFieldNames.has(fieldName),
  )
}
