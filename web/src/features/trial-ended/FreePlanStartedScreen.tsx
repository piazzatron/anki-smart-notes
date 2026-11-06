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

import { ArrowRight, Check } from "lucide-react"
import type { ComponentType, CSSProperties } from "react"
import { useTranslation } from "react-i18next"

import {
  BoltIcon,
  CardIcon,
  CogIcon,
  GalleryIcon,
  SearchIcon,
  SparklesIcon,
  VolumeIcon,
  type IconProps,
} from "@/components/shared/Icons"
import { SparkleField, type Sparkle } from "@/components/shared/SparkleField"
import { GlowButton } from "@/components/ui/GlowButton"
import { ReviewOffer } from "@/features/review-offer/ReviewOffer"
import { openSiteLink, SITE_LINKS } from "@/lib/siteLinks"
import type { FreePlanReason } from "@/types/api"

import type { FreePlanImpact } from "./freePlanImpact"

interface FreePlanStartedScreenProps {
  dailyNotesLimit: number
  /** What Free changes about the user's own fields, shown on the rows it affects. */
  impact: FreePlanImpact
  onContinue: () => void
  reason: FreePlanReason
}

interface Loss {
  icon: ComponentType<IconProps>
  key: string
  free: string
  /** How many of the user's own fields this changes, when any. */
  yours?: string
}

// Framing the content, never behind it: a crown around the title, loose pairs
// down both margins, and a few low around the call to action.
const SPARKLES: readonly Sparkle[] = [
  { delay: "-1.7s", duration: "15s", size: "11px", left: "18%", top: "6%" },
  { delay: "-0.6s", duration: "18s", size: "14px", left: "24%", top: "13%" },
  { delay: "-2.9s", duration: "13s", size: "17px", left: "77%", top: "5%" },
  { delay: "-1.3s", duration: "16s", size: "11px", left: "83%", top: "12%" },
  { delay: "-0.3s", duration: "17s", size: "13px", left: "6%", top: "30%" },
  { delay: "-2.4s", duration: "19s", size: "10px", left: "11%", top: "47%" },
  { delay: "-3.2s", duration: "16s", size: "15px", left: "4%", top: "63%" },
  { delay: "-0.8s", duration: "13s", size: "12px", left: "93%", top: "26%" },
  { delay: "-1.9s", duration: "18s", size: "10px", left: "88%", top: "42%" },
  { delay: "-3.6s", duration: "15s", size: "14px", left: "95%", top: "58%" },
  { delay: "-0.5s", duration: "20s", size: "13px", left: "27%", top: "84%" },
  { delay: "-2.1s", duration: "17s", size: "16px", left: "72%", top: "80%" },
  { delay: "-1.5s", duration: "16s", size: "11px", left: "78%", top: "91%" },
] as const

// Feature, the user's column, the arrow and Free's column, shared by the
// column labels and the rows.
const COMPARISON_GRID =
  "grid grid-cols-[minmax(0,1fr)_96px_40px_236px] items-center"

/** Shown once, the first time Smart Notes opens after a user drops to the free
 *  plan: why it happened, and, row by row, what they had and what Free turns it
 *  into. Upgrading is the loud button; staying on Free is one quiet click. */
export const FreePlanStartedScreen = ({
  dailyNotesLimit,
  impact,
  onContinue,
  reason,
}: FreePlanStartedScreenProps) => {
  const { t } = useTranslation()
  const none = t("freePlanStarted.freeValues.none")
  const fieldsStop = (count: number) =>
    count > 0
      ? t("freePlanStarted.freeValues.fieldsStop", { count })
      : undefined
  const fieldsMove = (count: number) =>
    count > 0
      ? t("freePlanStarted.freeValues.fieldsToStandard", { count })
      : undefined
  // Voice fields on a voice Free doesn't include move to a Standard voice in
  // their language, or stop when there's none.
  const voiceNote =
    impact.voiceStops === 0
      ? fieldsMove(impact.voiceFallbacks)
      : impact.voiceFallbacks === 0
        ? fieldsStop(impact.voiceStops)
        : t("freePlanStarted.freeValues.fieldsChange", {
            count: impact.voiceFallbacks + impact.voiceStops,
          })
  const losses: Loss[] = [
    {
      icon: SparklesIcon,
      key: "notes",
      free: t("freePlanStarted.freeValues.dailyNotes", {
        count: dailyNotesLimit,
      }),
    },
    {
      icon: VolumeIcon,
      key: "audio",
      free: t("freePlanStarted.freeValues.standardVoices"),
      yours: voiceNote,
    },
    {
      icon: GalleryIcon,
      key: "images",
      free: none,
      yours: fieldsStop(impact.imageFields),
    },
    {
      icon: CardIcon,
      key: "batch",
      free: t("freePlanStarted.freeValues.oneAtATime"),
    },
    { icon: CogIcon, key: "review", free: none },
    { icon: CogIcon, key: "added", free: none },
    {
      icon: BoltIcon,
      key: "models",
      free: t("freePlanStarted.freeValues.autoStandardOnly"),
      yours: fieldsMove(impact.modelFallbacks),
    },
    {
      icon: SearchIcon,
      key: "webSearch",
      free: none,
      yours:
        impact.webSearchFallbacks > 0
          ? t("freePlanStarted.freeValues.fieldsWithoutSearch", {
              count: impact.webSearchFallbacks,
            })
          : undefined,
    },
  ]
  const wasTrial = reason !== "accessEnded"

  return (
    <main
      className="relative isolate flex h-full w-full overflow-y-auto bg-canvas px-[54px] py-8 text-ink"
      data-testid="free-plan-started-screen"
    >
      {/* The welcome screen's ambient light, gathered under the way back. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(620px 380px at 50% 88%, rgba(31,212,125,0.07), transparent 70%), radial-gradient(620px 420px at 50% 18%, rgba(124,141,255,0.05), transparent 70%)",
        }}
      />
      <SparkleField className="inset-0" sparkles={SPARKLES} />
      <div className="relative z-10 m-auto flex w-full max-w-[680px] flex-col items-center">
        <p
          className="welcome-enter text-[13.5px] font-semibold text-ink-muted"
          style={enterDelay(0)}
        >
          {t(`freePlanStarted.reasons.${reason}`)}
        </p>
        <h1
          className="welcome-enter mt-2 text-center text-[38px] leading-[1.1] font-extrabold tracking-[-0.8px] text-ink"
          style={enterDelay(60)}
        >
          {t("freePlanStarted.title")}
        </h1>
        <p
          className="welcome-enter mt-3 text-center text-[14.5px] text-ink-muted"
          style={enterDelay(120)}
        >
          {t("freePlanStarted.description")}
        </p>

        {/* What the user has now and what Free turns it into, with an arrow
            between them on every row. */}
        <section className="welcome-enter mt-8 w-full" style={enterDelay(180)}>
          <div className={`${COMPARISON_GRID} pb-2`}>
            <span />
            <ColumnLabel className="text-center text-mint">
              {t(`freePlanStarted.nowLabel.${wasTrial ? "trial" : "plan"}`)}
            </ColumnLabel>
            <span />
            <ColumnLabel className="text-ink-muted">
              {t("freePlanStarted.freeLabel")}
            </ColumnLabel>
          </div>
          <div className="divide-y divide-hairline border-y border-hairline">
            {losses.map(({ icon: Icon, key, free, yours }) => (
              <div className={`${COMPARISON_GRID} h-[40px]`} key={key}>
                <span className="flex min-w-0 items-center gap-3">
                  <Icon className="shrink-0 text-ink-faint" size={17} />
                  <span className="truncate text-[14.5px] font-medium text-ink">
                    {t(`freePlanStarted.losses.${key}`)}
                  </span>
                </span>
                <span className="flex items-center justify-center">
                  <Check
                    aria-hidden
                    className="size-[17px] text-mint"
                    strokeWidth={2.75}
                  />
                </span>
                <span className="flex items-center justify-center text-ink-muted">
                  <ArrowRight
                    aria-hidden
                    className="size-4 rtl:rotate-180"
                    strokeWidth={2.25}
                  />
                </span>
                <span className="flex min-w-0 items-baseline gap-2">
                  <span className="shrink-0 text-[14.5px] font-bold text-ink">
                    {free}
                  </span>
                  {yours !== undefined && (
                    <span className="min-w-0 truncate text-xs text-ink-muted">
                      {yours}
                    </span>
                  )}
                </span>
              </div>
            ))}
          </div>
        </section>

        <div
          className="welcome-enter mt-8 flex w-full max-w-[380px] flex-col items-center"
          style={enterDelay(240)}
        >
          <GlowButton onClick={() => openSiteLink(SITE_LINKS.upgrade)}>
            {t("freePlanStarted.upgrade")}
          </GlowButton>
          <p className="mt-2.5 text-[13px] text-ink-muted">
            {t("freePlanStarted.pricing")}
          </p>
          <ReviewOffer className="mt-4 w-full" variant="button" />
          <button
            className="mt-5 cursor-pointer px-3 py-1 text-[13px] text-ink-muted underline-offset-4 transition hover:text-ink hover:underline"
            onClick={onContinue}
            type="button"
          >
            {t("freePlanStarted.continue")}
          </button>
        </div>
      </div>
    </main>
  )
}

const enterDelay = (ms: number): CSSProperties => ({
  animationDelay: `${ms}ms`,
})

const ColumnLabel = ({
  children,
  className,
}: {
  children: string
  className: string
}) => (
  <span
    // eslint-disable-next-line better-tailwindcss/no-restricted-classes -- an 11px all-caps eyebrow on a full-window moment; 12px sentence case would change its look
    className={`text-[11px] font-bold tracking-[0.08em] whitespace-nowrap uppercase ${className}`}
  >
    {children}
  </span>
)
