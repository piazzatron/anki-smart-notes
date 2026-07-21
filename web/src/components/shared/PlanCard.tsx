import type { AccountState } from "@/types/api"

import { getPlanPresentation } from "./planPresentation"

interface PlanCardProps {
  account: AccountState
  onOpenSubscription: () => void
}

const TONE_CLASSES = {
  neutral: "bg-indigo",
  success: "bg-mint",
  warning: "bg-amber",
}

export const PlanCard = ({ account, onOpenSubscription }: PlanCardProps) => {
  const presentation = getPlanPresentation(account)
  const isSignedOut = account.subscription === "UNAUTHENTICATED"

  return (
    <section
      className={`rounded-lg border p-3 ${
        isSignedOut
          ? "border-mint/25 bg-mint/[0.06]"
          : "border-white/[0.07] bg-white/[0.025]"
      }`}
      data-testid="plan-card"
    >
      <div className="flex items-center justify-between gap-3">
        <span
          className={`text-[11px] font-semibold ${isSignedOut ? "text-mint" : "text-zinc-300"}`}
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
          className={`mt-2 text-[10px] leading-4 ${isSignedOut ? "text-zinc-200" : "truncate text-ink-faint"}`}
        >
          {presentation.detail}
        </p>
      )}

      <button
        className={`mt-3 w-full rounded-md px-3 py-2 text-xs font-semibold transition ${
          presentation.tone === "success" || isSignedOut
            ? "bg-mint text-emerald-950 hover:bg-emerald-300"
            : "border border-white/10 bg-white/[0.04] text-zinc-200 hover:bg-white/[0.07]"
        }`}
        onClick={onOpenSubscription}
      >
        {presentation.actionLabel}
      </button>
    </section>
  )
}
