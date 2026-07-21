import type { AccountState } from "@/types/api"

import { getPlanPresentation } from "./planPresentation"

interface PlanCardProps {
  account: AccountState
  onOpenSubscription: () => void
}

const TONE_CLASSES = {
  neutral: "bg-indigo",
  signedOut: "bg-mint",
  success: "bg-mint",
  warning: "bg-amber",
}

const CARD_CLASSES = {
  neutral: "border-white/[0.07] bg-white/[0.025]",
  signedOut: "border-mint/25 bg-mint/[0.06]",
  success: "border-white/[0.07] bg-white/[0.025]",
  warning: "border-white/[0.07] bg-white/[0.025]",
}

const TITLE_CLASSES = {
  neutral: "text-zinc-300",
  signedOut: "text-mint",
  success: "text-zinc-300",
  warning: "text-zinc-300",
}

const DETAIL_CLASSES = {
  neutral: "truncate text-ink-faint",
  signedOut: "text-zinc-200",
  success: "truncate text-ink-faint",
  warning: "truncate text-ink-faint",
}

const BUTTON_CLASSES = {
  neutral:
    "border border-white/10 bg-white/[0.04] text-zinc-200 hover:bg-white/[0.07]",
  signedOut: "bg-mint text-emerald-950 hover:bg-emerald-300",
  success: "bg-mint text-emerald-950 hover:bg-emerald-300",
  warning:
    "border border-white/10 bg-white/[0.04] text-zinc-200 hover:bg-white/[0.07]",
}

export const PlanCard = ({ account, onOpenSubscription }: PlanCardProps) => {
  const presentation = getPlanPresentation(account)

  return (
    <section
      className={`rounded-lg border p-3 ${CARD_CLASSES[presentation.tone]}`}
      data-testid="plan-card"
    >
      <div className="flex items-center justify-between gap-3">
        <span
          className={`text-[11px] font-semibold ${TITLE_CLASSES[presentation.tone]}`}
        >
          {presentation.title}
        </span>
        {presentation.usagePercent !== null && (
          <span className="text-[11px] font-semibold text-zinc-200">
            {presentation.usagePercent}%
          </span>
        )}
      </div>

      {presentation.usagePercent !== null && (
        <div className="mt-2 h-1 overflow-hidden rounded-sm bg-white/[0.07]">
          <div
            className={`h-full rounded-sm ${TONE_CLASSES[presentation.tone]}`}
            style={{ width: `${presentation.usagePercent}%` }}
          />
        </div>
      )}

      {presentation.detail && (
        <p
          className={`mt-2 text-[10px] leading-4 ${DETAIL_CLASSES[presentation.tone]}`}
        >
          {presentation.detail}
        </p>
      )}

      <button
        className={`mt-3 w-full rounded-md px-3 py-2 text-xs font-semibold transition ${BUTTON_CLASSES[presentation.tone]}`}
        onClick={onOpenSubscription}
      >
        {presentation.actionLabel}
      </button>
    </section>
  )
}
