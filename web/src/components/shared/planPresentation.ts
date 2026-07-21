import type { AccountState, PlanInfo, SubscriptionState } from "@/types/api"

export type PlanVariant =
  "loading" | "signed-out" | "free-cta" | "trial" | "free-usage" | "paid"

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

export const hasGenerationAccess = (account: AccountState): boolean =>
  account.subscription === "FREE_TRIAL_ACTIVE" ||
  account.subscription === "PAID_PLAN_ACTIVE"

export const getPlanPresentation = (account: AccountState): PlanPresentation =>
  PLAN_PRESENTATIONS[account.subscription](account.plan)

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
      key: "voice",
      label: "Voice",
      percent: toPercent(plan.voiceCreditsUsed),
      color: "#5fe3b0",
    },
    {
      key: "images",
      label: "Images",
      percent: toPercent(plan.imageCreditsUsed),
      color: "#7c8dff",
    },
  ]
}

type PlanPresentationFactory = (plan: PlanInfo | null) => PlanPresentation

const PLAN_PRESENTATIONS: Record<SubscriptionState, PlanPresentationFactory> = {
  LOADING: () => presentation("loading"),
  UNAUTHENTICATED: () => presentation("signed-out"),
  NO_SUBSCRIPTION: (plan) =>
    plan === null
      ? presentation("free-cta")
      : paidOrFreePresentation("free-usage", plan, false),
  FREE_TRIAL_ACTIVE: (plan) =>
    plan?.notesLimit === null
      ? paidOrFreePresentation("free-usage", plan, false)
      : trialPresentation(plan, false),
  FREE_TRIAL_EXPIRED: (plan) => trialPresentation(plan, true),
  FREE_TRIAL_CAPACITY: (plan) => trialPresentation(plan, true),
  PAID_PLAN_ACTIVE: (plan) => paidOrFreePresentation("paid", plan, false),
  PAID_PLAN_EXPIRED: (plan) => paidOrFreePresentation("paid", plan, true),
  PAID_PLAN_CAPACITY: (plan) => paidOrFreePresentation("paid", plan, true),
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
  plan: PlanInfo | null,
  ended: boolean,
): PlanPresentation => {
  const usagePercent = ended ? 100 : getCreditUsagePercent(plan)
  const notesLimit = plan?.notesLimit ?? 50
  const notesUsed = ended ? notesLimit : (plan?.notesUsed ?? 0)
  const daysLeft = ended ? 0 : Math.max(0, plan?.daysLeft ?? 0)

  return {
    variant: "trial",
    planName: plan?.planName ?? "Free Trial",
    usagePercent,
    warning: ended || daysLeft <= 2 || usagePercent >= 80,
    daysLeft,
    notesUsed,
    notesLimit,
  }
}

const paidOrFreePresentation = (
  variant: "free-usage" | "paid",
  plan: PlanInfo | null,
  warning: boolean,
): PlanPresentation => ({
  variant,
  planName: plan?.planName ?? (variant === "free-usage" ? "Free" : "Paid"),
  usagePercent: getCreditUsagePercent(plan),
  warning,
  daysLeft: plan === null ? null : Math.max(0, plan.daysLeft),
  notesUsed: plan?.notesUsed ?? null,
  notesLimit: plan?.notesLimit ?? null,
})
