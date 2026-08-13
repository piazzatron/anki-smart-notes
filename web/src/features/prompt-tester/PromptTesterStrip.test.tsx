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

if (!("window" in globalThis)) {
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: { location: { search: "" } },
  })
}

const { PromptTesterStrip, SaveResultButton } =
  await import("./PromptTesterStrip")
const { SelectedTestCard } = await import("./SelectedTestCard")

const selectedNote = {
  cardId: 42,
  deckId: 1,
  fields: { Expression: "食べる", Meaning: "to eat" },
  id: 7,
  noteTypeId: 100,
}

describe("PromptTesterStrip", () => {
  test("keeps the disabled Test action visible in the one-line empty state", () => {
    const markup = renderToStaticMarkup(
      <PromptTesterStrip
        promptLabel="Prompt"
        provenance="Auto"
        saveTargetFieldName="Meaning"
        tester={{
          dismissError: () => undefined,
          error: null,
          hasNoteTypeMismatch: false,
          isPromptEditable: false,
          isTesting: false,
          prompt: "Translate {{Expression}}",
          requiredNoteTypeId: 100,
          result: null,
          runTest: async () => undefined,
          selection: { note: null, count: 0 },
          selectedNote: null,
          setError: () => undefined,
          setPrompt: () => undefined,
        }}
        title="Test your Smart Field"
      >
        <p>Result</p>
      </PromptTesterStrip>,
    )

    expect(markup).toContain("Test your Smart Field")
    expect(markup).toContain("Pick a card in the Anki Browser")
    expect(markup).toContain("Open Anki Browser")
    expect(markup).toContain('disabled=""')
    expect(markup).toContain(">Test</button>")
    expect(markup).not.toContain("This field runs on")
    expect(markup).not.toContain("Your selection appears here automatically")
  })

  test("shows a runnable picked card in the labeled boxed state", () => {
    const markup = renderToStaticMarkup(
      <PromptTesterStrip
        promptLabel="Prompt"
        provenance="Auto"
        saveTargetFieldName="Meaning"
        tester={{
          dismissError: () => undefined,
          error: null,
          hasNoteTypeMismatch: false,
          isPromptEditable: false,
          isTesting: false,
          prompt: "Translate {{Expression}}",
          requiredNoteTypeId: 100,
          result: {
            latencyMs: 125,
            prompt: "Translate {{Expression}}",
            value: { resultToken: "token-1", text: "To eat" },
          },
          runTest: async () => undefined,
          selection: { note: selectedNote },
          selectedNote,
          setError: () => undefined,
          setPrompt: () => undefined,
        }}
        title="Test your Smart Field"
      >
        <p>Result</p>
      </PromptTesterStrip>,
    )

    expect(markup).toContain("Currently selected card")
    expect(markup).toContain("食べる")
    expect(markup).toContain("Selected note type · Selected deck")
    expect(markup).toContain("View result")
    expect(markup).toContain("border-white/10")
    expect(markup).toContain("bg-white/[0.02]")
    expect(markup.match(/h-\[54px\]/g)).toHaveLength(2)
    expect(markup).not.toContain("Change")
  })

  test("keeps an invalid selection to the same fixed-height row", () => {
    const markup = renderToStaticMarkup(
      <SelectedTestCard
        compact
        deckName="Immediate"
        missingFieldNames={[]}
        note={selectedNote}
        noteTypeName="Japanese"
        referencedFieldNames={new Set()}
        requiredNoteTypeName="Basic"
        selection={{ note: selectedNote }}
        showNoteTypeMismatch
      />,
    )

    expect(markup).toContain("h-[54px]")
    expect(markup).toContain("Please select a note of type")
    expect(markup).toContain("Basic")
    // One line beside the browser action: it ellipsizes rather than running under it.
    expect(markup).toContain("truncate")
    expect(markup).not.toContain("This field runs on")
  })
})

describe("PromptTesterStrip owning its prompt", () => {
  test("offers a prompt editor and still keeps the result out of the page", () => {
    const markup = renderToStaticMarkup(
      <PromptTesterStrip
        promptLabel="Text to speak"
        provenance="Auto"
        tester={{
          dismissError: () => undefined,
          error: null,
          hasNoteTypeMismatch: false,
          isPromptEditable: true,
          isTesting: false,
          prompt: "Translate {{Expression}}",
          requiredNoteTypeId: null,
          result: {
            latencyMs: 125,
            prompt: "Translate {{Expression}}",
            value: { resultToken: "token-1", text: "To eat" },
          },
          runTest: async () => undefined,
          selection: { note: selectedNote },
          selectedNote,
          setError: () => undefined,
          setPrompt: () => undefined,
        }}
        title="Try it"
      >
        <p>Inline result sentinel</p>
      </PromptTesterStrip>,
    )

    expect(markup).toContain("Try it")
    expect(markup).toContain("Text to speak")
    expect(markup).toContain("<textarea")
    expect(markup).toContain(">Test</button>")
    expect(markup).not.toContain("Inline result sentinel")
    expect(markup).not.toContain("125ms")
  })

  test("has no prompt editor when something else owns the prompt", () => {
    const markup = renderToStaticMarkup(
      <PromptTesterStrip
        promptLabel="Prompt"
        provenance="Auto"
        saveTargetFieldName="Meaning"
        tester={{
          dismissError: () => undefined,
          error: null,
          hasNoteTypeMismatch: false,
          isPromptEditable: false,
          isTesting: false,
          prompt: "Translate {{Expression}}",
          requiredNoteTypeId: 100,
          result: null,
          runTest: async () => undefined,
          selection: { note: selectedNote },
          selectedNote,
          setError: () => undefined,
          setPrompt: () => undefined,
        }}
        title="Test your Smart Field"
      >
        <p>Result</p>
      </PromptTesterStrip>,
    )

    expect(markup).not.toContain("<textarea")
  })
})

describe("SaveResultButton", () => {
  test("offers the save as the affirmative action in the result modal", () => {
    const markup = renderToStaticMarkup(
      <SaveResultButton
        cardId={42}
        fieldName="Meaning"
        onError={() => undefined}
        token="token-1"
      />,
    )

    expect(markup).toContain("Save to card")
    expect(markup).toContain("bg-mint")
    expect(markup).not.toContain("disabled=")
  })
})
