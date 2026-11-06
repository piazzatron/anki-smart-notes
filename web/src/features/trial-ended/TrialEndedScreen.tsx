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

import { Image, Layers3, Play, Sparkles, type LucideIcon } from "lucide-react"
import { useEffect } from "react"
import { useTranslation } from "react-i18next"

import { SparklesIcon } from "@/components/shared/Icons"
import { ReviewOffer } from "@/features/review-offer/ReviewOffer"
import { openSiteLink, SITE_LINKS } from "@/lib/siteLinks"
import { trackAnalyticsEvent } from "@/services/analytics"

const KEPT_FEATURES: Array<{ icon: LucideIcon; labelKey: string }> = [
  { icon: Layers3, labelKey: "trialEnded.features.batch" },
  { icon: Play, labelKey: "trialEnded.features.review" },
  { icon: Image, labelKey: "trialEnded.features.images" },
  { icon: Sparkles, labelKey: "trialEnded.features.premium" },
]

export const TrialEndedScreen = () => {
  const { t } = useTranslation()

  useEffect(() => {
    void trackAnalyticsEvent({ event: "trial_ended_shown" })
  }, [])

  return (
    <main
      className="flex h-full w-full items-center justify-center overflow-y-auto bg-canvas px-[54px] py-7 text-ink"
      data-testid="trial-ended-screen"
    >
      <div className="my-auto flex w-full max-w-[560px] flex-col gap-[18px]">
        <ReviewOffer />

        <header className="text-center">
          <p className="mb-2 text-[13.5px] leading-none font-semibold text-[#5fe3b0]">
            {t("trialEnded.thanks")}
            <SparklesIcon
              className="ms-1 inline-block align-[-2px]"
              size={13}
            />
          </p>
          <h1 className="text-[28px] leading-[1.15] font-bold tracking-[-0.02em] text-[#f4f4f6]">
            {t("trialEnded.title")}
          </h1>
          <p className="mt-[9px] text-sm leading-[1.45] text-ink-muted">
            {t("trialEnded.description")}
          </p>
        </header>

        <section
          aria-label={t("trialEnded.features.ariaLabel")}
          className="divide-y divide-hairline rounded-xl bg-white/[0.03] px-[18px] py-1.5"
        >
          {KEPT_FEATURES.map(({ icon: Icon, labelKey }) => (
            <div
              className="flex min-h-[46px] items-center gap-3"
              key={labelKey}
            >
              <span className="inline-flex size-[30px] shrink-0 items-center justify-center rounded-lg bg-white/[0.04] text-[#c3c3cb]">
                <Icon aria-hidden className="size-[17px]" />
              </span>
              <span className="text-sm leading-tight font-medium text-[#e6e6ea]">
                {t(labelKey)}
              </span>
            </div>
          ))}
        </section>

        <button
          className="flex h-[46px] w-full items-center justify-center rounded-[10px] bg-[#1fd47d] text-[14.5px] font-bold tracking-[-0.1px] text-[#06281a] transition-[filter,transform] duration-150 hover:scale-[1.006] hover:brightness-105"
          onClick={() => {
            void trackAnalyticsEvent({ event: "clicked_trial_ended_upgrade" })
            openSiteLink(SITE_LINKS.upgrade)
          }}
          type="button"
        >
          {t("trialEnded.upgradeNow")}
        </button>
      </div>
    </main>
  )
}
