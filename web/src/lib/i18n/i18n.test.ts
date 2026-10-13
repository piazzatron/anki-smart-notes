/*
 * Copyright (C) 2024 Michael Piazza
 *
 * This file is part of Smart Notes.
 *
 * Smart Notes is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

import { describe, expect, test } from "bun:test"

import { sourceForLocale } from "./catalogSchema"
import { getLocaleDirection, matchCatalogLocale } from "./locale"

describe("locale selection", () => {
  test.each([
    ["pt-BR", "pt-BR"],
    ["pt_br", "pt-BR"],
    ["ja-JP", "ja"],
    ["en-GB", "en"],
    ["unknown", "en"],
  ] as const)("matches %s to %s", (requested, expected) => {
    expect(matchCatalogLocale(requested)).toBe(expected)
  })

  test("marks the supported RTL locales", () => {
    expect(getLocaleDirection("ar-SA")).toBe("rtl")
    expect(getLocaleDirection("he")).toBe("rtl")
    expect(getLocaleDirection("fa")).toBe("rtl")
    expect(getLocaleDirection("en")).toBe("ltr")
  })

  test("uses each locale's cardinal plural categories", () => {
    const source = { days_one: "{{count}} day", days_other: "{{count}} days" }

    expect(Object.keys(sourceForLocale(source, "pl")).sort()).toEqual([
      "days_few",
      "days_many",
      "days_one",
      "days_other",
    ])
    expect(Object.keys(sourceForLocale(source, "ja"))).toEqual(["days_other"])
  })
})
