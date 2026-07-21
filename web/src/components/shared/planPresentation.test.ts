import { describe, expect, test } from "bun:test"

import type { AccountState, SubscriptionState } from "@/types/api"

import {
  getCreditSegments,
  getPlanPresentation,
  hasGenerationAccess,
  pctLabel,
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

const VARIANT_CASES: Array<{
  subscription: SubscriptionState
  variant: ReturnType<typeof getPlanPresentation>["variant"]
  warning: boolean
}> = [
  { subscription: "LOADING", variant: "loading", warning: false },
  {
    subscription: "UNAUTHENTICATED",
    variant: "signed-out",
    warning: false,
  },
  { subscription: "NO_SUBSCRIPTION", variant: "free-cta", warning: false },
  { subscription: "FREE_TRIAL_ACTIVE", variant: "trial", warning: false },
  { subscription: "FREE_TRIAL_EXPIRED", variant: "trial", warning: true },
  { subscription: "FREE_TRIAL_CAPACITY", variant: "trial", warning: true },
  { subscription: "PAID_PLAN_ACTIVE", variant: "paid", warning: false },
  { subscription: "PAID_PLAN_EXPIRED", variant: "paid", warning: true },
  { subscription: "PAID_PLAN_CAPACITY", variant: "paid", warning: true },
]

describe("getPlanPresentation", () => {
  for (const { subscription, variant, warning } of VARIANT_CASES) {
    test(`presents ${subscription}`, () => {
      const plan =
        subscription === "LOADING" ||
        subscription === "UNAUTHENTICATED" ||
        subscription === "NO_SUBSCRIPTION"
          ? null
          : PLAN
      expect(getPlanPresentation({ subscription, plan })).toMatchObject({
        variant,
        warning,
      })
    })
  }

  test("warns when an active trial is near expiry or credit capacity", () => {
    expect(
      getPlanPresentation({
        subscription: "FREE_TRIAL_ACTIVE",
        plan: { ...PLAN, daysLeft: 2 },
      }).warning,
    ).toBe(true)
    expect(
      getPlanPresentation({
        subscription: "FREE_TRIAL_ACTIVE",
        plan: { ...PLAN, totalCreditsUsed: 240 },
      }).warning,
    ).toBe(true)
  })

  test("supports the post-trial free presentation when plan data is present", () => {
    expect(
      getPlanPresentation({
        subscription: "FREE_TRIAL_ACTIVE",
        plan: { ...PLAN, notesUsed: null, notesLimit: null, planName: "Free" },
      }),
    ).toMatchObject({ variant: "free-usage", usagePercent: 15 })
  })
})

describe("credit formatting", () => {
  test("never rounds a nonzero usage down to zero", () => {
    expect(pctLabel(0)).toBe("0%")
    expect(pctLabel(0.4)).toBe("<1%")
    expect(pctLabel(40.6)).toBe("41%")
  })

  test("segments use the shared total capacity", () => {
    expect(getCreditSegments(PLAN).map((segment) => segment.percent)).toEqual([
      10 / 3,
      5 / 3,
      0,
    ])
  })
})

describe("hasGenerationAccess", () => {
  test("allows only active trial and paid subscriptions", () => {
    const states: SubscriptionState[] = VARIANT_CASES.map(
      ({ subscription }) => subscription,
    )
    expect(
      states.filter((subscription) =>
        hasGenerationAccess({ subscription, plan: null }),
      ),
    ).toEqual(["FREE_TRIAL_ACTIVE", "PAID_PLAN_ACTIVE"])
  })
})
