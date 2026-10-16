import { describe, expect, test } from "bun:test"
import type { TFunction } from "i18next"

import type { AssistantActiveTarget, AssistantTargetHandle } from "@/types/api"

import { describeAssistantTarget } from "./assistantHeader"

// Copy changes freely; the key chosen for a mode does not. Interpolations come
// back so a test can prove what the header was handed.
const t = ((key: string, params?: Record<string, string>) =>
  params === undefined ? key : `${key}:${JSON.stringify(params)}`) as TFunction

const SECRET = "<b>mitochondria</b>"

const targetWith = (
  handle: AssistantTargetHandle,
  deckName: string | null = "Biology",
): AssistantActiveTarget => ({
  handle,
  noteTypeId: 1,
  noteTypeName: "Basic",
  deckId: deckName === null ? null : 2,
  deckName,
  fieldNames: ["Front", "Back"],
  firstFieldName: "Front",
  firstFieldValue: SECRET,
})

describe("describeAssistantTarget", () => {
  test("names the deck while reviewing, never the card", () => {
    const copy = describeAssistantTarget(
      targetWith({ mode: "review", cardId: 42 }),
      t,
    )

    expect(copy.mode).toBe("assistant.header.reviewing")
    expect(copy.target).toBe("Biology")
    expect(copy.subline).toBe("Basic")
    expect(copy.target).not.toContain("mitochondria")
    expect(copy.subline).not.toContain("mitochondria")
  })

  test("falls back to the note type when a reviewed card has no deck", () => {
    const copy = describeAssistantTarget(
      targetWith({ mode: "review", cardId: 42 }, null),
      t,
    )

    expect(copy.target).toBe("Basic")
    expect(copy.target).not.toContain("mitochondria")
  })

  test("names what is about to be made while adding", () => {
    const copy = describeAssistantTarget(
      targetWith({ mode: "add", bufferId: "b1" }),
      t,
    )

    expect(copy.mode).toBe("assistant.header.adding")
    expect(copy.target).toBe("assistant.header.addTarget")
    expect(copy.subline).toContain("Biology")
  })

  test("drops the deck clause when adding without one", () => {
    const copy = describeAssistantTarget(
      targetWith({ mode: "add", bufferId: "b1" }, null),
      t,
    )

    expect(copy.subline).toBe("Basic")
  })

  test("names the selected card itself, as plain text", () => {
    const copy = describeAssistantTarget(
      targetWith({ mode: "edit", noteId: 7, bufferId: "b1" }),
      t,
    )

    expect(copy.mode).toBe("assistant.header.currentCard")
    expect(copy.target).toBe("mitochondria")
    expect(copy.subline).toBe("Basic")
  })

  test("says only that no card is selected when nothing is bound", () => {
    const copy = describeAssistantTarget(null, t)

    expect(copy.mode).toBeNull()
    expect(copy.target).toBe("assistant.header.noneTarget")
    expect(copy.subline).toBe("")
  })
})
