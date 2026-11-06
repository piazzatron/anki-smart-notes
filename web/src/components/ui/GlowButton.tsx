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

import { SparklesIcon } from "@/components/shared/Icons"

/** The mint, sparkle-flanked call to action with a glow: the one gradient in the
 *  app, kept for full-window moments like starting a trial or upgrading. */
export const GlowButton = ({
  children,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) => (
  <button
    className={`w-full rounded-[14px] border mint-cta px-5 py-[19px] text-[17px] font-extrabold tracking-[0.1px] shadow-[inset_0_1px_0_rgba(255,255,255,0.36),0_16px_36px_-10px_rgba(31,212,125,0.66)] transition-[filter,transform] duration-150 hover:scale-[1.01] ${className}`}
    type="button"
    {...props}
  >
    <SparklesIcon className="me-2 inline-block align-[-3px]" size={19} />
    {children}
    <SparklesIcon className="ms-2 inline-block align-[-3px]" size={19} />
  </button>
)
