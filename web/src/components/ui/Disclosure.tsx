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
import { useId, useState, type ReactNode } from "react"

interface DisclosureProps {
  children: ReactNode
  className?: string
  // Open from the start when something inside is already in use, so nothing is hidden.
  defaultOpen?: boolean
  label: string
}

/** A quiet text button ("Advanced options") that shows the settings stacked under it. */
export const Disclosure = ({
  children,
  className = "",
  defaultOpen = false,
  label,
}: DisclosureProps) => {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const contentId = useId()

  return (
    <div className={className}>
      <button
        aria-controls={contentId}
        aria-expanded={isOpen}
        className="inline-flex cursor-pointer items-center gap-1 py-1 text-[13px] font-medium text-ink-muted transition hover:text-ink"
        onClick={() => setIsOpen(!isOpen)}
        type="button"
      >
        {label}
        <ChevronDown
          aria-hidden
          className={`size-3.5 transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>
      {isOpen && (
        <div className="mt-3 grid gap-3" id={contentId}>
          {children}
        </div>
      )}
    </div>
  )
}
