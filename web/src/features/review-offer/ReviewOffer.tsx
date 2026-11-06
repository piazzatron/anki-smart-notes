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

import { ArrowRight } from "lucide-react"
import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/Dialog"
import { Button } from "@/components/ui/Button"
import { GiftIcon } from "@/components/shared/Icons"
import { ANKIWEB_WRITE_REVIEW_URL } from "@/lib/helpChannels"
import { openSiteLink } from "@/lib/siteLinks"
import { trackAnalyticsEvent } from "@/services/analytics"
import { getReviewClaimState, sendReviewClaim } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { ReviewClaimState } from "@/types/api"

// The server's last answer this session, so a screen that remounts shows the
// offer at once while it asks again. `undefined` until the first request settles.
let lastClaimState: ReviewClaimState | null | undefined

/** The free month for an AnkiWeb review, for a call to action to open: whether
 *  the `review_free_month` flag is on, the server's answer on whether this
 *  account can get the month (`null` until it arrives, and after a failed
 *  request), `loading` until the session's first request settles (it stays
 *  `true` while the flag is off), and the dialog that claims it. `onDone` runs
 *  when the dialog closes after a claim, or after the server says this account
 *  can't get the month. */
export const useReviewOffer = ({ onDone }: { onDone?: () => void } = {}) => {
  const enabled = useAppStore(
    (store) => store.state?.featureFlags.reviewFreeMonth ?? false,
  )
  const [dialogOpen, setDialogOpen] = useState(false)
  const [claimState, setClaimStateValue] = useState(lastClaimState ?? null)
  const [loading, setLoading] = useState(lastClaimState === undefined)

  const setClaimState = (state: ReviewClaimState | null) => {
    lastClaimState = state
    setClaimStateValue(state)
  }

  useEffect(() => {
    if (!enabled) return
    getReviewClaimState()
      .then(setClaimState, () => setClaimState(lastClaimState ?? null))
      .finally(() => setLoading(false))
  }, [enabled])

  const changeOpen = (open: boolean) => {
    setDialogOpen(open)
    if (!open && (claimState === "claimed" || claimState === "unavailable")) {
      onDone?.()
    }
  }

  return {
    enabled,
    claimState,
    loading,
    open: () => setDialogOpen(true),
    dialog: (
      <ReviewOfferDialog
        claimState={claimState}
        onClaimed={setClaimState}
        onOpenChange={changeOpen}
        open={dialogOpen}
      />
    ),
  }
}

/** The free month on the trial-ended and free plan screens. Renders nothing
 *  while the `review_free_month` flag is off, and hides the call to action once
 *  the server says this account can't get the month. A `banner` leads the
 *  trial-ended screen; a `button` sits under the free plan screen's upgrade
 *  button as the second way to keep everything. */
export const ReviewOffer = ({
  className = "",
  variant = "banner",
}: {
  className?: string
  variant?: "banner" | "button"
}) => {
  const { enabled, claimState, open, dialog } = useReviewOffer()

  if (!enabled) return null

  const openDialog = () => {
    void trackAnalyticsEvent({ event: "clicked_trial_ended_review" })
    open()
  }

  // The offer shows until the server says this user can't get the free month.
  return (
    <>
      {claimState !== "unavailable" && (
        <div className={className}>
          {variant === "banner" ? (
            <ReviewOfferBanner onOpen={openDialog} />
          ) : (
            <ReviewOfferButton onOpen={openDialog} />
          )}
        </div>
      )}
      {dialog}
    </>
  )
}

// The banner's purple, as a button the width of the upgrade button above it.
const ReviewOfferButton = ({ onOpen }: { onOpen: () => void }) => {
  const { t } = useTranslation()
  return (
    <button
      className="relative flex h-[50px] w-full items-center justify-center gap-2.5 overflow-hidden rounded-[14px] review-offer-fill text-[16px] font-extrabold text-white shadow-[0_16px_36px_-12px_rgba(124,92,246,0.7)] transition-[filter,transform] duration-150 hover:scale-[1.01] hover:brightness-105"
      onClick={onOpen}
      type="button"
    >
      <span aria-hidden className="review-offer-sheen" />
      <GiftIcon className="relative text-white" size={22} />
      <span className="relative">
        {t("trialEnded.reviewOffer.buttonLabel")}
      </span>
    </button>
  )
}

const ReviewOfferBanner = ({ onOpen }: { onOpen: () => void }) => {
  const { t } = useTranslation()
  return (
    <section
      aria-label={t("trialEnded.reviewOffer.ariaLabel")}
      className="relative overflow-hidden rounded-xl review-offer-fill px-5 py-[18px] shadow-[0_18px_40px_-14px_rgba(124,92,246,0.85)]"
    >
      <span aria-hidden className="review-offer-sheen" />
      <div className="relative z-10 flex items-center gap-4">
        <GiftIcon className="text-white" size={36} />
        <span className="flex min-w-0 flex-1 flex-col gap-1">
          <span className="text-[17px] leading-[1.2] font-extrabold tracking-[-0.2px] text-white">
            {t("trialEnded.reviewOffer.title")}
          </span>
          <span className="text-[13.5px] leading-[1.3] text-white/90">
            {t("trialEnded.reviewOffer.description")}
          </span>
        </span>
        <button
          className="flex h-10 shrink-0 items-center rounded-[10px] bg-white px-[18px] text-[14px] font-extrabold whitespace-nowrap text-[#4b3fb0] transition-transform duration-150 hover:scale-[1.025]"
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
