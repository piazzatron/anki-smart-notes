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

import { Star, X } from "lucide-react"
import { useTranslation } from "react-i18next"

import { selectReviewBanner } from "../bannerPrompt"

import { IconButton } from "@/components/ui/IconButton"
import { GiftIcon } from "@/components/shared/Icons"
import { useReviewOffer } from "@/features/review-offer/ReviewOffer"
import { ANKIWEB_REVIEW_URL } from "@/lib/helpChannels"
import { useAppStore } from "@/store/appStore"

interface ReviewPromptProps {
  onComplete: () => void
}

/** The "Enjoying Smart Notes?" banner: the free-month offer or the plain
 *  AnkiWeb review ask (`selectReviewBanner` decides). */
export const ReviewPrompt = ({ onComplete }: ReviewPromptProps) => {
  const offerUnlocked = useAppStore(
    (store) => store.state?.reviewOfferUnlocked ?? false,
  )
  const { enabled, claimState, loading, open, dialog } = useReviewOffer({
    onDone: onComplete,
  })
  const banner = selectReviewBanner({
    reviewFreeMonth: enabled,
    offerUnlocked,
    claimLoading: loading,
    claimState,
  })

  return (
    <>
      {banner === "offer" && (
        <ReviewBanner offer onComplete={onComplete} onOpenOffer={open} />
      )}
      {banner === "plain" && <ReviewBanner onComplete={onComplete} />}
      {dialog}
    </>
  )
}

/** The banner itself: the plain review ask is gold and links to AnkiWeb, and
 *  the offer is purple and opens the free-month dialog. */
const ReviewBanner = ({
  offer = false,
  onComplete,
  onOpenOffer,
}: {
  offer?: boolean
  onComplete: () => void
  onOpenOffer?: () => void
}) => {
  const { t } = useTranslation()
  const action = offer
    ? { onClick: onOpenOffer }
    : {
        href: ANKIWEB_REVIEW_URL,
        onClick: onComplete,
        rel: "noreferrer",
        target: "_blank",
      }
  const Action = offer ? "button" : "a"

  return (
    <div
      // eslint-disable-next-line local/no-hex-color -- the review banner's gold gradient has no token
      className={`relative -mx-hang mb-5 flex cursor-pointer items-center gap-3 overflow-hidden rounded-[13px] py-3.5 ps-hang pe-3.5 transition-transform duration-150 ease-out hover:scale-[1.006] ${offer ? "review-offer-fill shadow-[0_14px_32px_-14px_rgba(124,92,246,0.85)]" : "bg-[linear-gradient(100deg,#b4560a_0%,#e0900f_46%,#f7c14a_100%)]"}`}
    >
      <Action
        aria-label={t(
          offer
            ? "smartFields.review.offerAriaLabel"
            : "smartFields.review.ariaLabel",
        )}
        className="absolute inset-0 z-10 rounded-[13px]"
        type={offer ? "button" : undefined}
        {...action}
      />
      {/* The offer wears the purple of the free-month offer elsewhere
          (ReviewOffer), so it reads as a different thing from the gold ask. */}
      {offer ? (
        <>
          <span aria-hidden className="review-offer-sheen" />
          <GiftIcon className="relative shrink-0 text-white" size={23} />
        </>
      ) : (
        <>
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(500px_150px_at_8%_-45%,rgba(255,244,206,0.34),transparent_72%)]" />
          <div aria-hidden className="banner-shine" />
          <Star
            aria-hidden
            className="review-star relative shrink-0 fill-pastel-butter text-pastel-butter"
            size={23}
          />
        </>
      )}
      <div className="relative min-w-0 flex-1 text-start">
        <p className="truncate text-[14px] leading-[1.35] font-semibold text-white">
          {t("smartFields.review.title")}
        </p>
        <p className="truncate text-sm leading-[1.35] font-medium text-white/80">
          {t(
            offer
              ? "smartFields.review.offerSubtitle"
              : "smartFields.review.subtitle",
          )}
        </p>
      </div>
      <Action
        // eslint-disable-next-line local/no-hex-color -- a button on a colored banner takes its banner's own colors (ui-design skill)
        className={`relative z-20 inline-flex banner-button items-center no-underline transition-transform duration-150 ease-out hover:scale-[1.035] ${offer ? "bg-white font-semibold text-[#4b3fb0]" : "bg-[#fff7dc] text-[#7b4807]"}`}
        type={offer ? "button" : undefined}
        {...action}
      >
        {t(
          offer
            ? "smartFields.review.offerButton"
            : "smartFields.review.button",
        )}
      </Action>
      <IconButton
        aria-label={t("smartFields.review.dismissAriaLabel")}
        onClick={onComplete}
        tone="banner"
      >
        <X aria-hidden className="size-3.5" />
      </IconButton>
    </div>
  )
}
