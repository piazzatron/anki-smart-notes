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
import { useState } from "react"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/Dialog"
import { ANKIWEB_REVIEW_URL, SUPPORT_EMAIL } from "@/lib/helpChannels"
import { openSiteLink, SITE_LINKS } from "@/lib/siteLinks"

const KEPT_FEATURES: Array<{ icon: LucideIcon; label: string }> = [
  { icon: Layers3, label: "Batch across your whole collection" },
  { icon: Play, label: "Generate during review" },
  { icon: Image, label: "Image generation" },
  { icon: Sparkles, label: "Every premium model & voice" },
]

interface TrialEndedScreenProps {
  reviewFreeMonthEnabled: boolean
}

export const TrialEndedScreen = ({
  reviewFreeMonthEnabled,
}: TrialEndedScreenProps) => {
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false)

  return (
    <main
      className="flex h-full w-full items-center justify-center overflow-y-auto bg-canvas px-[54px] py-7 text-ink"
      data-testid="trial-ended-screen"
    >
      <div className="my-auto flex w-full max-w-[560px] flex-col gap-[18px]">
        {reviewFreeMonthEnabled && (
          <ReviewOfferBanner onOpen={() => setReviewDialogOpen(true)} />
        )}

        <header className="text-center">
          <p className="mb-2 text-[12.5px] leading-none font-semibold text-[#5fe3b0]">
            Thanks for using Smart Notes ✨
          </p>
          <h1 className="text-[28px] leading-[1.15] font-extrabold tracking-[-0.5px] text-[#f4f4f6]">
            Your free trial has ended
          </h1>
          <p className="mt-[9px] text-[13px] leading-[1.45] text-[#9a9aa4]">
            Trials run 7 days or until your trial credits run out. {<br />}
          </p>
        </header>

        <section
          aria-label="What upgrading keeps"
          className="rounded-xl bg-white/[0.03] px-[18px] py-1.5"
        >
          {KEPT_FEATURES.map(({ icon: Icon, label }) => (
            <div
              className="flex min-h-[46px] items-center gap-3 border-t border-white/[0.05] first:border-t-0"
              key={label}
            >
              <span className="inline-flex size-[30px] shrink-0 items-center justify-center rounded-lg bg-white/[0.04] text-[#c3c3cb]">
                <Icon aria-hidden className="size-[17px]" />
              </span>
              <span className="text-[13px] leading-tight font-medium text-[#e6e6ea]">
                {label}
              </span>
            </div>
          ))}
        </section>

        <button
          className="flex h-[46px] w-full items-center justify-center rounded-[10px] bg-[#1fd47d] text-[14.5px] font-bold tracking-[-0.1px] text-[#06281a] transition-[filter,transform] duration-150 hover:scale-[1.006] hover:brightness-105"
          onClick={() => openSiteLink(SITE_LINKS.upgrade)}
          type="button"
        >
          Upgrade now
        </button>
      </div>

      <ReviewOfferDialog
        onOpenChange={setReviewDialogOpen}
        open={reviewDialogOpen}
      />
    </main>
  )
}

const ReviewOfferBanner = ({ onOpen }: { onOpen: () => void }) => (
  <section
    aria-label="Free month offer"
    className="relative overflow-hidden rounded-xl bg-[linear-gradient(100deg,#5b6fe8_0%,#8b5cf6_52%,#6d8bff_100%)] px-4 py-[15px] shadow-[0_14px_34px_-14px_rgba(124,92,246,0.75)]"
  >
    <span
      aria-hidden
      className="review-offer-sheen pointer-events-none absolute inset-y-0 left-0 w-[55%] bg-[linear-gradient(105deg,transparent_30%,rgba(255,255,255,0.3)_50%,transparent_70%)]"
    />
    <div className="relative z-10 flex items-center gap-[13px]">
      <span aria-hidden className="shrink-0 text-[26px] leading-none">
        🎁
      </span>
      <span className="flex min-w-0 flex-1 flex-col gap-[3px]">
        <span className="text-sm leading-[1.2] font-bold text-white">
          Get a free month of Smart Notes
        </span>
        <span className="text-xs leading-[1.3] text-white/85">
          Leave a quick AnkiWeb review, get a month on us.
        </span>
      </span>
      <button
        className="flex h-[34px] shrink-0 items-center rounded-lg bg-white px-[15px] text-[12.5px] font-bold whitespace-nowrap text-[#4b3fb0] transition-transform duration-150 hover:scale-[1.025]"
        onClick={onOpen}
        type="button"
      >
        Leave a review →
      </button>
    </div>
  </section>
)

const ReviewOfferDialog = ({
  onOpenChange,
  open,
}: {
  onOpenChange: (open: boolean) => void
  open: boolean
}) => (
  <Dialog onOpenChange={onOpenChange} open={open}>
    <DialogContent className="w-[min(380px,92vw)]">
      <div className="px-[22px] pt-6 pb-[14px] text-center">
        <div aria-hidden className="text-[30px] leading-none">
          🎁
        </div>
        <DialogTitle className="mt-3 text-[16.5px] font-bold text-[#f4f4f6]">
          Get your free month
        </DialogTitle>
        <DialogDescription className="mt-2 text-[12.5px] leading-[1.5] text-[#9a9aa4]">
          Leave a quick review on AnkiWeb, then email us — we&apos;ll add a free
          month of Smart Notes to your account.
        </DialogDescription>
        <a
          className="mt-[18px] inline-flex h-[42px] w-full items-center justify-center rounded-[9px] bg-[#5b6fe8] text-[13.5px] font-bold text-white"
          href={ANKIWEB_REVIEW_URL}
          rel="noreferrer"
          target="_blank"
        >
          Leave a review on AnkiWeb →
        </a>
        <a
          className="mt-2 inline-flex h-9 w-full items-center justify-center rounded-[9px] bg-white/[0.05] text-[12px] font-semibold text-zinc-300 transition hover:bg-white/[0.08] hover:text-white"
          href={`mailto:${SUPPORT_EMAIL}`}
        >
          ✉️ {SUPPORT_EMAIL}
        </a>
        <button
          className="mt-2.5 w-full bg-transparent p-2 text-[11.5px] text-[#8b8b94] transition hover:text-zinc-300"
          onClick={() => onOpenChange(false)}
          type="button"
        >
          Not now
        </button>
      </div>
    </DialogContent>
  </Dialog>
)
