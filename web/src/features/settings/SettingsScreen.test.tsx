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
import { renderToStaticMarkup } from "react-dom/server"

import type { Settings } from "@/types/api"

import { LoadedSettingsScreen } from "./SettingsScreen"

const SETTINGS: Settings = {
  generateAtReview: true,
  regenerateWhenBatching: false,
  debug: false,
  legacyOpenAiEnabled: false,
  legacyOpenAiKey: null,
  legacyOpenAiModel: "gpt-5-mini",
  legacyOpenAiHost: null,
  showWizardCompletion: true,
  didDismissDiscordPrompt: false,
}

test("legacy OpenAI settings require legacy support", () => {
  expect(
    renderToStaticMarkup(<LoadedSettingsScreen settings={SETTINGS} />),
  ).not.toContain("Use my own OpenAI key")

  expect(
    renderToStaticMarkup(
      <LoadedSettingsScreen
        settings={{ ...SETTINGS, legacyOpenAiEnabled: true }}
      />,
    ),
  ).toContain("Use my own OpenAI key")
})
