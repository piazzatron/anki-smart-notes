import { describe, expect, test } from "bun:test"

import type { NoteType, SmartField } from "@/types/api"

import { getValidPromptFields } from "./promptFields"

const noteType: NoteType = {
  id: 10,
  name: "Japanese",
  fields: ["Expression", "Reading", "Meaning", "Audio"],
}

const audioField: SmartField = {
  id: "audio",
  noteTypeId: 10,
  deckId: 1,
  targetFieldName: "Audio",
  fieldType: "tts",
  enabled: true,
  settings: {
    sourceFieldName: "Expression",
    provider: "google",
    model: "standard",
    voiceId: "voice",
    usesDefaultGenerationSettings: true,
  },
}

describe("getValidPromptFields", () => {
  test("drops the target field and fields filled with media", () => {
    expect(
      getValidPromptFields({
        deckId: 1,
        noteType,
        smartFields: [audioField],
        targetFieldName: "Meaning",
      }),
    ).toEqual(["Expression", "Reading"])
  })

  test("keeps every field when nothing is targeted or generated", () => {
    expect(
      getValidPromptFields({ deckId: 1, noteType, smartFields: [] }),
    ).toEqual(["Expression", "Reading", "Meaning", "Audio"])
  })

  test("returns nothing without a note type", () => {
    expect(
      getValidPromptFields({
        deckId: 1,
        noteType: undefined,
        smartFields: [audioField],
      }),
    ).toEqual([])
  })
})
