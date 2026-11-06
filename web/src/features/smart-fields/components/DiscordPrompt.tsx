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

import { X } from "lucide-react"
import { useTranslation } from "react-i18next"

import { IconButton } from "@/components/ui/IconButton"
import { DiscordMark } from "@/components/shared/DiscordMark"
import { DISCORD_URL } from "@/lib/helpChannels"

interface DiscordPromptProps {
  onDismiss: () => void
}

export const DiscordPrompt = ({ onDismiss }: DiscordPromptProps) => {
  const { t } = useTranslation()

  return (
    <div
      // eslint-disable-next-line local/no-hex-color -- Discord's brand gradient
      className="relative -mx-hang mb-5 flex cursor-pointer items-center gap-3 overflow-hidden rounded-[13px] bg-[linear-gradient(100deg,#3C45A5_0%,#5865F2_42%,#9B4DFF_100%)] py-3.5 ps-hang pe-3.5 transition-transform duration-150 ease-out hover:scale-[1.006]"
    >
      <a
        aria-label={t("smartFields.discord.joinAriaLabel")}
        className="absolute inset-0 z-10 rounded-[13px]"
        href={DISCORD_URL}
        rel="noreferrer"
        target="_blank"
      />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(460px_140px_at_10%_-40%,rgba(180,200,255,0.3),transparent_72%)]" />
      <div aria-hidden className="banner-shine" />
      <DiscordMark className="relative text-white" size={23} />
      <p className="relative min-w-0 flex-1 text-[14px] leading-[1.35] font-semibold text-white">
        {t("smartFields.discord.title")}
        <span className="text-sm font-medium text-white/80">
          {" "}
          {t("smartFields.discord.subtitle")}
        </span>
      </p>
      <a
        // eslint-disable-next-line local/no-hex-color -- Discord's brand purple, on its banner's button
        className="relative z-20 inline-flex banner-button items-center bg-white text-[#6B3FD4] no-underline transition-transform duration-150 ease-out hover:scale-[1.035]"
        href={DISCORD_URL}
        rel="noreferrer"
        target="_blank"
      >
        {t("smartFields.discord.join")}
      </a>
      <IconButton
        aria-label={t("smartFields.discord.dismissAriaLabel")}
        onClick={onDismiss}
        tone="banner"
      >
        <X aria-hidden className="size-3.5" />
      </IconButton>
    </div>
  )
}
