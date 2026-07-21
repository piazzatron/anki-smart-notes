import { describe, expect, test } from "bun:test"

import type { AccountState } from "@/types/api"

import { getPlanPresentation, hasGenerationAccess } from "./planPresentation"

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
      detail: "Sign in to use Smart Notes.",
      usagePercent: null,
      tone: "neutral",
      actionLabel: "Sign in",
    })
  })
})

describe("hasGenerationAccess", () => {
  test("allows only active trial and paid subscriptions", () => {
    const available = ["FREE_TRIAL_ACTIVE", "PAID_PLAN_ACTIVE"] satisfies Array<
      AccountState["subscription"]
    >
    const unavailable = [
      "LOADING",
      "UNAUTHENTICATED",
      "NO_SUBSCRIPTION",
      "FREE_TRIAL_EXPIRED",
      "FREE_TRIAL_CAPACITY",
      "PAID_PLAN_EXPIRED",
      "PAID_PLAN_CAPACITY",
    ] satisfies Array<AccountState["subscription"]>

    expect(
      available.map((subscription) =>
        hasGenerationAccess({ subscription, plan: null }),
      ),
    ).toEqual([true, true])
    expect(
      unavailable.map((subscription) =>
        hasGenerationAccess({ subscription, plan: null }),
      ),
    ).toEqual([false, false, false, false, false, false, false])
  })
})
