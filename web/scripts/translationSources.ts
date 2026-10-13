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

import { createHash } from "node:crypto"

import { PLURAL_SUFFIX, type FlatCatalog } from "../src/lib/i18n/catalogSchema"

// The English text every locale was last translated from, as a short hash per key.
// `translate` rewrites it after a full run; `checkTranslations` fails when English has
// changed since, so a reworded string can't ship with its old translations.
const TRANSLATION_SOURCES_FILE = new URL(
  "./translationSources.json",
  import.meta.url,
)

export const hashEnglish = (value: string) =>
  createHash("sha256").update(value).digest("hex").slice(0, 12)

export const readTranslationSources = async (): Promise<FlatCatalog> =>
  (await Bun.file(TRANSLATION_SOURCES_FILE).json()) as FlatCatalog

export const writeTranslationSources = async (english: FlatCatalog) => {
  const sources = Object.fromEntries(
    Object.entries(english).map(([key, value]) => [key, hashEnglish(value)]),
  )
  await Bun.write(
    TRANSLATION_SOURCES_FILE,
    `${JSON.stringify(sources, null, 2)}\n`,
  )
}

// English keys that are new or reworded since the locales were last translated.
export const findStaleEnglishKeys = (
  english: FlatCatalog,
  sources: FlatCatalog,
) =>
  Object.keys(english).filter(
    (key) => sources[key] !== hashEnglish(english[key]),
  )

// Locales have different plural categories, so a stale plural form makes every form of
// that word stale.
export const pluralBase = (key: string) => key.replace(PLURAL_SUFFIX, "")
