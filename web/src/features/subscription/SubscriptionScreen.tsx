/*
 * Copyright (C) 2024 Michael Piazza
 *
 * This file is part of Smart Notes.
 *
 * Smart Notes is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Smart Notes is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Smart Notes. If not, see <https://www.gnu.org/licenses/>.
 */

import { AlertTriangle, CreditCard, LogOut } from "lucide-react"
import { useState } from "react"

import {
  getCreditSegments,
  getCreditUsagePercent,
  pctLabel,
} from "@/components/shared/planPresentation"
import { openSiteLink, SITE_LINKS } from "@/lib/siteLinks"
import { logout } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AccountState } from "@/types/api"

export const SubscriptionScreen = () => {
  const state = useAppStore((store) => store.state)
  if (state === null) return <SubscriptionSkeleton />

  return <LoadedSubscriptionScreen account={state.account} />
}

interface LoadedSubscriptionScreenProps {
  account: AccountState
}

const LoadedSubscriptionScreen = ({
  account,
}: LoadedSubscriptionScreenProps) => {
  const [logoutError, setLogoutError] = useState<string | null>(null)
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const email = (account as AccountState & { email?: string | null }).email
  const isSignedOut = account.subscription === "UNAUTHENTICATED"
  const isPaid = account.subscription.startsWith("PAID_PLAN")

  const runLogout = async () => {
    setLogoutError(null)
    setIsLoggingOut(true)
    try {
      await logout()
    } catch (error) {
      setLogoutError(
        error instanceof Error ? error.message : "Could not log out",
      )
    } finally {
      setIsLoggingOut(false)
    }
  }

  return (
    <section
      className="flex min-h-0 flex-1 flex-col"
      data-testid="subscription-screen"
    >
      <header className="flex shrink-0 items-center justify-between gap-6 border-b border-white/[0.065] px-6 py-5">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <CreditCard aria-hidden className="size-5 text-indigo-soft" />
            <h1 className="text-[21px] leading-tight font-bold tracking-[-0.025em] text-zinc-100">
              Subscription
            </h1>
          </div>
          {email != null && (
            <p className="mt-1.5 truncate text-xs text-ink-muted">{email}</p>
          )}
        </div>
        {!isSignedOut && (
          <button
            className="inline-flex items-center gap-1.5 rounded-md border border-white/[0.08] bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-zinc-400 transition hover:bg-white/[0.07] hover:text-zinc-200"
            disabled={isLoggingOut}
            onClick={() => void runLogout()}
          >
            <LogOut aria-hidden className="size-3.5" />
            {isLoggingOut ? "Logging out…" : "Log out"}
          </button>
        )}
      </header>

      {logoutError !== null && (
        <p className="mx-6 mt-3 rounded-lg border border-red-300/15 bg-red-300/[0.06] px-3 py-2 text-xs text-danger">
          {logoutError}
        </p>
      )}

      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
        {isSignedOut ? (
          <SignedOutSubscription />
        ) : isPaid ? (
          <PaidSubscription account={account} />
        ) : (
          <FreeSubscription account={account} />
        )}
      </div>
    </section>
  )
}

const SignedOutSubscription = () => (
  <div className="flex min-h-full items-center justify-center p-6 text-center">
    <div>
      <h2 className="text-[19px] font-bold text-zinc-100">
        Sign in to manage your plan
      </h2>
      <p className="mt-1.5 text-xs text-ink-muted">
        Your smart fields and settings are stored on this device.
      </p>
      <button
        className="mt-4 rounded-md border border-white/10 bg-white/[0.07] px-5 py-2 text-xs font-semibold text-zinc-200 hover:bg-white/10"
        onClick={() => openSiteLink(SITE_LINKS.signIn)}
      >
        Sign In
      </button>
    </div>
  </div>
)

const FreeSubscription = ({ account }: { account: AccountState }) => {
  const plan = account.plan
  const usage = getCreditUsagePercent(plan)
  const warning = usage >= 80
  const isTrial = plan?.notesLimit !== null && plan?.notesLimit !== undefined

  return (
    <div className="max-w-[760px]">
      <div className="rounded-xl border border-indigo/30 bg-indigo/10 p-5">
        <div className="flex items-center justify-between gap-5">
          <div className="min-w-0 flex-1">
            <span className="inline-block rounded border border-amber/25 bg-amber/10 px-2.5 py-1 text-[10px] font-bold tracking-wide text-amber uppercase">
              You&apos;re on the Free plan
            </span>
            <h2 className="mt-2.5 text-xl font-bold tracking-[-0.02em] text-white">
              Upgrade — your whole collection, automatically
            </h2>
            <p className="mt-1.5 text-xs leading-5 text-indigo-soft">
              Bigger monthly allowance · all models &amp; voices · images ·
              batch · cancel anytime
            </p>
          </div>
          <div className="shrink-0 text-center">
            <button
              className="rounded-lg bg-mint px-6 py-3 text-[15px] font-semibold text-emerald-950 hover:bg-emerald-300"
              onClick={() => openSiteLink(SITE_LINKS.upgrade)}
            >
              Upgrade now →
            </button>
            <p className="mt-1.5 text-[11px] text-ink-muted">from $5/mo</p>
          </div>
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xs font-semibold tracking-wide text-zinc-200 uppercase">
            Credits this month
          </h2>
          <p className="text-[11px] text-ink-muted">
            Resets in{" "}
            <span className="text-zinc-200">{plan?.daysLeft ?? 0} days</span>
          </p>
        </div>
        <div className="mt-3 flex items-end gap-2.5">
          <span
            className={`text-[34px] leading-none font-bold tracking-[-0.03em] ${
              warning ? "text-amber" : "text-zinc-200"
            }`}
          >
            {pctLabel(usage)}
          </span>
          <span className="pb-0.5 text-[13px] text-ink-muted">
            of monthly credits used
          </span>
        </div>
        <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-white/[0.06]">
          <div
            className={`h-full rounded-full ${warning ? "bg-amber" : "bg-zinc-500"}`}
            style={{ width: `${usage}%` }}
          />
        </div>
        {warning && (
          <p className="mt-2 flex items-center gap-1.5 text-[11px] text-amber">
            <AlertTriangle aria-hidden className="size-3" />
            Almost out — generation pauses until your credits reset. Upgrade for
            a bigger allowance.
          </p>
        )}
      </div>

      <div className="mt-4 overflow-hidden rounded-xl border border-white/[0.08] bg-white/[0.02]">
        <PlanFact label="Plan" value={isTrial ? "Free Trial" : "Free"} />
        <PlanFact
          label="Credits reset"
          value={`In ${plan?.daysLeft ?? 0} days`}
        />
        {isTrial && plan?.notesLimit !== null ? (
          <PlanFact
            label="Notes used"
            last
            value={`${plan?.notesUsed ?? 0} of ${plan.notesLimit}`}
          />
        ) : (
          <PlanFact label="Notes used" last value="Unlimited" />
        )}
      </div>
    </div>
  )
}

const PaidSubscription = ({ account }: { account: AccountState }) => {
  const plan = account.plan
  if (plan === null) return <SignedOutSubscription />
  const usage = getCreditUsagePercent(plan)
  const segments = getCreditSegments(plan)

  return (
    <div className="max-w-[760px]">
      <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-[10px] font-semibold tracking-wide text-ink-faint uppercase">
              Your plan
            </p>
            <h2 className="mt-1 text-[15px] font-semibold text-zinc-100">
              {plan.planName}
            </h2>
          </div>
          <a
            className="text-[11.5px] text-indigo-soft hover:underline"
            href={SITE_LINKS.account}
            rel="noreferrer"
            target="_blank"
          >
            Manage or cancel
          </a>
        </div>
        <div className="mt-4 flex items-baseline justify-between">
          <span className="text-xs text-zinc-400">Monthly credits</span>
          <span className="text-[13px] font-semibold text-zinc-200">
            {pctLabel(usage)} used
          </span>
        </div>
        <div className="mt-2 flex h-1.5 overflow-hidden rounded-full bg-white/[0.07]">
          {segments.map((segment) => (
            <div
              key={segment.key}
              style={{
                backgroundColor: segment.color,
                width: `${segment.percent}%`,
              }}
            />
          ))}
        </div>
        <div className="mt-2.5 flex gap-4">
          {segments.map((segment) => (
            <span
              className="inline-flex items-center gap-1.5 text-[11.5px] text-ink-muted"
              key={segment.key}
            >
              <span
                className="size-[7px] rounded-sm"
                style={{ backgroundColor: segment.color }}
              />
              {segment.label} {pctLabel(segment.percent)}
            </span>
          ))}
        </div>
        <div className="mt-3 flex justify-between border-t border-white/[0.06] pt-3 text-[11.5px] text-ink-muted">
          <span>Resets in {plan.daysLeft} days</span>
          <span>Notes · unlimited</span>
        </div>
      </div>

      <div className="mt-4 overflow-hidden rounded-xl border border-white/[0.08] bg-white/[0.02]">
        <PlanFact label="Plan" value={plan.planName} />
        <PlanFact label="Credits reset" value={`In ${plan.daysLeft} days`} />
        <PlanFact label="Notes used" last value="Unlimited" />
      </div>
    </div>
  )
}

const PlanFact = ({
  label,
  last = false,
  value,
}: {
  label: string
  last?: boolean
  value: string
}) => (
  <div
    className={`flex justify-between px-4 py-3 text-xs ${
      last ? "" : "border-b border-white/[0.05]"
    }`}
  >
    <span className="text-ink-muted">{label}</span>
    <span className="font-medium text-zinc-200">{value}</span>
  </div>
)

const SubscriptionSkeleton = () => (
  <section
    aria-label="Loading Subscription"
    className="flex min-h-0 flex-1 animate-pulse flex-col"
  >
    <div className="h-[86px] border-b border-white/[0.065] px-6 py-5">
      <div className="h-5 w-44 rounded bg-white/[0.06]" />
    </div>
    <div className="p-6">
      <div className="h-40 max-w-[760px] rounded-xl bg-white/[0.025]" />
    </div>
  </section>
)
