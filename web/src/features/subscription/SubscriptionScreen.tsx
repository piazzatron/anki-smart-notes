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

import { useEffect, useState } from "react"

import { PageTitle } from "@/components/shared/PageTitle"
import {
  getCreditSegments,
  getCreditUsagePercent,
  getPlanConditions,
  getPlanPresentation,
  pctLabel,
} from "@/components/shared/planPresentation"
import { ScreenSkeleton } from "@/components/shared/ScreenSkeleton"
import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { errorMessage } from "@/lib/errors"
import { openSiteLink, SITE_LINKS } from "@/lib/siteLinks"
import { logout, refreshAccount } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AccountState, PlanInfo } from "@/types/api"

const CARD_CLASS = "rounded-[13px] bg-white/[0.05]"
type AuthenticatedAccount = Extract<AccountState, { status: "AUTHENTICATED" }>

export const SubscriptionScreen = () => {
  const state = useAppStore((store) => store.state)

  useEffect(() => {
    void refreshAccount()
  }, [])

  if (state === null) {
    return (
      <ScreenSkeleton
        ariaLabel="Loading Subscription"
        contentClassName="h-40"
        showSubtitle={false}
      />
    )
  }

  return <LoadedSubscriptionScreen account={state.account} />
}

const LoadedSubscriptionScreen = ({ account }: { account: AccountState }) => {
  const [logoutError, setLogoutError] = useState<string | null>(null)
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const presentation = getPlanPresentation(account)
  const isSignedOut = presentation.variant === "signed-out"

  const runLogout = async () => {
    setLogoutError(null)
    setIsLoggingOut(true)
    try {
      await logout()
    } catch (error) {
      setLogoutError(errorMessage(error, "Could not log out"))
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
          <PageTitle>Account and Usage</PageTitle>
          {!isSignedOut && account.email !== null && (
            <p className="mt-1.5 truncate text-xs text-ink-muted">
              {account.email}
            </p>
          )}
        </div>
        {!isSignedOut && (
          <button
            className="rounded-md border border-white/[0.08] bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-zinc-400 transition hover:bg-white/[0.07] hover:text-zinc-200"
            disabled={isLoggingOut}
            onClick={() => void runLogout()}
            type="button"
          >
            {isLoggingOut ? "Logging out…" : "Log out"}
          </button>
        )}
      </header>

      {logoutError !== null && (
        <ErrorBanner
          className="mx-6 mt-3"
          message={logoutError}
          onDismiss={() => setLogoutError(null)}
        />
      )}

      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
        {presentation.variant === "loading" ? (
          <div
            aria-label="Checking subscription"
            className="animate-pulse space-y-2.5"
          >
            <div className="h-28 rounded-[13px] bg-white/[0.04]" />
            <div className="h-40 rounded-[13px] bg-white/[0.04]" />
          </div>
        ) : isSignedOut ? (
          <SignedOutSubscription />
        ) : (
          <SubscriptionDetails account={account} />
        )}
      </div>
    </section>
  )
}

const SubscriptionDetails = ({ account }: { account: AccountState }) => {
  if (account.status !== "AUTHENTICATED") return null

  const presentation = getPlanPresentation(account)
  const plan = account.plan
  const usage = getCreditUsagePercent(plan)
  const isTrial = presentation.variant === "trial"
  const isFree = presentation.variant === "free-usage"
  const isPaid = presentation.variant === "paid"
  const hero = getHeroContent(account)

  return (
    <div className="w-full space-y-2.5">
      {hero !== null && <PlanHero {...hero} />}
      <UsageModule
        daysLeft={plan.daysLeft}
        period={isTrial ? "trial" : "month"}
        plan={plan}
        usage={usage}
      />
      <PlanFacts facts={getPlanFacts({ isFree, isPaid, isTrial, plan })} />
      {isPaid && <ManageRow topTier={isTopTier(plan)} />}
    </div>
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
        className="mt-4 rounded-lg bg-white/[0.09] px-5 py-2.5 text-xs font-bold text-zinc-200 transition hover:bg-white/[0.12]"
        onClick={() => openSiteLink(SITE_LINKS.signIn)}
        type="button"
      >
        Sign In
      </button>
    </div>
  </div>
)

interface HeroContent {
  context: string
  cta: string
  note?: string
  tone: "indigo" | "mint"
  url: string
}

const getHeroContent = (account: AuthenticatedAccount): HeroContent | null => {
  const presentation = getPlanPresentation(account)
  const conditions = getPlanConditions(account.plan)

  if (presentation.variant === "free-usage") {
    return {
      context: conditions.creditLimitReached
        ? "You're out of free credits this month"
        : conditions.noteLimitReached
          ? "You've reached your note limit"
          : conditions.expired
            ? "Your free credits are resetting"
            : "You're on the Free plan",
      cta: "Upgrade — your whole collection, automatically",
      tone: "indigo",
      url: SITE_LINKS.upgrade,
    }
  }

  if (presentation.variant === "trial") {
    const daysLeft = presentation.daysLeft ?? 0
    return {
      context: conditions.creditLimitReached
        ? "You're out of trial credits"
        : conditions.noteLimitReached
          ? "You've reached your trial note limit"
          : conditions.expired
            ? "Your trial has ended"
            : daysLeft === 1
              ? "Your trial ends today"
              : `${daysLeft} days left in your trial`,
      cta: "✨ Upgrade to paid",
      tone: "mint",
      url: SITE_LINKS.upgrade,
    }
  }

  if (presentation.variant !== "paid" || conditions.hasGenerationAccess) {
    return null
  }

  if (conditions.expired) {
    return {
      context: "Your plan has expired",
      cta: "Manage your plan",
      tone: "mint",
      url: SITE_LINKS.account,
    }
  }

  const topTier = isTopTier(account.plan)
  return {
    context: conditions.noteLimitReached
      ? "You've reached your note limit"
      : "You're out of credits this month",
    cta: topTier ? "Buy more credits" : "Upgrade for more credits",
    ...(topTier
      ? {
          note: "Pay-as-you-go credits roll over every month — yours forever.",
        }
      : {}),
    tone: "mint",
    url: topTier ? SITE_LINKS.topUp : SITE_LINKS.upgrade,
  }
}

const HERO_STYLES = {
  indigo: {
    background: "linear-gradient(180deg, #7c8dff, #5b6fe8)",
    borderColor: "rgba(124,141,255,0.6)",
    boxShadow:
      "inset 0 1px 0 rgba(255,255,255,0.28), 0 8px 18px -14px rgba(91,111,232,0.35)",
    ink: "#fff",
    sub: "rgba(255,255,255,0.85)",
  },
  mint: {
    background: "linear-gradient(180deg, #4cf0a8, #1fd47d)",
    borderColor: "rgba(31,212,125,0.6)",
    boxShadow:
      "inset 0 1px 0 rgba(255,255,255,0.36), 0 8px 18px -14px rgba(31,212,125,0.35)",
    ink: "#06281a",
    sub: "rgba(6,40,26,0.72)",
  },
} as const

const PlanHero = ({ context, cta, note, tone, url }: HeroContent) => {
  const styles = HERO_STYLES[tone]

  return (
    <button
      className="flex w-full cursor-pointer flex-col items-center justify-center rounded-[14px] border px-[22px] pt-[22px] pb-6 text-center transition-[filter,transform] duration-150 ease-out hover:scale-[1.006] hover:brightness-105"
      onClick={() => openSiteLink(url)}
      style={{
        background: styles.background,
        borderColor: styles.borderColor,
        boxShadow: styles.boxShadow,
      }}
      type="button"
    >
      <span className="text-[15px] font-semibold" style={{ color: styles.sub }}>
        {context}
      </span>
      <span
        className="mt-1 text-[23px] font-extrabold tracking-[-0.4px]"
        style={{ color: styles.ink }}
      >
        {cta} <span className="font-bold">→</span>
      </span>
      {note !== undefined && (
        <span
          className="mt-2 text-xs font-medium"
          style={{ color: styles.sub }}
        >
          {note}
        </span>
      )}
    </button>
  )
}

const UsageModule = ({
  daysLeft,
  period,
  plan,
  usage,
}: {
  daysLeft: number
  period: "month" | "trial"
  plan: PlanInfo
  usage: number
}) => {
  const segments = getCreditSegments(plan).filter(
    (segment) => segment.percent > 0,
  )
  const warning = usage >= 80

  return (
    <section className={`${CARD_CLASS} p-[18px]`}>
      <div className="flex items-baseline justify-between">
        <h2 className="text-xs font-semibold tracking-[0.4px] text-zinc-200 uppercase">
          Credit Usage
        </h2>
        <p className="text-[11px] text-ink-muted">
          Resets in <span className="text-zinc-200">{daysLeft} days</span>
        </p>
      </div>
      <div className="mt-3.5 flex items-end gap-2.5">
        <span
          className={`text-[34px] leading-none font-bold tracking-[-1px] ${warning ? "text-amber" : "text-zinc-200"}`}
        >
          {pctLabel(usage)}
        </span>
        <span className="pb-[3px] text-[13px] text-ink-muted">
          of {period === "trial" ? "trial" : "monthly"} credits used
        </span>
      </div>
      <div className="mt-3 flex h-2.5 overflow-hidden rounded-full bg-white/[0.06]">
        {segments.map((segment) => (
          <span
            key={segment.key}
            style={{
              backgroundColor: segment.color,
              width: `${segment.percent}%`,
            }}
          />
        ))}
      </div>
      <div className="mt-[11px] flex gap-4">
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
    </section>
  )
}

const getPlanFacts = ({
  isFree,
  isPaid,
  isTrial,
  plan,
}: {
  isFree: boolean
  isPaid: boolean
  isTrial: boolean
  plan: PlanInfo | null
}): Array<[string, string]> => {
  if (isTrial) {
    const daysLeft = plan?.daysLeft ?? 0
    return [
      ["Plan", "Free trial"],
      ["Trial ends", daysLeft === 1 ? "Today" : `In ${daysLeft} days`],
      ["Notes", `${plan?.notesUsed ?? 0}/${plan?.notesLimit ?? 50} used`],
    ]
  }

  if (isPaid && plan !== null) {
    return [
      ["Plan", plan.planName],
      ["Credits reset", `In ${plan.daysLeft} days`],
      ["Notes used", "Unlimited"],
    ]
  }

  return [
    ["Plan", isFree ? "Free" : (plan?.planName ?? "Free")],
    ["Credits reset", `In ${plan?.daysLeft ?? 0} days`],
    ["Notes used", "Unlimited"],
  ]
}

const PlanFacts = ({ facts }: { facts: Array<[string, string]> }) => (
  <div
    className="grid gap-2.5"
    style={{ gridTemplateColumns: `repeat(${facts.length}, minmax(0, 1fr))` }}
  >
    {facts.map(([label, value]) => (
      <div className={`${CARD_CLASS} px-4 py-[13px]`} key={label}>
        <p className="text-[11px] text-ink-muted">{label}</p>
        <p className="mt-[3px] truncate text-sm font-bold text-zinc-100">
          {value}
        </p>
      </div>
    ))}
  </div>
)

const ManageRow = ({ topTier }: { topTier: boolean }) => (
  <button
    className={`${CARD_CLASS} flex w-full items-center justify-between gap-4 px-[18px] py-[15px] text-left transition hover:bg-white/[0.07]`}
    onClick={() => openSiteLink(SITE_LINKS.account)}
    type="button"
  >
    <span className="min-w-0">
      <span className="block text-[13.5px] font-bold text-zinc-100">
        {topTier ? "Manage plan" : "Manage or upgrade plan"}
      </span>
      <span className="mt-[3px] block text-[11.5px] text-ink-muted">
        Change plan, update payment, or cancel.
      </span>
    </span>
    <span className="shrink-0 text-[17px] text-ink-muted">→</span>
  </button>
)

const isTopTier = (plan: PlanInfo): boolean => plan.planType === "large"
