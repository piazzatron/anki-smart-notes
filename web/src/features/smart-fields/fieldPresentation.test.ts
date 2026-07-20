import { describe, expect, test } from "bun:test"

import {
  smartFieldDescription,
  smartFieldModelLabel,
} from "./fieldPresentation"
import type { SmartField } from "./types"

describe("Smart Field presentation", () => {
  test("shows default Auto as the routing choice", () => {
    const field: SmartField = {
      id: "reading",
      noteTypeId: 1,
      deckId: 1,
      targetFieldName: "Reading",
      fieldType: "chat",
      enabled: true,
      settings: {
        promptText: "Generate {{Front}}",
        provider: "auto",
        model: "auto",
        reasoningLevel: "off",
        webSearchEnabled: false,
        usesDefaultGenerationSettings: true,
      },
    }

    expect(smartFieldModelLabel(field)).toBe("✦ Auto")
    expect(smartFieldDescription(field)).toBe("Generate {{Front}}")
  })

  test("describes TTS using its source field", () => {
    const field: SmartField = {
      id: "audio",
      noteTypeId: 1,
      deckId: 1,
      targetFieldName: "Audio",
      fieldType: "tts",
      enabled: true,
      settings: {
        sourceFieldName: "Front",
        provider: "google",
        model: "standard",
        voiceId: "en-US-Casual-K",
        usesDefaultGenerationSettings: false,
      },
    }

    expect(smartFieldDescription(field)).toBe("Reads {{Front}} aloud")
    expect(smartFieldModelLabel(field)).toBe("Google · en-US-Casual-K")
  })
})
