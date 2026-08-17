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

import type { Catalog, ChatGenerationSettings } from "@/types/api"

import { TextModelSettings } from "./TextModelSettings"

const catalog: Catalog = {
  chat: {
    providers: ["auto", "openai"],
    models: [
      { id: "auto", provider: "auto" },
      { id: "gpt-5-mini", provider: "openai" },
    ],
    reasoningLevels: ["off", "low", "high"],
  },
  image: { providers: [], models: [] },
}

const defaults: ChatGenerationSettings = {
  provider: "auto",
  model: "auto",
  reasoningLevel: "off",
  webSearchEnabled: false,
}

describe("TextModelSettings", () => {
  test("presents the selected catalog model and model guidance", () => {
    const markup = renderSettings(defaults)

    expect(markup).toContain('aria-label="Text model"')
    expect(markup).toContain('role="combobox"')
    expect(markup).toContain("Picking a model")
  })

  test("shows custom Auto controls with the shared reasoning select", () => {
    const markup = renderSettings({ ...defaults })

    expect(markup).toContain("text-indigo-soft")
    expect(markup).toContain('aria-label="Reasoning level"')
    expect(markup).toContain('role="combobox"')
    expect(markup).toContain('aria-label="Use web search for this field"')
  })

  test("hides reasoning for pinned models that do not support it", () => {
    const markup = renderSettings({
      ...defaults,
      provider: "openai",
      model: "gpt-5-mini",
    })

    expect(markup).not.toContain('aria-label="Reasoning level"')
    expect(markup).toContain('aria-label="Use web search for this field"')
  })
})

const renderSettings = (value: ChatGenerationSettings): string =>
  renderToStaticMarkup(
    <TextModelSettings
      catalog={catalog.chat}
      onChange={() => undefined}
      value={value}
    />,
  )
