import { Sparkles } from "lucide-react"

import { ProgressBar } from "@/components/ui/ProgressBar"
import { openSiteLink, SITE_LINKS } from "@/lib/siteLinks"
import type { AccountState } from "@/types/api"

import { getPlanPresentation, pctLabel } from "./planPresentation"

interface PlanCardProps {
  account: AccountState
  onOpenSubscription: () => void
}

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
        className="rounded-[10px] border border-white/[0.08] bg-white/[0.02] p-3"
        data-testid="plan-card"
      >
        <p className="text-xs font-semibold text-zinc-200">Signed out</p>
        <p className="mt-1 text-[10.5px] leading-[1.45] text-ink-muted">
          Generation is paused until you sign in.
        </p>
        <button
          className="mt-2.5 w-full rounded-md border border-white/10 bg-white/[0.06] px-2 py-2 text-xs font-semibold text-zinc-200 transition hover:bg-white/[0.09]"
          onClick={() => openSiteLink(SITE_LINKS.signIn)}
        >
          Sign In
        </button>
      </section>
    )
  }

  if (presentation.variant === "free-cta") {
    return (
      <section
        className="rounded-[10px] border border-mint/25 bg-mint/[0.065] p-3.5"
        data-testid="plan-card"
      >
        <p className="text-xs font-bold text-mint">
          You&apos;re on the free plan
        </p>
        <p className="mt-1 text-[10.5px] leading-[1.45] text-ink-muted">
          Unlock unlimited text, voice &amp; images.
        </p>
        <button
          className="mt-3 inline-flex w-full items-center justify-center gap-1.5 rounded-[10px] border border-mint/60 bg-gradient-to-b from-emerald-300 to-mint px-2 py-3 text-[12.5px] font-extrabold text-emerald-950 shadow-[inset_0_1px_rgba(255,255,255,0.34),0_10px_24px_-8px_rgba(31,212,125,0.6)] transition hover:brightness-105"
          onClick={() => openSiteLink(SITE_LINKS.startTrial)}
        >
          <Sparkles aria-hidden className="size-3.5" />
          Start Free Trial
        </button>
      </section>
    )
  }

  if (presentation.variant === "trial") {
    const notesPercent =
      presentation.notesLimit !== null && presentation.notesLimit > 0
        ? Math.min(
            100,
            ((presentation.notesUsed ?? 0) / presentation.notesLimit) * 100,
          )
        : 100
    const meterColor = presentation.warning ? "bg-amber" : "bg-mint"
    const statusColor = presentation.warning ? "text-amber" : "text-mint"

    return (
      <section
        className="rounded-[10px] border border-mint/20 bg-mint/[0.045] p-3"
        data-testid="plan-card"
      >
        <div className="flex items-center justify-between">
          <span className="text-[9.5px] font-bold tracking-[0.06em] text-mint uppercase">
            Free Trial
          </span>
          <span className={`text-[10.5px] font-semibold ${statusColor}`}>
            {presentation.daysLeft} days left
          </span>
        </div>
        <div className="mt-2.5 space-y-2.5">
          <Meter
            colorClass={meterColor}
            label="Notes"
            percent={notesPercent}
            value={`${presentation.notesUsed} of ${presentation.notesLimit}`}
          />
          <Meter
            colorClass={meterColor}
            label="Credits"
            percent={presentation.usagePercent ?? 100}
            value={`${pctLabel(presentation.usagePercent ?? 100)} used`}
          />
        </div>
        <button
          className="mt-3 w-full rounded-md bg-mint px-2 py-2 text-xs font-semibold text-emerald-950 transition hover:bg-emerald-300"
          onClick={() => openSiteLink(SITE_LINKS.upgrade)}
        >
          Upgrade Now
        </button>
      </section>
    )
  }

  const usage = presentation.usagePercent ?? 0
  const warning = presentation.warning || usage >= 80
  const colorClass = warning ? "bg-amber" : "bg-zinc-500"
  const textColor = warning ? "text-amber" : "text-zinc-300"

  if (presentation.variant === "paid") {
    return (
      <button
        className="block w-full px-0.5 py-1 text-left"
        data-testid="plan-card"
        onClick={onOpenSubscription}
      >
        <span className="flex items-center justify-between text-[11px]">
          <span className="text-ink-muted">{presentation.planName} plan</span>
          <span className={`font-medium ${textColor}`}>{pctLabel(usage)}</span>
        </span>
        <ProgressBar
          colorClass={colorClass}
          heightClass="h-[3px]"
          percent={usage}
          trackClass="mt-1.5 bg-white/[0.07]"
        />
        {presentation.warning && (
          <span className="mt-1.5 block text-[10px] text-amber">
            Generation is paused — review your plan.
          </span>
        )}
      </button>
    )
  }

  return (
    <button
      className={`block w-full rounded-[10px] border p-3 text-left ${
        warning
          ? "border-amber/25 bg-white/[0.02]"
          : "border-white/[0.08] bg-white/[0.02]"
      }`}
      data-testid="plan-card"
      onClick={onOpenSubscription}
    >
      <span className="flex items-center justify-between">
        <span className="text-[11px] font-medium text-ink-muted">
          Free plan
        </span>
        <span className={`text-xs font-semibold ${textColor}`}>
          {pctLabel(usage)}
        </span>
      </span>
      <ProgressBar
        colorClass={colorClass}
        percent={usage}
        trackClass="mt-1.5 bg-white/[0.08]"
      />
      <span className="mt-1.5 block text-[11px] text-ink-faint">
        Resets in {presentation.daysLeft ?? 0} days
      </span>
      <span className="mt-2.5 block rounded-md bg-mint px-2 py-2 text-center text-xs font-semibold text-emerald-950">
        Upgrade
      </span>
    </button>
  )
}

interface MeterProps {
  colorClass: string
  label: string
  percent: number
  value: string
}

const Meter = ({ colorClass, label, percent, value }: MeterProps) => (
  <div>
    <div className="mb-1 flex justify-between text-[10.5px] leading-none text-ink-muted">
      <span>{label}</span>
      <span className="font-medium text-zinc-300">{value}</span>
    </div>
    <ProgressBar
      colorClass={colorClass}
      heightClass="h-[3px]"
      percent={percent}
    />
  </div>
)
