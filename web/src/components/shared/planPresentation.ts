import type { AccountState, PlanInfo, Settings } from "@/types/api"

export type PlanVariant =
  "loading" | "signed-out" | "trial" | "free-usage" | "paid"

export interface PlanPresentation {
  variant: PlanVariant
  planName: string
  usagePercent: number | null
  warning: boolean
  daysLeft: number | null
  notesUsed: number | null
  notesLimit: number | null
}

export interface CreditSegment {
  key: "text" | "voice" | "images"
  label: string
  percent: number
  color: string
}

export interface PlanConditions {
  expired: boolean
  noteLimitReached: boolean
  creditLimitReached: boolean
  hasGenerationAccess: boolean
}

export const getPlanConditions = (plan: PlanInfo): PlanConditions => {
  const expired = plan.daysLeft <= 0
  const noteLimitReached =
    plan.notesLimit !== null && (plan.notesUsed ?? 0) >= plan.notesLimit
  const creditLimitReached = plan.totalCreditsUsed >= plan.totalCreditsCapacity

  return {
    expired,
    noteLimitReached,
    creditLimitReached,
    hasGenerationAccess: !expired && !noteLimitReached && !creditLimitReached,
  }
}

export const hasGenerationAccess = (account: AccountState): boolean =>
  account.status === "AUTHENTICATED" &&
  getPlanConditions(account.plan).hasGenerationAccess

export const shouldShowTrialEndedTakeover = (
  account: AccountState,
  settings: Pick<Settings, "legacyOpenAiEnabled">,
): boolean => {
  if (account.status !== "AUTHENTICATED") return false
  if (account.plan.planType !== "trial") return false
  if (settings.legacyOpenAiEnabled) return false

  return !getPlanConditions(account.plan).hasGenerationAccess
}

export const getPlanPresentation = (
  account: AccountState,
): PlanPresentation => {
  if (account.status !== "AUTHENTICATED") {
    return presentation(account.status === "LOADING" ? "loading" : "signed-out")
  }

  const conditions = getPlanConditions(account.plan)
  if (account.plan.planType === "trial") {
    return trialPresentation(account.plan, conditions)
  }
  return paidOrFreePresentation(account.plan, conditions)
}

export const getCreditUsagePercent = (plan: PlanInfo | null): number => {
  if (plan === null || plan.totalCreditsCapacity <= 0) return 0
  return Math.min(
    100,
    (plan.totalCreditsUsed / plan.totalCreditsCapacity) * 100,
  )
}

export const pctLabel = (percent: number): string => {
  if (percent > 0 && percent < 1) return "<1%"
  return `${Math.round(percent)}%`
}

export const getCreditSegments = (plan: PlanInfo): CreditSegment[] => {
  const capacity = plan.totalCreditsCapacity
  const toPercent = (used: number) =>
    capacity > 0 ? Math.min(100, (used / capacity) * 100) : 0

  return [
    {
      key: "text",
      label: "Text",
      percent: toPercent(plan.textCreditsUsed),
      color: "#9a9aa4",
    },
    {
      key: "images",
      label: "Images",
      percent: toPercent(plan.imageCreditsUsed),
      color: "#7c8dff",
    },
    {
      key: "voice",
      label: "Voice",
      percent: toPercent(plan.voiceCreditsUsed),
      color: "#5fe3b0",
    },
  ]
}

const presentation = (variant: PlanVariant): PlanPresentation => ({
  variant,
  planName: "",
  usagePercent: null,
  warning: false,
  daysLeft: null,
  notesUsed: null,
  notesLimit: null,
})

const trialPresentation = (
  plan: PlanInfo,
  conditions: PlanConditions,
): PlanPresentation => {
  const usagePercent = getCreditUsagePercent(plan)
  const daysLeft = Math.max(0, plan.daysLeft)

  return {
    variant: "trial",
    planName: plan.planName,
    usagePercent,
    warning:
      !conditions.hasGenerationAccess || daysLeft <= 2 || usagePercent >= 80,
    daysLeft,
    notesUsed: plan.notesUsed,
    notesLimit: plan.notesLimit,
  }
}

const paidOrFreePresentation = (
  plan: PlanInfo,
  conditions: PlanConditions,
): PlanPresentation => {
  const variant = plan.planType === "freemium" ? "free-usage" : "paid"
  const usagePercent = getCreditUsagePercent(plan)
  return {
    variant,
    planName: plan.planName,
    usagePercent,
    warning: !conditions.hasGenerationAccess || usagePercent >= 80,
    daysLeft: Math.max(0, plan.daysLeft),
    notesUsed: plan.notesUsed,
    notesLimit: plan.notesLimit,
  }
}
