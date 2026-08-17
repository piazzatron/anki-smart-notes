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

import { AlertCircle, X } from "lucide-react"

interface ErrorBannerProps {
  className?: string
  message: string
  onDismiss: () => void
}

export const ErrorBanner = ({
  className = "",
  message,
  onDismiss,
}: ErrorBannerProps) => (
  <div
    className={`flex items-start gap-2 rounded-lg border border-red-300/15 bg-red-300/[0.06] px-3 py-2.5 text-xs text-danger ${className}`}
  >
    <AlertCircle aria-hidden className="mt-0.5 size-3.5 shrink-0" />
    <p className="min-w-0 flex-1">{message}</p>
    <button
      aria-label="Dismiss error"
      className="cursor-pointer"
      onClick={onDismiss}
    >
      <X aria-hidden className="size-3.5" />
    </button>
  </div>
)
