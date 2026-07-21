import { describe, expect, test } from "bun:test"

import type { AccountState, SubscriptionState } from "@/types/api"

import {
  getPlanPresentation,
  hasGenerationAccess,
  type PlanPresentation,
} from "./planPresentation"

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

const SIGNED_OUT_PRESENTATION: PlanPresentation = {
  title: "Signed out",
  detail: "Sign in to use Smart Notes.",
  usagePercent: null,
  tone: "neutral",
  actionLabel: "Sign in",
}

const TRIAL_PRESENTATION: PlanPresentation = {
  title: "Trial",
  detail: "5 days left · 12/50 notes",
  usagePercent: 15,
  tone: "success",
  actionLabel: "Upgrade",
}

const PAID_PRESENTATION: PlanPresentation = {
  title: "Free Trial",
  detail: "15% of credits used",
  usagePercent: 15,
  tone: "neutral",
  actionLabel: "Manage",
}

const PRESENTATION_CASES: Array<{
  subscription: SubscriptionState
  plan: AccountState["plan"]
  expected: PlanPresentation
}> = [
  {
    subscription: "LOADING",
    plan: null,
    expected: {
      title: "Checking plan…",
      detail: "",
      usagePercent: null,
      tone: "neutral",
      actionLabel: "Subscription",
    },
  },
  {
    subscription: "UNAUTHENTICATED",
    plan: null,
    expected: { ...SIGNED_OUT_PRESENTATION, tone: "signedOut" },
  },
  {
    subscription: "NO_SUBSCRIPTION",
    plan: null,
    expected: SIGNED_OUT_PRESENTATION,
  },
  {
    subscription: "FREE_TRIAL_ACTIVE",
    plan: PLAN,
    expected: TRIAL_PRESENTATION,
  },
  {
    subscription: "FREE_TRIAL_EXPIRED",
    plan: PLAN,
    expected: { ...TRIAL_PRESENTATION, tone: "warning" },
  },
  {
    subscription: "FREE_TRIAL_CAPACITY",
    plan: PLAN,
    expected: { ...TRIAL_PRESENTATION, tone: "warning" },
  },
  {
    subscription: "PAID_PLAN_ACTIVE",
    plan: PLAN,
    expected: PAID_PRESENTATION,
  },
  {
    subscription: "PAID_PLAN_EXPIRED",
    plan: PLAN,
    expected: { ...PAID_PRESENTATION, tone: "warning" },
  },
  {
    subscription: "PAID_PLAN_CAPACITY",
    plan: PLAN,
    expected: { ...PAID_PRESENTATION, tone: "warning" },
  },
]

describe("getPlanPresentation", () => {
  for (const { subscription, plan, expected } of PRESENTATION_CASES) {
    test(`presents ${subscription}`, () => {
      expect(getPlanPresentation({ subscription, plan })).toEqual(expected)
    })
  }

  test("warns when an active trial is near expiry", () => {
    expect(
      getPlanPresentation({
        subscription: "FREE_TRIAL_ACTIVE",
        plan: { ...PLAN, daysLeft: 2 },
      }).tone,
    ).toBe("warning")
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
