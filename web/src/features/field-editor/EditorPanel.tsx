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

import { ChevronDown } from "lucide-react"
import { useId, type ReactNode } from "react"

interface EditorPanelProps {
  // Sits after the subtitle, like the tester's recent image results.
  accessory?: ReactNode
  children: ReactNode
  icon: ReactNode
  isOpen: boolean
  onToggle: () => void
  subtitle?: string
  // Lets a control inside the panel point at the subtitle with aria-describedby.
  subtitleId?: string
  title: string
  tone?: "indigo" | "neutral"
}

/** A hung surface in the field editor that folds down to its header row. The parent
 *  owns whether it's open, since opening one panel can fold another. */
export const EditorPanel = ({
  accessory,
  children,
  icon,
  isOpen,
  onToggle,
  subtitle,
  subtitleId,
  title,
  tone = "neutral",
}: EditorPanelProps) => {
  const bodyId = useId()

  return (
    <section
      className={`hang overflow-hidden rounded-xl ${tone === "indigo" ? "bg-indigo/[0.07]" : "bg-white/[0.05]"}`}
    >
      {/* The accessory holds its own buttons, so it sits beside the toggle, not in it. */}
      <div className="flex items-center gap-2.5">
        <h2 className="min-w-0 flex-1">
          <button
            aria-controls={bodyId}
            aria-expanded={isOpen}
            className="flex w-full cursor-pointer items-center gap-2.5 py-4 text-start"
            onClick={onToggle}
            type="button"
          >
            {icon}
            <span className="min-w-0 flex-1">
              <span className="block text-[16px] leading-tight font-semibold text-ink">
                {title}
              </span>
              {subtitle !== undefined && (
                <span
                  className="mt-0.5 block truncate text-xs text-ink-muted"
                  id={subtitleId}
                >
                  {subtitle}
                </span>
              )}
            </span>
          </button>
        </h2>
        {accessory}
        {/* Clickable for the pointer; keyboard users toggle with the button above. */}
        <ChevronDown
          aria-hidden
          className={`size-4 shrink-0 cursor-pointer text-ink-faint transition-transform ${isOpen ? "rotate-180" : ""}`}
          onClick={onToggle}
        />
      </div>
      {isOpen && (
        <div className="animate-fade-in pb-5" id={bodyId}>
          {children}
        </div>
      )}
    </section>
  )
}
