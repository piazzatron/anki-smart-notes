import { ProgressBar } from "@/components/ui/ProgressBar"
import { SparklesIcon } from "@/components/shared/Icons"
import { openSiteLink, SITE_LINKS } from "@/lib/siteLinks"
import type { AccountState, PlanInfo } from "@/types/api"
import { useTranslation } from "react-i18next"

import {
  getPaidPlanCardState,
  getPlanConditions,
  dailyResetTime,
  getPlanPresentation,
  pctLabel,
} from "./planPresentation"

interface PlanCardProps {
  account: AccountState
  onOpenSubscription: () => void
}

const PLAN_ACTION_BUTTON_CLASS =
  "mint-cta mt-3 block border w-full rounded-lg px-2 py-2.5 text-center text-[13px] font-semibold shadow-[inset_0_1px_rgba(255,255,255,0.34),0_10px_22px_-8px_rgba(31,212,125,0.55)] transition"
const TRIAL_ACTION_BUTTON_CLASS =
  "mt-3 block w-full rounded-lg bg-indigo/80 px-2 py-2 text-center text-[13px] font-medium text-white transition hover:bg-indigo/90"

export const PlanCard = ({ account, onOpenSubscription }: PlanCardProps) => {
  const { t } = useTranslation()
  const presentation = getPlanPresentation(account)

  if (presentation.variant === "loading") {
    return (
      <div
        aria-label={t("subscription.checking")}
        className="animate-pulse space-y-2 px-0.5 py-1"
        data-testid="plan-card"
      >
        <div className="h-2.5 w-20 rounded bg-white/[0.06]" />
        <div className="h-1 w-full rounded bg-white/[0.04]" />
      </div>
    )
  }

  if (presentation.variant === "signed-out") {
    return (
      <section
        className="rounded-[11px] bg-white/[0.05] p-3"
        data-testid="plan-card"
      >
        <div className="flex items-center gap-2">
          <span
            aria-hidden
            className="size-1.5 rounded-full bg-caution shadow-[0_0_8px_rgba(255,155,94,0.65)]"
          />
          <p className="text-sm font-semibold text-ink">
            {t("subscription.signedOut.title")}
          </p>
        </div>
        <p className="mt-1.5 text-xs leading-[1.45] text-zinc-400">
          {t("subscription.signedOut.paused")}
        </p>
        <button
          className={PLAN_ACTION_BUTTON_CLASS}
          onClick={() => openSiteLink(SITE_LINKS.signIn)}
        >
          {t("common.signIn")}
        </button>
      </section>
    )
  }

  if (account.status !== "AUTHENTICATED") return null

  const usage = presentation.usagePercent ?? 0
  const conditions = getPlanConditions(account.plan)

  if (presentation.variant === "trial") {
    if (!conditions.hasGenerationAccess) {
      const title = conditions.creditLimitReached
        ? t("subscription.outOfCredits")
        : conditions.noteLimitReached
          ? t("subscription.trialNoteLimitReached")
          : t("subscription.trialEnded")
      return (
        <OutOfCreditsCard
          note={t("subscription.upgradeToKeepGenerating")}
          onOpenSubscription={onOpenSubscription}
          title={title}
          usage={usage}
        />
      )
    }

    const daysLeft = presentation.daysLeft ?? 0
    const ending = daysLeft <= 2
    const accentClass = ending ? "text-caution-soft" : "text-mint"
    const meterClass = ending ? "bg-caution" : "bg-mint"

    return (
      <section
        className="rounded-[11px] bg-white/[0.05] p-3"
        data-testid="plan-card"
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-ink-muted">
            {t("subscription.freeTrial")}
          </span>
          <span className={`text-xs font-semibold ${accentClass}`}>
            {t("subscription.daysLeft", { count: daysLeft })}
          </span>
        </div>
        <ProgressBar
          colorClass={meterClass}
          heightClass="h-1"
          percent={Math.min(100, (daysLeft / account.plan.totalDays) * 100)}
          trackClass="mt-2.5 bg-white/[0.08]"
        />
        <button
          className={TRIAL_ACTION_BUTTON_CLASS}
          onClick={onOpenSubscription}
        >
          {t("common.upgrade")}
        </button>
      </section>
    )
  }

  if (presentation.variant === "free") {
    return <FreePlanCard plan={account.plan} />
  }

  if (presentation.variant === "paid") {
    const cardState = getPaidPlanCardState(account.plan)
    if (cardState !== "available") {
      if (cardState === "expired") {
        return (
          <OutOfCreditsCard
            actionLabel={t("subscription.managePlan")}
            note={t("subscription.resubscribeToContinue")}
            onOpenSubscription={onOpenSubscription}
            showUsage={false}
            title={t("subscription.planExpired")}
            usage={usage}
          />
        )
      }

      return (
        <OutOfCreditsCard
          note={
            account.plan.subscriptionStatus === "canceling"
              ? undefined
              : t("subscription.pausedUntilReset")
          }
          onOpenSubscription={onOpenSubscription}
          title={
            conditions.creditLimitReached
              ? t("subscription.outOfCredits")
              : conditions.noteLimitReached
                ? t("subscription.noteLimitReached")
                : t("subscription.planInactive")
          }
          usage={usage}
        />
      )
    }

    return (
      <button
        className="block w-full px-nav py-1 text-start"
        data-testid="plan-card"
        onClick={onOpenSubscription}
      >
        <span className="flex items-center justify-between text-xs">
          <span className="text-ink-muted">{t("subscription.usage")}</span>
          <span className="font-medium text-zinc-400">{pctLabel(usage)}</span>
        </span>
        <ProgressBar
          colorClass="bg-zinc-600"
          heightClass="h-[3px]"
          percent={usage}
          trackClass="mt-1.5 bg-white/[0.07]"
        />
      </button>
    )
  }

  const out = !conditions.hasGenerationAccess
  const warning = usage >= 80
  const accentClass = out
    ? "text-danger"
    : warning
      ? "text-caution-soft"
      : "text-zinc-200"
  const meterClass = out ? "bg-danger" : warning ? "bg-caution" : "bg-zinc-500"

  return (
    <button
      className="block w-full rounded-[11px] bg-white/[0.05] p-3 text-start"
      data-testid="plan-card"
      onClick={onOpenSubscription}
    >
      <span className="flex items-center justify-between">
        <span
          className={`text-xs ${out ? "font-bold text-danger" : "font-medium text-ink-muted"}`}
        >
          {out ? t("subscription.outOfCredits") : t("subscription.freePlan")}
        </span>
        <span className={`text-[13px] font-semibold ${accentClass}`}>
          {pctLabel(usage)}
        </span>
      </span>
      <ProgressBar
        colorClass={meterClass}
        heightClass="h-1"
        percent={usage}
        trackClass="mt-1.5 bg-white/[0.08]"
      />
      <span className="mt-2 block text-xs leading-[1.45] text-ink-muted">
        {out
          ? t("subscription.pausedUntilReset")
          : warning
            ? t("subscription.mostCreditsUsed")
            : t("subscription.resetsInDays", {
                count: presentation.daysLeft ?? 0,
              })}
      </span>
      <span className={PLAN_ACTION_BUTTON_CLASS}>
        <SparklesIcon className="me-1.5 inline-block align-[-2px]" size={13} />
        {t("common.upgrade")}
        <SparklesIcon className="ms-1.5 inline-block align-[-2px]" size={13} />
      </span>
    </button>
  )
}

interface OutOfCreditsCardProps {
  actionLabel?: string
  note?: string
  onOpenSubscription: () => void
  showUsage?: boolean
  title: string
  usage: number
}

const OutOfCreditsCard = ({
  actionLabel,
  note,
  onOpenSubscription,
  showUsage = true,
  title,
  usage,
}: OutOfCreditsCardProps) => {
  const { t } = useTranslation()

  return (
    <section
      className="rounded-[11px] bg-white/[0.05] p-3"
      data-testid="plan-card"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-danger">{title}</span>
        {showUsage && (
          <span className="text-[12.5px] font-bold text-danger">
            {pctLabel(usage)}
          </span>
        )}
      </div>
      {showUsage && (
        <ProgressBar
          colorClass="bg-danger"
          heightClass="h-1"
          percent={usage}
          trackClass="mt-2.5 bg-white/[0.08]"
        />
      )}
      {note !== undefined && (
        <p className="mt-2 text-xs leading-[1.45] text-ink-muted">{note}</p>
      )}
      <button className={PLAN_ACTION_BUTTON_CLASS} onClick={onOpenSubscription}>
        {actionLabel ?? (
          <>
            <SparklesIcon
              className="me-1.5 inline-block align-[-2px]"
              size={13}
            />
            {t("common.upgrade")}
            <SparklesIcon
              className="ms-1.5 inline-block align-[-2px]"
              size={13}
            />
          </>
        )}
      </button>
    </section>
  )
}

// The free plan's card: today's notes against the daily limit, and the way to
// a paid plan as the loudest thing in the sidebar.
const FreePlanCard = ({ plan }: { plan: PlanInfo }) => {
  const { t } = useTranslation()
  const used = plan.dailyNotesUsed ?? 0
  const limit = plan.dailyNotesLimit ?? 0
  const out = used >= limit
  const low = !out && used >= limit * 0.8
  const resetTime = dailyResetTime()

  return (
    <section
      className="rounded-[11px] bg-white/[0.05] p-3"
      data-testid="plan-card"
    >
      <div className="flex items-center justify-between">
        <span className="text-[13px] font-semibold text-ink-muted">
          {t("subscription.freePlan")}
        </span>
        <span
          className={`text-[12.5px] font-bold tabular-nums ${out ? "text-danger" : low ? "text-caution-soft" : "text-ink"}`}
        >
          {t("subscription.free.notesToday", { used, limit })}
        </span>
      </div>
      <ProgressBar
        colorClass={out ? "bg-danger" : low ? "bg-caution" : "bg-mint"}
        heightClass="h-1"
        percent={limit > 0 ? Math.min(100, (used / limit) * 100) : 0}
        trackClass="mt-2.5 bg-white/[0.08]"
      />
      <p className="mt-2 text-xs leading-[1.45] text-ink-muted">
        {t("subscription.free.resetsAt", { time: resetTime })}
      </p>
      <button
        className={PLAN_ACTION_BUTTON_CLASS}
        onClick={() => openSiteLink(SITE_LINKS.upgrade)}
      >
        <SparklesIcon className="me-1.5 inline-block align-[-2px]" size={13} />
        {t("subscription.free.upgradeToPaid")}
        <SparklesIcon className="ms-1.5 inline-block align-[-2px]" size={13} />
      </button>
    </section>
  )
}
