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

import { trackAnalyticsEvent } from "@/services/commands"
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
    imageAlt:
      "Anki Browser context menu with Generate Smart Fields highlighted",
    imagePosition: "object-center",
    title: "In bulk, from the Browser",
    caption: "Select notes or deck → right-click → ✨ Generate Smart Fields.",
  },
  {
    image: generateNoteImage,
    imageAlt: "Anki editor toolbar with the Smart Notes button highlighted",
    imagePosition: "origin-top-right scale-[2.1] object-right",
    title: "One card at a time",
    caption: "Click the ✨ button in the editor toolbar or type ⌘⇧G.",
  },
  {
    image: generateFieldImage,
    imageAlt: "Anki field context menu with Generate Smart Field highlighted",
    imagePosition: "origin-bottom-left scale-[1.15] object-bottom",
    title: "A single field",
    caption: "Right-click any field → Generate Smart Field.",
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
  [-320, -40, -390, 630, 210, 780, "#7c8dff", 0.01, 2.35],
  [-290, 40, -355, 680, -190, -720, "#4ade80", 0.04, 2.5],
  [-250, 110, -310, 700, 250, 840, "#ffd27a", 0.02, 2.4],
  [-220, -55, -270, 620, -220, -760, "#f58fb0", 0.07, 2.55],
  [-180, 155, -215, 720, 190, 700, "#5eead4", 0, 2.3],
  [-140, 70, -165, 660, -240, -800, "#a78bfa", 0.05, 2.45],
  [-95, -65, -115, 610, 220, 760, "#ffd27a", 0.03, 2.6],
  [-45, 180, -55, 730, -180, -680, "#4ade80", 0.08, 2.25],
  [40, -70, 50, 600, 240, 820, "#f58fb0", 0.02, 2.55],
  [80, 170, 100, 720, -210, -740, "#7c8dff", 0.06, 2.3],
  [130, 70, 160, 650, 190, 720, "#5eead4", 0, 2.45],
  [175, -55, 215, 610, -230, -800, "#ffd27a", 0.04, 2.6],
  [220, 140, 270, 700, 220, 780, "#a78bfa", 0.07, 2.35],
  [260, 45, 320, 660, -190, -720, "#4ade80", 0.02, 2.5],
  [300, -35, 370, 620, 250, 840, "#f58fb0", 0.05, 2.4],
  [330, 100, 405, 690, -220, -760, "#7c8dff", 0.01, 2.55],
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
    }).catch(() => undefined)
  }, [fieldType, trackCreation])

  return null
}

export const StepDone = ({
  fieldType,
  noteTypeName,
  targetFieldName,
  trackCreation,
}: StepDoneProps) => (
  <div>
    <CompletionTelemetry fieldType={fieldType} trackCreation={trackCreation} />
    <div className="text-center">
      <h2 className="text-[27px] leading-[1.1] font-extrabold tracking-[-0.8px] text-[#f6f6f8]">
        Your Smart Field is live
        <span
          aria-hidden
          className="ml-1.5 inline-block translate-y-[-3px] text-lg font-normal"
        >
          🥳
        </span>
      </h2>
      <p className="mx-auto mt-3 max-w-[430px] text-[13.5px] leading-[1.55] text-[#b4b4be]">
        <strong className="font-semibold text-[#e6e6ea]">
          {targetFieldName}
        </strong>{" "}
        on{" "}
        <strong className="font-semibold text-[#e6e6ea]">{noteTypeName}</strong>{" "}
        notes fills in whenever you generate it.
      </p>
    </div>

    <div className="mt-[34px]">
      <p className="mb-3.5 text-xs font-semibold text-[#8b8b94]">
        A few ways to generate it:
      </p>
      <div className="flex flex-col gap-2.5">
        {GENERATION_METHODS.map((method) => (
          <div
            className="grid grid-cols-[320px_1fr] items-center gap-[22px]"
            key={method.title}
          >
            <div className="h-[156px] w-[320px] overflow-hidden rounded-lg border border-white/[0.08] bg-black/30">
              <img
                alt={method.imageAlt}
                className={`size-full object-cover ${method.imagePosition}`}
                src={method.image}
              />
            </div>
            <div className="min-w-0">
              <h3 className="text-[13px] font-semibold text-[#f4f4f6]">
                {method.title}
              </h3>
              <p className="mt-[3px] text-[11.5px] leading-[1.5] text-[#8b8b94]">
                {method.caption}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
)
