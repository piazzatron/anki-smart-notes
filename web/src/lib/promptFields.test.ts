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
        globalDeckId: 1,
        noteType,
        smartFields: [audioField],
        targetFieldName: "Meaning",
      }),
    ).toEqual(["Expression", "Reading"])
  })

  test("keeps every field when nothing is targeted or generated", () => {
    expect(
      getValidPromptFields({
        deckId: 1,
        globalDeckId: 1,
        noteType,
        smartFields: [],
      }),
    ).toEqual(["Expression", "Reading", "Meaning", "Audio"])
  })

  test("applies global media fields under deck overrides, ignoring case", () => {
    const globalAudio = { ...audioField, deckId: 1, targetFieldName: "audio" }
    const deckReading: SmartField = {
      ...audioField,
      id: "reading",
      deckId: 2,
      targetFieldName: "Reading",
    }
    const globalReading: SmartField = {
      ...audioField,
      id: "global-reading",
      deckId: 1,
      targetFieldName: "Reading",
    }
    const deckReadingText: SmartField = {
      id: "reading-text",
      noteTypeId: 10,
      deckId: 2,
      targetFieldName: "Reading",
      fieldType: "chat",
      enabled: true,
      settings: {
        promptText: "{{Expression}}",
        provider: "auto",
        model: "auto",
        reasoningLevel: "off",
        webSearchEnabled: false,
        usesDefaultGenerationSettings: true,
      },
    }
    const args = {
      deckId: 2,
      globalDeckId: 1,
      noteType,
      targetFieldName: "Meaning",
    }

    expect(
      getValidPromptFields({
        ...args,
        smartFields: [globalAudio, deckReading],
      }),
    ).toEqual(["Expression"])
    expect(
      getValidPromptFields({
        ...args,
        smartFields: [globalReading, deckReadingText],
      }),
    ).toEqual(["Expression", "Reading", "Audio"])
  })

  test("returns nothing without a note type", () => {
    expect(
      getValidPromptFields({
        deckId: 1,
        globalDeckId: 1,
        noteType: undefined,
        smartFields: [audioField],
      }),
    ).toEqual([])
  })
})
