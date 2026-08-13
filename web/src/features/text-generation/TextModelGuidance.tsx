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

import type { ReactNode } from "react"

export const TextModelGuidance = () => (
  <div className="mt-3 rounded-lg border border-indigo/15 bg-indigo/[0.055] p-3.5">
    <p className="text-xs font-semibold text-zinc-200">
      💡 Picking a model
    </p>
    <p className="mt-2 text-[11px] leading-4 text-ink-muted">
      <ModelName>Auto</ModelName> and <ModelName>Auto MAX</ModelName> are the
      Smart Notes recommended models that balance performance and cost. Choose{" "}
      <ModelName>Auto</ModelName> for standard tasks and upgrade to{" "}
      <ModelName>Auto MAX</ModelName> if needed.
    </p>
  </div>
)

const ModelName = ({ children }: { children: ReactNode }) => (
  <strong className="font-semibold text-indigo-soft">{children}</strong>
)
