import type { TFunction } from "i18next"

import type { AssistantActiveTarget } from "@/types/api"

export interface AssistantHeaderCopy {
  /** The uppercase mode pill, absent when nothing is open. */
  mode: string | null
  target: string
  /** Empty when the target needs no second line. */
  subline: string
}

/**
 * What the chat header says the assistant is looking at.
 *
 * Mode gates what the assistant can do, so it is stated rather than inferred.
 * Review deliberately names the deck instead of the card: showing the first
 * field would give the answer away mid-review. Outside review there is nothing
 * to spoil, so the card names itself.
 */
export const describeAssistantTarget = (
  target: AssistantActiveTarget | null,
  t: TFunction,
): AssistantHeaderCopy => {
  // Nothing bound says all there is to say, so there is no second line.
  if (target === null)
    return {
      mode: null,
      target: t("assistant.header.noneTarget"),
      subline: "",
    }

  const noteType = target.noteTypeName
  const mode = target.handle.mode

  // Sublines identify the target and nothing else — what the assistant does
  // with it is not the header's job.
  if (mode === "review")
    return {
      mode: t("assistant.header.reviewing"),
      target: target.deckName ?? noteType,
      subline: noteType,
    }

  if (mode === "add")
    return {
      mode: t("assistant.header.adding"),
      target: t("assistant.header.addTarget"),
      subline:
        target.deckName === null
          ? noteType
          : t("assistant.header.addSubline", {
              deck: target.deckName,
              noteType,
            }),
    }

  // Not "Editing": the assistant is bound to whichever card is currently
  // selected, which says nothing about whether the user is editing it.
  return {
    mode: t("assistant.header.currentCard"),
    target:
      stripHtml(target.firstFieldValue) ||
      noteType ||
      t("assistant.header.untitled"),
    subline: noteType,
  }
}

/** Anki fields hold HTML; the header shows a plain-text preview. */
export const stripHtml = (value: string): string =>
  value
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim()
