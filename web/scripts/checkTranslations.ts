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

import {
  flattenCatalog,
  placeholders,
  sourceForLocale,
  type Catalog,
} from "../src/lib/i18n/catalogSchema"
import { LANGUAGES } from "../src/lib/i18n/languages"
import englishCatalog from "../src/lib/i18n/locales/en.json"
import {
  findStaleEnglishKeys,
  readTranslationSources,
} from "./translationSources"

// Fails when any locale is missing a string, has one English no longer has, breaks a
// placeholder, or was translated from English that has since changed, and when English
// has a string no code reads.
const english = flattenCatalog(englishCatalog)
const problems: string[] = []

const staleKeys = findStaleEnglishKeys(english, await readTranslationSources())
if (staleKeys.length > 0) {
  problems.push(
    `English is new or changed since the last translation: ${staleKeys.join(", ")}`,
  )
}

for (const { bcp47 } of LANGUAGES) {
  if (bcp47 === "en") continue

  const source = sourceForLocale(english, bcp47)
  const catalog = flattenCatalog(
    (await Bun.file(
      new URL(`../src/lib/i18n/locales/${bcp47}.json`, import.meta.url),
    ).json()) as Catalog,
  )
  const missing = Object.keys(source).filter((key) => !(key in catalog))
  const extra = Object.keys(catalog).filter((key) => !(key in source))
  const brokenPlaceholders = Object.keys(source).filter(
    (key) =>
      key in catalog &&
      JSON.stringify(placeholders(catalog[key])) !==
        JSON.stringify(placeholders(source[key])),
  )

  if (missing.length > 0)
    problems.push(`${bcp47} is missing: ${missing.join(", ")}`)
  if (extra.length > 0)
    problems.push(`${bcp47} has removed keys: ${extra.join(", ")}`)
  if (brokenPlaceholders.length > 0) {
    problems.push(
      `${bcp47} placeholders differ from English: ${brokenPlaceholders.join(", ")}`,
    )
  }
}

// English keys no source file reads. A key counts as read when its quoted name appears
// in src/, or when it starts with the static head of a template key like
// `upgradeSheet.features.${feature}.title`. Plural forms (`_one`, `_other`) count as
// their base key.
const sources = await Promise.all(
  [
    ...new Bun.Glob("src/**/*.{ts,tsx}").scanSync(
      new URL("..", import.meta.url).pathname,
    ),
  ].map((path) => Bun.file(new URL(`../${path}`, import.meta.url)).text()),
)
const sourceText = sources.join("\n")
const dynamicPrefixes = [
  ...sourceText.matchAll(/`([A-Za-z][\w]*(?:\.[\w]+)*\.)\$\{/g),
].map(([, prefix]) => prefix)
const unusedKeys = Object.keys(english).filter((key) => {
  const base = key.replace(/_(zero|one|two|few|many|other)$/, "")
  return (
    !new RegExp(`["'\`]${base.replaceAll(".", "\\.")}["'\`]`).test(
      sourceText,
    ) && !dynamicPrefixes.some((prefix) => base.startsWith(prefix))
  )
})
if (unusedKeys.length > 0) {
  problems.push(
    `en.json has keys no source file reads; remove them: ${unusedKeys.join(", ")}`,
  )
}

if (problems.length > 0) {
  for (const problem of problems) console.error(problem)
  // translate fixes the locales; an unused key is removed from en.json by hand.
  if (unusedKeys.length < problems.length)
    console.error("\nRun `bun run translate` to fix.")
  process.exit(1)
}
console.log("Translations are complete and current.")
