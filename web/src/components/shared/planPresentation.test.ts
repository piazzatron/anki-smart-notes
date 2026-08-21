import { describe, expect, test } from "bun:test"

import type { AccountState, PlanInfo } from "@/types/api"

import {
  getCreditSegments,
  getPlanConditions,
  getPlanPresentation,
  hasGenerationAccess,
  pctLabel,
  shouldShowTrialEndedTakeover,
} from "./planPresentation"

const PLAN: NonNullable<AccountState["plan"]> = {
  planId: "free",
  planType: "trial",
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

const authenticated = (plan: PlanInfo = PLAN): AccountState => ({
  status: "AUTHENTICATED",
  plan,
  email: "person@example.com",
  authToken: null,
})

describe("getPlanPresentation", () => {
  test("presents pending account states", () => {
    expect(
      getPlanPresentation({
        status: "LOADING",
        plan: null,
        email: null,
        authToken: null,
      }),
    ).toMatchObject({ variant: "loading", warning: false })
    expect(
      getPlanPresentation({
        status: "UNAUTHENTICATED",
        plan: null,
        email: null,
        authToken: null,
      }),
    ).toMatchObject({ variant: "signed-out", warning: false })
  })

  test("derives presentation variants from planType", () => {
    expect(getPlanPresentation(authenticated())).toMatchObject({
      variant: "trial",
    })
    expect(
      getPlanPresentation(
        authenticated({
          ...PLAN,
          planId: "free_mini_1",
          planType: "freemium",
          planName: "Free",
          notesUsed: null,
          notesLimit: null,
        }),
      ),
    ).toMatchObject({ variant: "free-usage", usagePercent: 15 })
    expect(
      getPlanPresentation(
        authenticated({
          ...PLAN,
          planId: "medium1",
          planType: "medium",
          planName: "Standard",
        }),
      ),
    ).toMatchObject({ variant: "paid" })
  })

  test("warns near trial expiry or credit capacity", () => {
    expect(
      getPlanPresentation(authenticated({ ...PLAN, daysLeft: 2 })).warning,
    ).toBe(true)
    expect(
      getPlanPresentation(authenticated({ ...PLAN, totalCreditsUsed: 240 }))
        .warning,
    ).toBe(true)
  })

  test("keeps real usage metrics when a trial expires", () => {
    expect(
      getPlanPresentation(authenticated({ ...PLAN, daysLeft: 0 })),
    ).toMatchObject({
      daysLeft: 0,
      notesUsed: 12,
      usagePercent: 15,
      warning: true,
    })
  })
})

describe("getPlanConditions", () => {
  test("reports independent blockers that can coexist", () => {
    expect(
      getPlanConditions({
        ...PLAN,
        daysLeft: 0,
        notesUsed: 50,
        totalCreditsUsed: 300,
      }),
    ).toEqual({
      expired: true,
      noteLimitReached: true,
      creditLimitReached: true,
      hasGenerationAccess: false,
    })
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
      0,
      5 / 3,
    ])
  })
})

describe("hasGenerationAccess", () => {
  test("requires authentication and a plan without blockers", () => {
    expect(hasGenerationAccess(authenticated())).toBe(true)
    expect(
      hasGenerationAccess({
        status: "UNAUTHENTICATED",
        plan: null,
        email: null,
        authToken: null,
      }),
    ).toBe(false)
    expect(hasGenerationAccess(authenticated({ ...PLAN, daysLeft: 0 }))).toBe(
      false,
    )
  })
})

describe("shouldShowTrialEndedTakeover", () => {
  test("does not take over the app for legacy-entitled users", () => {
    const endedTrial = authenticated({ ...PLAN, daysLeft: 0 })

    expect(
      shouldShowTrialEndedTakeover(endedTrial, {
        legacyOpenAiEnabled: false,
      }),
    ).toBe(true)
    expect(
      shouldShowTrialEndedTakeover(endedTrial, {
        legacyOpenAiEnabled: true,
      }),
    ).toBe(false)
    expect(
      shouldShowTrialEndedTakeover(authenticated(), {
        legacyOpenAiEnabled: false,
      }),
    ).toBe(false)
  })
})
