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

import type { CSSProperties } from "react"
import { useEffect, useRef } from "react"
import { useTranslation } from "react-i18next"

import { ConfettiIcon } from "@/components/shared/Icons"
import { trackAnalyticsEvent } from "@/services/analytics"
import type { SmartField } from "@/types/api"

import generateFieldImage from "./assets/generate-field.png"
import generateInBrowserImage from "./assets/generate-in-browser.png"
import generateNoteImage from "./assets/generate-note.png"

interface StepDoneProps {
  fieldType: SmartField["fieldType"]
  noteTypeName: string
  targetFieldName: string
  trackCreation: boolean
}

const GENERATION_METHODS = [
  {
    image: generateInBrowserImage,
    imageAlt: "fieldEditor.completion.methods.bulk.imageAlt",
    imagePosition: "object-center",
    title: "fieldEditor.completion.methods.bulk.title",
    caption: "fieldEditor.completion.methods.bulk.caption",
  },
  {
    image: generateNoteImage,
    imageAlt: "fieldEditor.completion.methods.card.imageAlt",
    imagePosition:
      "origin-top-right rtl:origin-top-left scale-[2.1] object-right rtl:object-left",
    title: "fieldEditor.completion.methods.card.title",
    caption: "fieldEditor.completion.methods.card.caption",
  },
  {
    image: generateFieldImage,
    imageAlt: "fieldEditor.completion.methods.field.imageAlt",
    imagePosition:
      "origin-bottom-left rtl:origin-bottom-right scale-[1.15] object-bottom",
    title: "fieldEditor.completion.methods.field.title",
    caption: "fieldEditor.completion.methods.field.caption",
  },
]

type ConfettiStyle = CSSProperties & {
  "--confetti-burst-x": string
  "--confetti-burst-y": string
  "--confetti-color": string
  "--confetti-delay": string
  "--confetti-duration": string
  "--confetti-end-x": string
  "--confetti-end-y": string
  "--confetti-mid-turn": string
  "--confetti-turn": string
}

const CONFETTI_PIECES = [
  [-320, -40, -390, 630, 210, 780, "var(--color-indigo)", 0.01, 2.35],
  [-290, 40, -355, 680, -190, -720, "var(--color-mint)", 0.04, 2.5],
  [-250, 110, -310, 700, 250, 840, "var(--color-pastel-butter)", 0.02, 2.4],
  [-220, -55, -270, 620, -220, -760, "var(--color-pastel-pink)", 0.07, 2.55],
  [-180, 155, -215, 720, 190, 700, "var(--color-pastel-sky)", 0, 2.3],
  [-140, 70, -165, 660, -240, -800, "var(--color-pastel-lavender)", 0.05, 2.45],
  [-95, -65, -115, 610, 220, 760, "var(--color-pastel-butter)", 0.03, 2.6],
  [-45, 180, -55, 730, -180, -680, "var(--color-mint)", 0.08, 2.25],
  [40, -70, 50, 600, 240, 820, "var(--color-pastel-pink)", 0.02, 2.55],
  [80, 170, 100, 720, -210, -740, "var(--color-indigo)", 0.06, 2.3],
  [130, 70, 160, 650, 190, 720, "var(--color-pastel-sky)", 0, 2.45],
  [175, -55, 215, 610, -230, -800, "var(--color-pastel-butter)", 0.04, 2.6],
  [220, 140, 270, 700, 220, 780, "var(--color-pastel-lavender)", 0.07, 2.35],
  [260, 45, 320, 660, -190, -720, "var(--color-mint)", 0.02, 2.5],
  [300, -35, 370, 620, 250, 840, "var(--color-pastel-pink)", 0.05, 2.4],
  [330, 100, 405, 690, -220, -760, "var(--color-indigo)", 0.01, 2.55],
] as const

export const CompletionConfetti = () => (
  <div aria-hidden className="completion-confetti">
    {CONFETTI_PIECES.map(
      ([burstX, burstY, endX, endY, midTurn, turn, color, delay, duration]) => (
        <i
          className="completion-confetti-piece"
          key={`${burstX}-${burstY}`}
          style={
            {
              "--confetti-burst-x": `${burstX}px`,
              "--confetti-burst-y": `${burstY}px`,
              "--confetti-color": color,
              "--confetti-delay": `${delay}s`,
              "--confetti-duration": `${duration}s`,
              "--confetti-end-x": `${endX}px`,
              "--confetti-end-y": `${endY}px`,
              "--confetti-mid-turn": `${midTurn}deg`,
              "--confetti-turn": `${turn}deg`,
            } as ConfettiStyle
          }
        />
      ),
    )}
  </div>
)

const CompletionTelemetry = ({
  fieldType,
  trackCreation,
}: Pick<StepDoneProps, "fieldType" | "trackCreation">) => {
  const didTrackCompletion = useRef(false)

  useEffect(() => {
    if (!trackCreation || didTrackCompletion.current) return

    didTrackCompletion.current = true
    void trackAnalyticsEvent({
      event: "smart_field_completion_shown",
      properties: { field_type: fieldType },
    })
  }, [fieldType, trackCreation])

  return null
}

export const StepDone = ({
  fieldType,
  noteTypeName,
  targetFieldName,
  trackCreation,
}: StepDoneProps) => {
  const { t } = useTranslation()

  return (
    <div>
      <CompletionTelemetry
        fieldType={fieldType}
        trackCreation={trackCreation}
      />
      <div className="text-center">
        <h2 className="text-[27px] leading-[1.1] font-extrabold tracking-[-0.8px] text-ink">
          {t("fieldEditor.completion.title")}
          <ConfettiIcon className="ms-2 inline-block align-[-2px]" size={24} />
        </h2>
        <p className="mx-auto mt-3 max-w-[430px] text-[14.5px] leading-[1.55] text-ink-muted">
          <strong className="font-semibold text-ink">{targetFieldName}</strong>{" "}
          {t("fieldEditor.completion.descriptionBefore")}{" "}
          <strong className="font-semibold text-ink">{noteTypeName}</strong>{" "}
          {t("fieldEditor.completion.descriptionAfter")}
        </p>
      </div>

      <div className="mt-[34px]">
        <p className="mb-3.5 text-[13px] font-semibold text-ink-muted">
          {t("fieldEditor.completion.waysToGenerate")}
        </p>
        <div className="flex flex-col gap-2.5">
          {GENERATION_METHODS.map((method) => (
            <div
              className="grid grid-cols-[320px_1fr] items-center gap-[22px]"
              key={method.title}
            >
              <div className="h-[156px] w-[320px] overflow-hidden rounded-lg bg-black/30">
                <img
                  alt={t(method.imageAlt)}
                  className={`size-full object-cover ${method.imagePosition}`}
                  src={method.image}
                />
              </div>
              <div className="min-w-0">
                <h3 className="text-sm font-semibold text-ink">
                  {t(method.title)}
                </h3>
                <p className="mt-[3px] text-[12.5px] leading-[1.5] text-ink-muted">
                  {t(method.caption)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
