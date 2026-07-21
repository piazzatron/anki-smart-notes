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

const SITE_URL = "https://smart-notes.xyz"

export const SITE_LINKS = {
  account: `${SITE_URL}/account`,
  signIn: `${SITE_URL}/sign-in?utm_source=plugin`,
  startTrial: `${SITE_URL}/trial?utm_source=plugin`,
  upgrade: `${SITE_URL}/upgrade/sign-in?utm_source=plugin`,
} as const

export const openSiteLink = (url: string): void => {
  window.open(url, "_blank", "noopener,noreferrer")
}
