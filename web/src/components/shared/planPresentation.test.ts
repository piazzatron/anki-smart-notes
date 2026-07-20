import { describe, expect, test } from "bun:test"

import type { AccountState } from "./planPresentation"

import { getPlanPresentation } from "./planPresentation"

const PLAN: NonNullable<AccountState["plan"]> = {
  planId: "free",
  planName: "Free Trial",
  notesUsed: 12,
  notesLimit: 50,
  daysLeft: 5,
  textCreditsUsed: 10,
  textCreditsCapacity: 100,
  voiceCreditsUsed: 5,
  voiceCreditsCapacity: 100,
  imageCreditsUsed: 0,
  imageCreditsCapacity: 100,
  totalCreditsUsed: 45,
  totalCreditsCapacity: 300,
}

describe("getPlanPresentation", () => {
  test("presents an active trial without inventing a free-plan state", () => {
    const account: AccountState = {
      subscription: "FREE_TRIAL_ACTIVE",
      plan: PLAN,
    }

    expect(getPlanPresentation(account)).toEqual({
      title: "Trial",
      detail: "5 days left · 12/50 notes",
      usagePercent: 15,
      tone: "success",
      actionLabel: "Upgrade",
    })
  })

  test("presents signed-out state without usage", () => {
    expect(
      getPlanPresentation({ subscription: "UNAUTHENTICATED", plan: null }),
    ).toEqual({
      title: "Signed out",
      detail: "Generation is paused",
      usagePercent: null,
      tone: "neutral",
      actionLabel: "Sign in",
    })
  })
})
