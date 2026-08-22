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

import { useTranslation } from "react-i18next"

export const TextModelGuidance = () => {
  const { t } = useTranslation()

  return (
    <div className="mt-3 rounded-lg border border-indigo/15 bg-indigo/[0.055] p-3.5">
      <p className="text-xs font-semibold text-zinc-200">
        {t("defaults.text.pickingModel")}
      </p>
      <p className="mt-2 text-[11px] leading-4 text-ink-muted">
        {t("defaults.text.modelGuidance", {
          auto: "Auto",
          autoMax: "Auto MAX",
        })}
      </p>
    </div>
  )
}
