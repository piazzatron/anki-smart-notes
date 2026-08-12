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

import { describe, expect, test } from "bun:test"
import { renderToStaticMarkup } from "react-dom/server"

import type { AppState, SmartField } from "@/types/api"

import { createFieldEditorDraft } from "./fieldEditor"
import type { FieldEditorDraft, FieldType } from "./fieldEditor"
import { StepTarget } from "./StepTarget"
import type { FieldEditorControls } from "./useFieldEditor"

const existingField = {
  id: "meaning",
  noteTypeId: 10,
  deckId: 1,
  targetFieldName: "Meaning",
  fieldType: "chat",
  enabled: true,
  settings: {
    promptText: "Translate {{Front}}",
    provider: "auto",
    model: "auto",
    reasoningLevel: "off",
    webSearchEnabled: false,
    usesDefaultGenerationSettings: true,
  },
} as SmartField

const appState = {
  noteTypes: [{ id: 10, name: "Basic", fields: ["Front", "Meaning", "Audio"] }],
  decks: [{ id: 1, name: "Default" }],
  smartFields: [existingField],
  globalDeckId: 1,
} as AppState

describe("StepTarget", () => {
  test("asks the three wizard questions in task order", () => {
    const markup = renderStep()

    expect(markup.indexOf("What do you want to generate?")).toBeLessThan(
      markup.indexOf("Which notes?"),
    )
    expect(markup.indexOf("Which notes?")).toBeLessThan(
      markup.indexOf("Which field should it fill?"),
    )
    expect(markup).toContain('aria-label="Note Type"')
    expect(markup).toContain('aria-label="Deck"')
    expect(markup).toContain('aria-label="Field"')
  })

  test("marks only the selected type badge as checked", () => {
    const markup = renderStep("tts")

    expect(markup).toContain("🔈")
    expect(markup).toContain("💬")
    expect(markup).toContain("🖼️")
    expect(markup.match(/aria-checked="true"/g)).toHaveLength(1)
  })

  test("warns when the chosen field already has a Smart Field", () => {
    const markup = renderStep("chat", "Meaning")

    expect(markup).toContain("already has a Smart Field")
  })
})

const renderStep = (
  fieldType: FieldType = "chat",
  targetFieldName = "Front",
): string => {
  const draft: FieldEditorDraft = createFieldEditorDraft(appState, "create")
  const controls = {
    form: { ...draft, target: { ...draft.target, fieldType, targetFieldName } },
    setTarget: () => undefined,
    update: () => undefined,
  } as unknown as FieldEditorControls

  return renderToStaticMarkup(
    <StepTarget controls={controls} state={appState} />,
  )
}
