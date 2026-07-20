type SubscriptionState =
  | "LOADING"
  | "UNAUTHENTICATED"
  | "NO_SUBSCRIPTION"
  | "FREE_TRIAL_ACTIVE"
  | "FREE_TRIAL_EXPIRED"
  | "FREE_TRIAL_CAPACITY"
  | "PAID_PLAN_ACTIVE"
  | "PAID_PLAN_EXPIRED"
  | "PAID_PLAN_CAPACITY"

interface PlanInfo {
  planId: string
  planName: string
  notesUsed: number | null
  notesLimit: number | null
  daysLeft: number
  textCreditsUsed: number
  textCreditsCapacity: number
  voiceCreditsUsed: number
  voiceCreditsCapacity: number
  imageCreditsUsed: number
  imageCreditsCapacity: number
  totalCreditsUsed: number
  totalCreditsCapacity: number
}

export interface AccountState {
  subscription: SubscriptionState
  plan: PlanInfo | null
}

interface PlanPresentation {
  title: string
  detail: string
  usagePercent: number | null
  tone: "neutral" | "success" | "warning"
  actionLabel: string
}

export const getPlanPresentation = (
  account: AccountState,
): PlanPresentation => {
  const { plan, subscription } = account

  if (subscription === "LOADING") {
    return {
      title: "Checking plan…",
      detail: "",
      usagePercent: null,
      tone: "neutral",
      actionLabel: "Subscription",
    }
  }

  if (plan === null) {
    return {
      title: "Signed out",
      detail: "Generation is paused",
      usagePercent: null,
      tone: "neutral",
      actionLabel: "Sign in",
    }
  }

  const usagePercent =
    plan.totalCreditsCapacity > 0
      ? Math.min(
          100,
          Math.round((plan.totalCreditsUsed / plan.totalCreditsCapacity) * 100),
        )
      : 0
  const isWarning =
    subscription.endsWith("CAPACITY") ||
    subscription.endsWith("EXPIRED") ||
    (subscription === "FREE_TRIAL_ACTIVE" && plan.daysLeft <= 2)

  if (subscription.startsWith("FREE_TRIAL")) {
    const noteUsage =
      plan.notesUsed !== null && plan.notesLimit !== null
        ? ` · ${plan.notesUsed}/${plan.notesLimit} notes`
        : ""

    return {
      title: "Trial",
      detail: `${Math.max(0, plan.daysLeft)} days left${noteUsage}`,
      usagePercent,
      tone: isWarning ? "warning" : "success",
      actionLabel: "Upgrade",
    }
  }

  return {
    title: plan.planName,
    detail: `${usagePercent}% of credits used`,
    usagePercent,
    tone: isWarning ? "warning" : "neutral",
    actionLabel: "Manage",
  }
}
