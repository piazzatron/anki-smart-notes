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

import { AnkiMark, GithubMark } from "@/components/shared/BrandMarks"
import { DiscordMark } from "@/components/shared/DiscordMark"
import { FeedbackDialog } from "@/components/shared/FeedbackDialog"
import { PageLayout } from "@/components/shared/PageLayout"
import { ScreenSkeleton } from "@/components/shared/ScreenSkeleton"
import { BugIcon, LetterIcon } from "@/components/shared/Icons"
import {
  ANKIWEB_REVIEW_URL,
  DISCORD_URL,
  SUPPORT_EMAIL,
} from "@/lib/helpChannels"
import { useAppStore } from "@/store/appStore"
import type { ReactNode } from "react"
import { useTranslation } from "react-i18next"

const REFERENCE_LINKS = [
  {
    href: `mailto:${SUPPORT_EMAIL}`,
    labelKey: "support.emailUs",
    mark: <LetterIcon className="text-zinc-300" size={22} />,
    sub: SUPPORT_EMAIL,
  },
  {
    href: ANKIWEB_REVIEW_URL,
    labelKey: "support.ankiWeb",
    mark: <AnkiMark />,
    subKey: "support.ankiWebDescription",
  },
  {
    href: "https://github.com/piazzatron/anki-smart-notes",
    labelKey: "support.github",
    mark: <GithubMark />,
    sub: undefined,
  },
]

export const SupportScreen = () => {
  const { t } = useTranslation()
  const state = useAppStore((store) => store.state)

  if (state === null)
    return (
      <ScreenSkeleton
        ariaLabel={t("support.loading")}
        className="max-w-[800px]"
        contentClassName="h-64"
        title={t("support.title")}
      />
    )

  return (
    <PageLayout
      className="max-w-[800px]"
      testId="support-screen"
      title={t("support.title")}
    >
      <div className="relative -mx-hang flex items-center gap-[15px] overflow-hidden rounded-[13px] bg-[linear-gradient(100deg,#3C45A5_0%,#5865F2_42%,#9B4DFF_100%)] py-[17px] ps-hang pe-4">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(460px_140px_at_10%_-40%,rgba(180,200,255,0.3),transparent_72%)]" />
        <DiscordMark className="relative text-white" size={31} />
        <div className="relative min-w-0 flex-1">
          <h2 className="text-base font-extrabold tracking-[-0.01em] text-white">
            {t("support.discord.title")}
          </h2>
          <p className="mt-[3px] text-[13.5px] text-white/80">
            {t("support.discord.description")}
          </p>
        </div>
        <a
          className="relative shrink-0 rounded-lg bg-white px-[22px] py-2.5 text-sm font-extrabold text-[#6B3FD4]"
          href={DISCORD_URL}
          rel="noreferrer"
          target="_blank"
        >
          {t("support.discord.join")}
        </a>
      </div>

      <div className="-mx-hang mt-[9px] flex items-center gap-[15px] rounded-[13px] bg-white/[0.05] py-4 ps-hang pe-4">
        <BugIcon className="text-zinc-300" size={26} />
        <div className="min-w-0 flex-1">
          <h2 className="text-base font-extrabold tracking-[-0.01em] text-zinc-100">
            {t("support.feedback.title")}
          </h2>
          <p className="mt-[3px] text-[13.5px] text-zinc-400">
            {t("support.feedback.description")}
          </p>
        </div>
        <FeedbackDialog>
          <button
            className="shrink-0 rounded-[9px] bg-[#5b6fe8] px-5 py-2.5 text-sm font-extrabold text-white"
            type="button"
          >
            {t("support.feedback.send")}
          </button>
        </FeedbackDialog>
      </div>

      <div className="-mx-hang mt-[9px] grid grid-cols-3 gap-[9px]">
        {REFERENCE_LINKS.map((link) => (
          <a
            className="flex min-w-0 items-center gap-3 rounded-[13px] bg-white/[0.05] px-hang py-3.5"
            href={link.href}
            key={link.labelKey}
            rel="noreferrer"
            target="_blank"
          >
            <span className="flex shrink-0" aria-hidden>
              {link.mark}
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-bold text-zinc-100">
                {t(link.labelKey)}
              </span>
              <span className="mt-0.5 block truncate text-[12.5px] text-zinc-400">
                {link.subKey === undefined ? link.sub : t(link.subKey)}
              </span>
            </span>
          </a>
        ))}
      </div>

      <footer className="mt-[18px] px-0.5">
        <p className="text-[13px] leading-[1.55] text-zinc-400">
          <a
            className="text-zinc-400 hover:text-zinc-200"
            href="https://smart-notes.xyz"
            rel="noreferrer"
            target="_blank"
          >
            {t("common.productName")}
          </a>{" "}
          {t("support.byline")}
        </p>
        <p className="mt-2.5 text-xs text-ink-muted">
          {t("support.copyright", { version: state.appVersion })}{" "}
          <a
            className="text-zinc-400 hover:text-zinc-200"
            href="https://docs.smart-notes.xyz"
            rel="noreferrer"
            target="_blank"
          >
            {t("support.changelog")}
          </a>
        </p>
        {/* Attribution names the artwork and its licenses, so it stays in English. */}
        {/* eslint-disable i18next/no-literal-string */}
        <p className="mt-1 text-xs text-ink-muted">
          Icons:{" "}
          <CreditLink href="https://www.figma.com/community/file/1166831539721848736">
            Solar
          </CreditLink>{" "}
          by 480 Design (
          <CreditLink href="https://creativecommons.org/licenses/by/4.0/">
            CC BY 4.0
          </CreditLink>
          ) ·{" "}
          <CreditLink href="https://github.com/googlefonts/noto-emoji">
            Noto Emoji
          </CreditLink>{" "}
          by Google (Apache 2.0)
        </p>
        {/* eslint-enable i18next/no-literal-string */}
      </footer>
    </PageLayout>
  )
}

const CreditLink = ({
  children,
  href,
}: {
  children?: ReactNode
  href: string
}) => (
  <a
    className="text-zinc-400 hover:text-zinc-200"
    href={href}
    rel="noreferrer"
    target="_blank"
  >
    {children}
  </a>
)
