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
import { afterEach, expect, mock, test } from "bun:test"

import { useAppStore } from "@/store/appStore"
import type { AppState } from "@/types/api"

import { openSiteLink, SITE_LINKS } from "./siteLinks"

const originalStore = useAppStore.getState()

afterEach(() => {
  useAppStore.setState(originalStore, true)
  delete (globalThis as { window?: unknown }).window
})

test("site links carry the install ID, so the site joins this install's Amplitude user", () => {
  const open = mock()
  ;(globalThis as { window?: unknown }).window = { open }
  useAppStore.setState({
    state: { installId: "6f1c2a4e-8b3d-4f5a-9c7e-1d2b3a4c5e6f" } as AppState,
  })

  openSiteLink(SITE_LINKS.startTrial)

  const url = new URL(open.mock.calls[0][0] as string)
  expect(url.searchParams.get("utm_source")).toBe("plugin")
  expect(url.searchParams.get("install_id")).toBe(
    "6f1c2a4e-8b3d-4f5a-9c7e-1d2b3a4c5e6f",
  )
})
