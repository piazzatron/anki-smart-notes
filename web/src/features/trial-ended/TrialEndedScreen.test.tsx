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

import { describe, expect, test } from "bun:test"
import { renderToStaticMarkup } from "react-dom/server"

import { TrialEndedScreen } from "./TrialEndedScreen"

describe("TrialEndedScreen", () => {
  test("always shows the upgrade CTA", () => {
    const markup = renderToStaticMarkup(
      <TrialEndedScreen reviewFreeMonthEnabled={false} />,
    )

    expect(markup).toContain("Your free trial has ended")
    expect(markup).toContain("Upgrade now")
  })

  test("shows the review offer only when its feature flag is enabled", () => {
    expect(
      renderToStaticMarkup(<TrialEndedScreen reviewFreeMonthEnabled={false} />),
    ).not.toContain("Get a free month of Smart Notes")
    expect(
      renderToStaticMarkup(<TrialEndedScreen reviewFreeMonthEnabled={true} />),
    ).toContain("Get a free month of Smart Notes")
  })
})
