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

import type { SmartField } from "@/types/api"

import { getDefaultUsage } from "./defaultUsage"

const textField = (
  id: string,
  usesDefaultGenerationSettings: boolean,
): SmartField => ({
  id,
  noteTypeId: 1,
  deckId: 1,
  targetFieldName: id,
  fieldType: "chat",
  enabled: true,
  settings: {
    promptText: "Define {{Front}}",
    provider: "auto",
    model: "auto",
    reasoningLevel: "off",
    webSearchEnabled: false,
    usesDefaultGenerationSettings,
  },
})

describe("Text Defaults", () => {
  test("counts fields following defaults separately from pinned fields", () => {
    expect(
      getDefaultUsage(
        [
          textField("one", true),
          textField("two", true),
          textField("three", false),
        ],
        "chat",
      ),
    ).toEqual({ following: 2, pinned: 1 })
  })
})
