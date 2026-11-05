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

import {
  ArrowRight,
  Image,
  Layers3,
  Play,
  Sparkles,
  type LucideIcon,
} from "lucide-react"
import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/Dialog"
import { Button } from "@/components/ui/Button"
import { GiftIcon, SparklesIcon } from "@/components/shared/Icons"
import { ANKIWEB_WRITE_REVIEW_URL } from "@/lib/helpChannels"
import { openSiteLink, SITE_LINKS } from "@/lib/siteLinks"
import { trackAnalyticsEvent } from "@/services/analytics"
import { getReviewClaimState, sendReviewClaim } from "@/services/commands"
import type { ReviewClaimState } from "@/types/api"

const KEPT_FEATURES: Array<{ icon: LucideIcon; labelKey: string }> = [
  { icon: Layers3, labelKey: "trialEnded.features.batch" },
  { icon: Play, labelKey: "trialEnded.features.review" },
  { icon: Image, labelKey: "trialEnded.features.images" },
  { icon: Sparkles, labelKey: "trialEnded.features.premium" },
]

interface TrialEndedScreenProps {
  reviewFreeMonthEnabled: boolean
}

export const TrialEndedScreen = ({
  reviewFreeMonthEnabled,
}: TrialEndedScreenProps) => {
  const { t } = useTranslation()
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false)
  const [claimState, setClaimState] = useState<ReviewClaimState | null>(null)

  useEffect(() => {
    void trackAnalyticsEvent({ event: "trial_ended_shown" })
  }, [])

  // The offer shows until the server says this user can't get the free month.
  useEffect(() => {
    if (!reviewFreeMonthEnabled) return
    getReviewClaimState().then(setClaimState, () => undefined)
  }, [reviewFreeMonthEnabled])

  return (
    <main
      className="flex h-full w-full items-center justify-center overflow-y-auto bg-canvas px-[54px] py-7 text-ink"
      data-testid="trial-ended-screen"
    >
      <div className="my-auto flex w-full max-w-[560px] flex-col gap-[18px]">
        {reviewFreeMonthEnabled && claimState !== "unavailable" && (
          <ReviewOfferBanner
            onOpen={() => {
              void trackAnalyticsEvent({ event: "clicked_trial_ended_review" })
              setReviewDialogOpen(true)
            }}
          />
        )}

        <header className="text-center">
          <p className="mb-2 text-[13.5px] leading-none font-semibold text-[#5fe3b0]">
            {t("trialEnded.thanks")}
            <SparklesIcon
              className="ms-1 inline-block align-[-2px]"
              size={13}
            />
          </p>
          <h1 className="text-[28px] leading-[1.15] font-extrabold tracking-[-0.5px] text-[#f4f4f6]">
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

      <ReviewOfferDialog
        claimState={claimState}
        onClaimed={setClaimState}
        onOpenChange={setReviewDialogOpen}
        open={reviewDialogOpen}
      />
    </main>
  )
}

const ReviewOfferBanner = ({ onOpen }: { onOpen: () => void }) => {
  const { t } = useTranslation()
  return (
    <section
      aria-label={t("trialEnded.reviewOffer.ariaLabel")}
      className="relative overflow-hidden rounded-xl bg-[linear-gradient(100deg,#5b6fe8_0%,#8b5cf6_52%,#6d8bff_100%)] px-4 py-[15px] shadow-[0_14px_34px_-14px_rgba(124,92,246,0.75)]"
    >
      <span
        aria-hidden
        className="review-offer-sheen pointer-events-none absolute inset-y-0 start-0 w-[55%] bg-[linear-gradient(105deg,transparent_30%,rgba(255,255,255,0.3)_50%,transparent_70%)]"
      />
      <div className="relative z-10 flex items-center gap-[13px]">
        <GiftIcon className="text-white" size={28} />
        <span className="flex min-w-0 flex-1 flex-col gap-[3px]">
          <span className="text-sm leading-[1.2] font-bold text-white">
            {t("trialEnded.reviewOffer.title")}
          </span>
          <span className="text-[13px] leading-[1.3] text-white/85">
            {t("trialEnded.reviewOffer.description")}
          </span>
        </span>
        <button
          className="flex h-[34px] shrink-0 items-center rounded-lg bg-white px-[15px] text-[13.5px] font-bold whitespace-nowrap text-[#4b3fb0] transition-transform duration-150 hover:scale-[1.025]"
          onClick={onOpen}
          type="button"
        >
          {t("trialEnded.reviewOffer.leaveReview")}
          <ArrowRight aria-hidden className="ms-1 size-4 rtl:rotate-180" />
        </button>
      </div>
    </section>
  )
}

const ReviewOfferDialog = ({
  claimState,
  onClaimed,
  onOpenChange,
  open,
}: {
  claimState: ReviewClaimState | null
  onClaimed: (state: ReviewClaimState) => void
  onOpenChange: (open: boolean) => void
  open: boolean
}) => {
  const { t } = useTranslation()
  const [claiming, setClaiming] = useState(false)
  const [claimFailed, setClaimFailed] = useState(false)
  // After a claim, or when the server says this user can't get the month,
  // the steps give way to a note.
  const done = claimState === "claimed" || claimState === "unavailable"

  // A failed claim's error shouldn't greet the user when they come back.
  const changeOpen = (next: boolean) => {
    if (!next) setClaimFailed(false)
    onOpenChange(next)
  }

  const writeReview = () => {
    void trackAnalyticsEvent({ event: "clicked_write_review" })
    openSiteLink(ANKIWEB_WRITE_REVIEW_URL)
    // The server takes AnkiWeb's review count now, as the baseline the user's
    // review will raise.
    sendReviewClaim("write").then(onClaimed, () => undefined)
  }

  const claimReview = async () => {
    void trackAnalyticsEvent({ event: "clicked_left_review" })
    setClaiming(true)
    setClaimFailed(false)
    try {
      onClaimed(await sendReviewClaim("claim"))
    } catch {
      setClaimFailed(true)
    } finally {
      setClaiming(false)
    }
  }

  return (
    <Dialog onOpenChange={changeOpen} open={open}>
      <DialogContent className="w-[min(380px,92vw)]">
        <div className="px-[22px] pt-6 pb-[14px] text-center">
          <GiftIcon className="mx-auto" size={32} />
          <DialogTitle className="mt-3 text-[16.5px] font-bold text-ink">
            {t("trialEnded.reviewOffer.dialogTitle")}
          </DialogTitle>
          <DialogDescription
            aria-live="polite"
            className="mt-2 text-[13.5px] leading-[1.5] text-ink-muted"
          >
            {claimState === "claimed"
              ? t("trialEnded.reviewOffer.claimed")
              : claimState === "unavailable"
                ? t("trialEnded.reviewOffer.unavailable")
                : t("trialEnded.reviewOffer.dialogDescription")}
          </DialogDescription>
          {!done && (
            <>
              <Button
                className="mt-[18px] h-[42px] w-full text-[14.5px]"
                onClick={writeReview}
                variant="primary"
              >
                {t("trialEnded.reviewOffer.writeReview")}
                <ArrowRight aria-hidden className="size-4 rtl:rotate-180" />
              </Button>
              <Button
                className="mt-2 h-9 w-full"
                disabled={claiming}
                onClick={() => void claimReview()}
              >
                {t("trialEnded.reviewOffer.leftReview")}
              </Button>
              {claimFailed && (
                <p className="mt-2 text-xs text-danger" role="alert">
                  {t("trialEnded.reviewOffer.claimError")}
                </p>
              )}
            </>
          )}
          <button
            className="mt-2.5 w-full bg-transparent p-2 text-[12.5px] text-ink-muted transition hover:text-zinc-300"
            onClick={() => changeOpen(false)}
            type="button"
          >
            {done ? t("common.close") : t("common.notNow")}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
