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

const MODEL = "claude-sonnet-4-5-20250929"
const TRANSLATION_TOOL_NAME = "submit_translations"
const TRANSLATION_BATCH_SIZE = 10
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
      throw new Error(
        `${locale}: placeholders changed for ${key}: ${JSON.stringify(translated[key])}`,
      )
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
  const entriesWithProtectedLiterals = Object.entries(source).map(
    ([key, value]) => {
      let protectedValue = value
      const protectedTokens: Array<[string, string]> = []
      for (const [index, placeholder] of placeholders(value).entries()) {
        const token = `__SN_PLACEHOLDER_${index}__`
        protectedValue = protectedValue.replace(placeholder, token)
        protectedTokens.push([token, placeholder])
      }
      for (const term of PROTECTED_TERMS) {
        while (protectedValue.includes(term)) {
          const token = `__SN_TERM_${protectedTokens.length}__`
          protectedValue = protectedValue.replace(term, token)
          protectedTokens.push([token, term])
        }
      }
      return { key, protectedValue, protectedTokens }
    },
  )
  const response = await new Anthropic().messages.create({
    model: MODEL,
    max_tokens: 1_024,
    system:
      "You translate UI copy for Smart Notes, an Anki add-on. Call submit_translations exactly once with every input key translated. Preserve every {{placeholder}} and component markup tag byte-for-byte. Never translate the product terms Smart Notes, Smart Fields, Anki, provider names, or model names. Match the source sentence casing and keep the tone concise and natural for software UI.",
    tools: [
      {
        name: TRANSLATION_TOOL_NAME,
        description: "Submit the translated UI catalog.",
        strict: true,
        input_schema: {
          type: "object",
          properties: Object.fromEntries(
            entriesWithProtectedLiterals.map(({ key }) => [
              key,
              { type: "string" },
            ]),
          ),
          required: entriesWithProtectedLiterals.map(({ key }) => key),
          additionalProperties: false,
        },
      },
    ],
    tool_choice: { type: "tool", name: TRANSLATION_TOOL_NAME },
    messages: [
      {
        role: "user",
        content: `Translate these English UI strings to ${language.nativeName} (${language.bcp47}). Preserve every __SN_PLACEHOLDER_N__ and __SN_TERM_N__ token exactly; the script will restore the original placeholder, markup, or product term afterward:\n${JSON.stringify(
          entriesWithProtectedLiterals.map(({ key, protectedValue }) => ({
            key,
            value: protectedValue,
          })),
          null,
          2,
        )}`,
      },
    ],
  })
  const toolUse = response.content.find(
    (block) =>
      block.type === "tool_use" && block.name === TRANSLATION_TOOL_NAME,
  )
  if (toolUse?.type !== "tool_use") {
    throw new Error("Claude returned no translation tool call")
  }
  const input = toolUse.input as FlatCatalog
  const translated = Object.fromEntries(
    entriesWithProtectedLiterals.map(({ key, protectedTokens }) => {
      let value = input[key]
      for (const [token, original] of protectedTokens) {
        value = value.replace(token, original)
      }
      return [key, value]
    }),
  )

  validateTranslations(language.bcp47, source, translated)
  return translated
}

const translateInBatches = async (
  language: (typeof targetLanguages)[number],
  source: FlatCatalog,
): Promise<FlatCatalog> => {
  const entries = Object.entries(source)
  const translated: FlatCatalog = {}

  for (let index = 0; index < entries.length; index += TRANSLATION_BATCH_SIZE) {
    console.log(
      `${language.bcp47}: translating ${Math.min(index + TRANSLATION_BATCH_SIZE, entries.length)}/${entries.length} strings`,
    )
    Object.assign(
      translated,
      await translate(
        language,
        Object.fromEntries(
          entries.slice(index, index + TRANSLATION_BATCH_SIZE),
        ),
      ),
    )
  }

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
    Object.keys(missing).length === 0
      ? {}
      : await translateInBatches(language, missing)
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
