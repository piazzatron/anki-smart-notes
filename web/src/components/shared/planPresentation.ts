import type { AccountState, PlanInfo, SubscriptionState } from "@/types/api"

export interface PlanPresentation {
  title: string
  detail: string
  usagePercent: number | null
  tone: "neutral" | "signedOut" | "success" | "warning"
  actionLabel: string
}

export const hasGenerationAccess = (account: AccountState): boolean =>
  account.subscription === "FREE_TRIAL_ACTIVE" ||
  account.subscription === "PAID_PLAN_ACTIVE"

export const getPlanPresentation = (account: AccountState): PlanPresentation =>
  PLAN_PRESENTATIONS[account.subscription](account.plan)

type PlanPresentationFactory = (plan: PlanInfo | null) => PlanPresentation

const PLAN_PRESENTATIONS: Record<SubscriptionState, PlanPresentationFactory> = {
  LOADING: () => ({
    title: "Checking plan…",
    detail: "",
    usagePercent: null,
    tone: "neutral",
    actionLabel: "Subscription",
  }),
  UNAUTHENTICATED: () => ({
    ...SIGNED_OUT_PRESENTATION,
    tone: "signedOut",
  }),
  NO_SUBSCRIPTION: (plan) => getPaidPresentation(plan, "neutral"),
  FREE_TRIAL_ACTIVE: (plan) =>
    getTrialPresentation(
      plan,
      plan !== null && plan.daysLeft <= 2 ? "warning" : "success",
    ),
  FREE_TRIAL_EXPIRED: (plan) => getTrialPresentation(plan, "warning"),
  FREE_TRIAL_CAPACITY: (plan) => getTrialPresentation(plan, "warning"),
  PAID_PLAN_ACTIVE: (plan) => getPaidPresentation(plan, "neutral"),
  PAID_PLAN_EXPIRED: (plan) => getPaidPresentation(plan, "warning"),
  PAID_PLAN_CAPACITY: (plan) => getPaidPresentation(plan, "warning"),
}

const SIGNED_OUT_PRESENTATION: PlanPresentation = {
  title: "Signed out",
  detail: "Sign in to use Smart Notes.",
  usagePercent: null,
  tone: "neutral",
  actionLabel: "Sign in",
}

const getTrialPresentation = (
  plan: PlanInfo | null,
  tone: PlanPresentation["tone"],
): PlanPresentation => {
  if (plan === null) return SIGNED_OUT_PRESENTATION

  const noteUsage =
    plan.notesUsed !== null && plan.notesLimit !== null
      ? ` · ${plan.notesUsed}/${plan.notesLimit} notes`
      : ""

  return {
    title: "Trial",
    detail: `${Math.max(0, plan.daysLeft)} days left${noteUsage}`,
    usagePercent: getUsagePercent(plan),
    tone,
    actionLabel: "Upgrade",
  }
}

const getPaidPresentation = (
  plan: PlanInfo | null,
  tone: PlanPresentation["tone"],
): PlanPresentation => {
  if (plan === null) return SIGNED_OUT_PRESENTATION

  const usagePercent = getUsagePercent(plan)

  return {
    title: plan.planName,
    detail: `${usagePercent}% of credits used`,
    usagePercent,
    tone,
    actionLabel: "Manage",
  }
}

const getUsagePercent = (plan: PlanInfo): number =>
  plan.totalCreditsCapacity > 0
    ? Math.min(
        100,
        Math.round((plan.totalCreditsUsed / plan.totalCreditsCapacity) * 100),
      )
    : 0
