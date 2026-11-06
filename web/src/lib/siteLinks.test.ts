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
import { expect, test } from "bun:test"

import { SITE_LINKS, withInstallId } from "./siteLinks"

test("site links carry the install ID, so the site joins this install's Amplitude user", () => {
  const url = new URL(
    withInstallId(
      SITE_LINKS.startTrial,
      "6f1c2a4e-8b3d-4f5a-9c7e-1d2b3a4c5e6f",
    ),
  )

  expect(url.searchParams.get("utm_source")).toBe("plugin")
  expect(url.searchParams.get("install_id")).toBe(
    "6f1c2a4e-8b3d-4f5a-9c7e-1d2b3a4c5e6f",
  )
})
