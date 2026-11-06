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

import type { ButtonHTMLAttributes } from "react"

// `banner` sits on a colored banner whose own link covers the whole surface, so it
// stacks above it.
const TONE_CLASSES = {
  quiet: "text-ink-faint hover:bg-white/[0.08] hover:text-ink",
  banner: "relative z-20 text-white/60 hover:bg-white/10 hover:text-white",
}

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  "aria-label": string
  tone?: keyof typeof TONE_CLASSES
}

/** A small square button holding one Lucide icon: dismiss, add, and the like. */
export const IconButton = ({
  className = "",
  tone = "quiet",
  type = "button",
  ...props
}: IconButtonProps) => (
  <button
    className={`inline-flex size-6 shrink-0 items-center justify-center rounded-md transition ${TONE_CLASSES[tone]} ${className}`}
    type={type}
    {...props}
  />
)
