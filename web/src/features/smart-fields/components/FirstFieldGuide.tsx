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

import { X } from "lucide-react"
import type { CSSProperties } from "react"
import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"

import { SparklesEmoji } from "@/components/shared/Emoji"
import { IconButton } from "@/components/ui/IconButton"
import { useAppStore } from "@/store/appStore"
import { type Sparkle, SparkleField } from "@/components/shared/SparkleField"

import { Confetti } from "./Confetti"
import generateBatchClip from "../assets/generate-batch.webp"
import generateSingleClip from "../assets/generate-single.webp"

// Clips rendered from `media/` (the HowTo-* compositions), each with a little tilt.
const OPTIONS = [
  { key: "single", clip: generateSingleClip, tilt: "-rotate-2" },
  { key: "batch", clip: generateBatchClip, tilt: "rotate-[1.5deg]" },
] as const

const SPARKLES: readonly Sparkle[] = [
  { delay: "-1.7s", duration: "15s", size: "12px", left: "8%", top: "4%" },
  { delay: "-0.6s", duration: "18s", size: "16px", left: "15%", top: "18%" },
  { delay: "-2.9s", duration: "13s", size: "11px", left: "86%", top: "2%" },
  { delay: "-1.3s", duration: "16s", size: "15px", left: "92%", top: "20%" },
  { delay: "-0.3s", duration: "17s", size: "10px", left: "3%", top: "60%" },
  { delay: "-2.4s", duration: "19s", size: "13px", left: "97%", top: "66%" },
]

const enterDelay = (ms: number): CSSProperties => ({
  animationDelay: `${ms}ms`,
})

interface FirstFieldGuideProps {
  onDismiss: () => void
}

/** Shows how to generate a Smart Field, under the list once the first one is saved. */
export const FirstFieldGuide = ({ onDismiss }: FirstFieldGuideProps) => {
  const { t } = useTranslation()
  // The confetti and entrance play once, not each time the user comes back to the
  // screen. Read once on mount, so marking it seen doesn't cut the animation short.
  const [celebrate] = useState(
    () => useAppStore.getState().firstFieldGuide === "new",
  )
  const enter = celebrate ? "guide-pop" : ""
  useEffect(() => {
    useAppStore.setState({ firstFieldGuide: "seen" })
  }, [])

  return (
    <section
      aria-labelledby="first-field-guide-title"
      className="relative mt-12 pb-6"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -inset-x-10 -top-10 bottom-0 bg-[radial-gradient(420px_220px_at_50%_30%,rgba(31,212,125,0.08),transparent_70%)]"
      />
      <SparkleField className="inset-0" sparkles={SPARKLES} />
      {celebrate && <Confetti />}
      <IconButton
        aria-label={t("smartFields.firstFieldGuide.dismissAriaLabel")}
        // Above the full-width title, which comes after it.
        className="absolute end-0 top-0 z-10"
        onClick={onDismiss}
      >
        <X aria-hidden className="size-3.5" />
      </IconButton>

      <h2
        className={`${enter} relative flex items-center justify-center gap-2.5 text-center text-[28px] leading-[1.1] font-extrabold tracking-[-0.6px] text-ink`}
        id="first-field-guide-title"
        style={enterDelay(0)}
      >
        {t("smartFields.firstFieldGuide.title")}
        <SparklesEmoji size={26} />
      </h2>

      {/* Titles and clips sit on shared rows, so the clips line up when a translated
          title wraps. */}
      <ul className="relative mx-auto mt-8 grid w-fit grid-cols-[repeat(2,240px)] grid-rows-[auto_auto] gap-x-8">
        {OPTIONS.map(({ key, clip, tilt }, index) => (
          <li
            className={`${enter} row-span-2 grid grid-rows-subgrid justify-items-center text-center`}
            key={key}
            style={enterDelay(250 + index * 160)}
          >
            <p className="self-end text-[17px] font-semibold text-ink">
              {t(`smartFields.firstFieldGuide.methods.${key}.title`)}
            </p>
            <img
              alt={t(`smartFields.firstFieldGuide.methods.${key}.imageAlt`)}
              className={`mt-4 aspect-square w-[180px] rounded-xl shadow-[0_14px_30px_-12px_rgba(0,0,0,0.7)] transition-transform duration-200 hover:scale-[1.04] hover:rotate-0 ${tilt}`}
              src={clip}
            />
          </li>
        ))}
      </ul>
    </section>
  )
}
