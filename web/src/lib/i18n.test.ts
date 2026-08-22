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

import english from "../locales/en.json"
import { flattenCatalog, sourceForLocale, type Catalog } from "./catalogSchema"
import { LANGUAGES } from "./languages"
import { getLocaleDirection, matchCatalogLocale } from "./locale"

const placeholders = (value: string): string[] =>
  [...value.matchAll(/{{[^{}]+}}/g)].map(([placeholder]) => placeholder).sort()

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

  test.each(LANGUAGES.map((language) => [language] as const))(
    "$nativeName has a complete catalog",
    async ({ bcp47 }) => {
      const source =
        bcp47 === "en"
          ? flattenCatalog(english)
          : sourceForLocale(flattenCatalog(english), bcp47)
      const catalog = flattenCatalog(
        (await Bun.file(
          new URL(`../locales/${bcp47}.json`, import.meta.url),
        ).json()) as Catalog,
      )

      expect(Object.keys(catalog).sort()).toEqual(Object.keys(source).sort())
      for (const [key, value] of Object.entries(source)) {
        expect(placeholders(catalog[key])).toEqual(placeholders(value))
      }
    },
  )
})
