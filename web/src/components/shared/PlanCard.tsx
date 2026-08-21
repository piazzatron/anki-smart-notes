import { ProgressBar } from "@/components/ui/ProgressBar"
import { openSiteLink, SITE_LINKS } from "@/lib/siteLinks"
import type { AccountState } from "@/types/api"

import {
  getPlanConditions,
  getPlanPresentation,
  pctLabel,
} from "./planPresentation"

interface PlanCardProps {
  account: AccountState
  onOpenSubscription: () => void
}

const PLAN_ACTION_BUTTON_CLASS =
  "mt-3 block w-full rounded-lg border border-[#1fd47d]/60 bg-gradient-to-b from-[#4cf0a8] to-[#1fd47d] px-2 py-2.5 text-center text-xs font-extrabold text-[#06281a] shadow-[inset_0_1px_rgba(255,255,255,0.34),0_10px_22px_-8px_rgba(31,212,125,0.55)] transition hover:brightness-105"
const TRIAL_ACTION_BUTTON_CLASS =
  "mt-3 block w-full rounded-lg border border-indigo/40 bg-indigo/80 px-2 py-2.5 text-center text-xs font-extrabold text-white shadow-[inset_0_1px_rgba(255,255,255,0.24),0_10px_22px_-8px_rgba(124,141,255,0.42)] transition hover:bg-indigo/90"

export const PlanCard = ({ account, onOpenSubscription }: PlanCardProps) => {
  const presentation = getPlanPresentation(account)

  if (presentation.variant === "loading") {
    return (
      <div
        aria-label="Checking subscription"
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
            className="size-1.5 rounded-full bg-amber shadow-[0_0_8px_rgba(255,210,122,0.65)]"
          />
          <p className="text-sm font-bold tracking-[-0.1px] text-zinc-100">
            Signed out
          </p>
        </div>
        <p className="mt-1.5 text-[10.5px] leading-[1.45] text-zinc-400">
          Generation is paused until you sign in.
        </p>
        <button
          className={PLAN_ACTION_BUTTON_CLASS}
          onClick={() => openSiteLink(SITE_LINKS.signIn)}
        >
          Sign In
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
        ? "Out of credits"
        : conditions.noteLimitReached
          ? "Trial note limit reached"
          : "Trial ended"
      return (
        <OutOfCreditsCard
          note="Upgrade to keep generating."
          onOpenSubscription={onOpenSubscription}
          title={title}
          usage={usage}
        />
      )
    }

    const daysLeft = presentation.daysLeft ?? 0
    const ending = daysLeft <= 2
    const accentClass = ending ? "text-amber" : "text-[#7df0c0]"
    const meterClass = ending ? "bg-amber" : "bg-[#7df0c0]"

    return (
      <section
        className="rounded-[11px] bg-white/[0.05] p-3"
        data-testid="plan-card"
      >
        <div className="flex items-center justify-between">
          <span className="text-[9.5px] font-bold tracking-[0.06em] text-ink-muted uppercase">
            Free Trial
          </span>
          <span className={`text-[11.5px] font-bold ${accentClass}`}>
            {daysLeft === 1 ? "Last day" : `${daysLeft} days left`}
          </span>
        </div>
        <ProgressBar
          colorClass={meterClass}
          heightClass="h-1"
          percent={Math.min(100, (daysLeft / 7) * 100)}
          trackClass="mt-2.5 bg-white/[0.08]"
        />
        <button
          className={TRIAL_ACTION_BUTTON_CLASS}
          onClick={onOpenSubscription}
        >
          Upgrade
        </button>
      </section>
    )
  }

  if (presentation.variant === "paid") {
    if (!conditions.hasGenerationAccess) {
      return (
        <OutOfCreditsCard
          note="Generation is paused until your credits reset."
          onOpenSubscription={onOpenSubscription}
          title={
            conditions.creditLimitReached
              ? "Out of credits"
              : conditions.noteLimitReached
                ? "Note limit reached"
                : "Plan inactive"
          }
          usage={usage}
        />
      )
    }

    return (
      <button
        className="block w-full px-0.5 py-1 text-left"
        data-testid="plan-card"
        onClick={onOpenSubscription}
      >
        <span className="flex items-center justify-between text-[11px]">
          <span className="text-ink-muted">Usage</span>
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
    ? "text-[#ff7a7a]"
    : warning
      ? "text-amber"
      : "text-zinc-200"
  const meterClass = out ? "bg-[#ff7a7a]" : warning ? "bg-amber" : "bg-zinc-500"

  return (
    <button
      className="block w-full rounded-[11px] bg-white/[0.05] p-3 text-left"
      data-testid="plan-card"
      onClick={onOpenSubscription}
    >
      <span className="flex items-center justify-between">
        <span
          className={`text-[11px] ${out ? "font-bold text-[#ff7a7a]" : "font-medium text-ink-muted"}`}
        >
          {out ? "Out of credits" : "Free plan"}
        </span>
        <span className={`text-xs font-semibold ${accentClass}`}>
          {pctLabel(usage)}
        </span>
      </span>
      <ProgressBar
        colorClass={meterClass}
        heightClass="h-1"
        percent={usage}
        trackClass="mt-1.5 bg-white/[0.08]"
      />
      <span className="mt-2 block text-[10.5px] leading-[1.45] text-ink-muted">
        {out
          ? "Generation is paused until your credits reset."
          : warning
            ? "Most of this month's credits are used"
            : `Resets in ${presentation.daysLeft ?? 0} days`}
      </span>
      <span className={PLAN_ACTION_BUTTON_CLASS}>✨ Upgrade ✨</span>
    </button>
  )
}

interface OutOfCreditsCardProps {
  note: string
  onOpenSubscription: () => void
  title?: string
  usage: number
}

const OutOfCreditsCard = ({
  note,
  onOpenSubscription,
  title = "Out of credits",
  usage,
}: OutOfCreditsCardProps) => (
  <section
    className="rounded-[11px] bg-white/[0.05] p-3"
    data-testid="plan-card"
  >
    <div className="flex items-center justify-between">
      <span className="text-[11px] font-bold text-[#ff7a7a]">{title}</span>
      <span className="text-[11.5px] font-bold text-[#ff7a7a]">
        {pctLabel(usage)}
      </span>
    </div>
    <ProgressBar
      colorClass="bg-[#ff7a7a]"
      heightClass="h-1"
      percent={usage}
      trackClass="mt-2.5 bg-white/[0.08]"
    />
    <p className="mt-2 text-[10.5px] leading-[1.45] text-ink-muted">{note}</p>
    <button className={PLAN_ACTION_BUTTON_CLASS} onClick={onOpenSubscription}>
      ✨ Upgrade ✨
    </button>
  </section>
)
