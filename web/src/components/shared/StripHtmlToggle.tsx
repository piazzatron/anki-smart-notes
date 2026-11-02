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

import { useId } from "react"
import { useTranslation } from "react-i18next"

import { InfoTip } from "@/components/ui/InfoTip"
import { Toggle } from "@/components/ui/Toggle"

interface StripHtmlToggleProps {
  checked: boolean
  /** Hangs past the column by its own padding (see TextModelPicker). */
  hanging?: boolean
  onCheckedChange: (checked: boolean) => void
}

/** The "Strip HTML from input" switch, as a row under Advanced options. */
export const StripHtmlToggle = ({
  checked,
  hanging = false,
  onCheckedChange,
}: StripHtmlToggleProps) => {
  const { t } = useTranslation()
  const labelId = useId()

  return (
    <div
      className={`flex items-center gap-4 rounded-xl bg-white/[0.05] py-[18px] ${hanging ? "hang" : "px-hang"}`}
    >
      <p className="flex min-h-[22px] min-w-0 flex-1 items-center gap-2 text-sm font-medium text-ink">
        <span id={labelId}>{t("stripHtml.label")}</span>
        <InfoTip label={t("stripHtml.tipLabel")}>
          {t("stripHtml.description")}
        </InfoTip>
      </p>
      <Toggle
        aria-labelledby={labelId}
        checked={checked}
        onCheckedChange={onCheckedChange}
      />
    </div>
  )
}
