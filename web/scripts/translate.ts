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

import Anthropic from "@anthropic-ai/sdk"

import {
  flattenCatalog,
  placeholders,
  sourceForLocale,
  type Catalog,
  type FlatCatalog,
} from "../src/lib/i18n/catalogSchema"
import { LANGUAGES } from "../src/lib/i18n/languages"
import english from "../src/lib/i18n/locales/en.json"

const MODEL = "claude-haiku-4-5-20251001"
const LOCALES_DIRECTORY = new URL("../src/lib/i18n/locales/", import.meta.url)
const forceIndex = process.argv.indexOf("--force")
const forcedLocale = forceIndex === -1 ? null : process.argv[forceIndex + 1]
const targetLanguages = LANGUAGES.filter(({ bcp47 }) => bcp47 !== "en")

if (forceIndex !== -1 && forcedLocale === undefined) {
  throw new Error("Usage: bun run translate --force <language>")
}
if (
  forcedLocale !== null &&
  !targetLanguages.some(({ bcp47 }) => bcp47 === forcedLocale)
) {
  throw new Error(`Unsupported translation locale: ${forcedLocale}`)
}

const buildCatalog = (flatCatalog: FlatCatalog): Catalog => {
  const catalog: Catalog = {}
  for (const [path, value] of Object.entries(flatCatalog)) {
    const parts = path.split(".")
    let current = catalog
    for (const part of parts.slice(0, -1)) {
      const next = current[part]
      if (typeof next === "string")
        throw new Error(`Catalog path collision: ${path}`)
      current = next ?? (current[part] = {})
    }
    current[parts.at(-1)!] = value
  }
  return catalog
}

const readCatalog = async (locale: string): Promise<FlatCatalog> => {
  const file = Bun.file(new URL(`${locale}.json`, LOCALES_DIRECTORY))
  if (!(await file.exists())) return {}
  return flattenCatalog((await file.json()) as Catalog)
}

const extractJson = (response: string): FlatCatalog => {
  const firstBrace = response.indexOf("{")
  const lastBrace = response.lastIndexOf("}")
  if (firstBrace === -1 || lastBrace === -1) {
    throw new Error("Claude returned no JSON object")
  }
  return JSON.parse(response.slice(firstBrace, lastBrace + 1)) as FlatCatalog
}

const PROTECTED_TERMS = [
  "Smart Notes",
  "Smart Fields",
  "Anki",
  "OpenAI",
  "GPT Image",
  "Auto MAX",
]

const validateTranslations = (
  locale: string,
  source: FlatCatalog,
  translated: FlatCatalog,
) => {
  if (
    Object.keys(translated).length !== Object.keys(source).length ||
    Object.keys(source).some((key) => !(key in translated))
  ) {
    throw new Error(`${locale}: translated keys do not match source keys`)
  }
  for (const [key, value] of Object.entries(source)) {
    if (
      JSON.stringify(placeholders(value)) !==
      JSON.stringify(placeholders(translated[key]))
    ) {
      throw new Error(`${locale}: placeholders changed for ${key}`)
    }
    for (const term of PROTECTED_TERMS) {
      if (value.includes(term) && !translated[key].includes(term)) {
        throw new Error(`${locale}: protected term ${term} changed for ${key}`)
      }
    }
  }
}

const translate = async (
  language: (typeof targetLanguages)[number],
  source: FlatCatalog,
): Promise<FlatCatalog> => {
  const response = await new Anthropic().messages
    .stream({
      model: MODEL,
      max_tokens: 32_000,
      system:
        "You translate UI copy for Smart Notes, an Anki add-on. Return only one JSON object with exactly the input keys. Preserve every {{placeholder}} and component markup tag byte-for-byte. Never translate the product terms Smart Notes, Smart Fields, Anki, provider names, or model names. Match the source sentence casing and keep the tone concise and natural for software UI.",
      messages: [
        {
          role: "user",
          content: `Translate this JSON from English to ${language.nativeName} (${language.bcp47}):\n${JSON.stringify(source, null, 2)}`,
        },
      ],
    })
    .finalMessage()
  const text = response.content
    .filter((block) => block.type === "text")
    .map((block) => block.text)
    .join("")
  const translated = extractJson(text)

  validateTranslations(language.bcp47, source, translated)
  return translated
}

const englishSource = flattenCatalog(english)
for (const language of targetLanguages) {
  if (forcedLocale !== null && language.bcp47 !== forcedLocale) continue

  const source = sourceForLocale(englishSource, language.bcp47)
  const existing =
    forcedLocale === language.bcp47 ? {} : await readCatalog(language.bcp47)
  const preserved = Object.fromEntries(
    Object.keys(source)
      .filter((key) => key in existing)
      .map((key) => [key, existing[key]]),
  )
  const missing = Object.fromEntries(
    Object.entries(source).filter(([key]) => !(key in preserved)),
  )
  const translated =
    Object.keys(missing).length === 0 ? {} : await translate(language, missing)
  const completeCatalog = { ...preserved, ...translated }
  validateTranslations(language.bcp47, source, completeCatalog)

  await Bun.write(
    new URL(`${language.bcp47}.json`, LOCALES_DIRECTORY),
    `${JSON.stringify(buildCatalog(completeCatalog), null, 2)}\n`,
  )
  console.log(
    `${language.bcp47}: translated ${Object.keys(missing).length} strings`,
  )
}
