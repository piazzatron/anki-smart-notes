import { describe, expect, test } from "bun:test"

import {
  selectBannerPrompt,
  selectReviewBanner,
  type BannerPromptState,
  type ReviewBannerKind,
  type ReviewBannerState,
} from "./bannerPrompt"

const base: BannerPromptState = {
  hasState: true,
  didDismissReviewPrompt: false,
  didDismissDiscordPrompt: false,
  reviewDismissedThisSession: false,
  discordDismissedThisSession: false,
}

describe("selectBannerPrompt", () => {
  test("shows the review prompt on a fresh open", () => {
    expect(selectBannerPrompt(base)).toBe("review")
  })

  test("leaves the slot empty right after the review prompt is dismissed", () => {
    // The persisted flag and the session flag both flip on dismissal. The
    // Discord prompt must not pop into the freed slot in the same session.
    expect(
      selectBannerPrompt({
        ...base,
        didDismissReviewPrompt: true,
        reviewDismissedThisSession: true,
      }),
    ).toBeNull()
  })

  test("shows the Discord prompt on the next open after the review was dismissed", () => {
    // Reopen: the session flag has reset, the persisted dismissal carries over.
    expect(selectBannerPrompt({ ...base, didDismissReviewPrompt: true })).toBe(
      "discord",
    )
  })

  test("leaves the slot empty once both prompts have been dismissed", () => {
    expect(
      selectBannerPrompt({
        ...base,
        didDismissReviewPrompt: true,
        didDismissDiscordPrompt: true,
      }),
    ).toBeNull()
  })

  test("shows nothing before app state has loaded", () => {
    expect(selectBannerPrompt({ ...base, hasState: false })).toBeNull()
  })
})

describe("selectReviewBanner", () => {
  const offerBase: ReviewBannerState = {
    reviewFreeMonth: true,
    offerUnlocked: true,
    claimLoading: false,
    claimState: "available",
  }

  test.each<[string, Partial<ReviewBannerState>, ReviewBannerKind]>([
    ["offers the month to a user who can claim it", {}, "offer"],
    [
      "keeps offering it while a claim is pending",
      { claimState: "claimed" },
      "offer",
    ],
    [
      "asks for a plain review when the flag is off",
      { reviewFreeMonth: false },
      "plain",
    ],
    [
      "asks for a plain review when the server refuses the month",
      { claimState: "unavailable" },
      "plain",
    ],
    [
      "asks for a plain review when the claim state couldn't load",
      { claimState: null },
      "plain",
    ],
    [
      "shows nothing before the first generation",
      { offerUnlocked: false },
      null,
    ],
    [
      "shows nothing while the claim state loads",
      { claimLoading: true, claimState: null },
      null,
    ],
  ])("%s", (_, overrides, expected) => {
    expect(selectReviewBanner({ ...offerBase, ...overrides })).toBe(expected)
  })
})
