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

import { useAppStore } from "@/store/appStore"

const SITE_URL = import.meta.env.DEV
  ? "http://localhost:3001"
  : "https://smart-notes.xyz"

export const SITE_LINKS = {
  account: `${SITE_URL}/account`,
  signIn: `${SITE_URL}/sign-in?utm_source=plugin`,
  startTrial: `${SITE_URL}/trial?utm_source=plugin`,
  topUp: `${SITE_URL}/top-up?utm_source=plugin`,
  upgrade: `${SITE_URL}/upgrade/sign-in?utm_source=plugin`,
} as const

/** Opens a site page in the browser, carrying the install ID so the site's Amplitude session joins this install's. */
export const openSiteLink = (url: string): void => {
  const installId = useAppStore.getState().state?.installId
  const link = new URL(url)
  if (installId) link.searchParams.set("install_id", installId)
  window.open(link.toString(), "_blank", "noopener,noreferrer")
}
