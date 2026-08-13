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

import type { getDefaultUsage } from "./defaultUsage"

type DefaultUsage = ReturnType<typeof getDefaultUsage>

/** How far this default reaches, for the screen header. A default no field uses is not
 *  worth a badge, so it gets none. */
export const DefaultUsagePill = ({ usage }: { usage: DefaultUsage }) => {
  if (usage.following === 0 && usage.pinned === 0) return null

  return (
    <span className="shrink-0 rounded-full border border-white/[0.08] bg-white/[0.025] px-3 py-1.5 text-[10.5px] text-zinc-400">
      {usage.following > 0 && (
        <>
          Applies to {usage.following} field
          {usage.following === 1 ? "" : "s"}
        </>
      )}
      {usage.pinned > 0 && (
        <span className="text-amber">
          {usage.following > 0 && " · "}
          {usage.pinned} pinned
        </span>
      )}
    </span>
  )
}
