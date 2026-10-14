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
  type FlatCatalog,
} from "../src/lib/i18n/catalogSchema"
import { LANGUAGES } from "../src/lib/i18n/languages"
import english from "../src/lib/i18n/locales/en.json"
import {
  findStaleEnglishKeys,
  pluralBase,
  readTranslationSources,
  writeTranslationSources,
} from "./translationSources"

const MODEL = "claude-haiku-5-5"
const RETRY_MODEL = "claude-sonnet-5-5"
const MAX_ATTEMPTS = 3
const CONCURRENCY = 8
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
    throw new Error("claude returned no JSON object")
  }
  return JSON.parse(response.slice(firstBrace, lastBrace + 1)) as FlatCatalog
}

// Keys whose translation keeps every {{placeholder}} and markup tag, the only things
// that break at runtime. Anything else in a reply is dropped and retried.
const validKeys = (source: FlatCatalog, translated: FlatCatalog) =>
  Object.keys(source).filter(
    (key) =>
      typeof translated[key] === "string" &&
      JSON.stringify(placeholders(translated[key])) ===
        JSON.stringify(placeholders(source[key])),
  )

const SYSTEM_PROMPT =
  "You translate UI copy for Smart Notes, an Anki add-on. Return only one JSON object with exactly the input keys. Preserve every {{placeholder}} and component markup tag byte-for-byte. Never translate the product terms Smart Notes, Smart Fields, Anki, provider names, or model names; if grammar would inflect one, rephrase so it appears exactly as written. Match the source sentence casing and keep the tone concise and natural for software UI."

// Runs on the developer's Claude Code login through `claude -p`, so no API key is
// needed. No tools, MCP servers or settings files (and so no hooks): each call is a
// single model turn.
const translate = async (
  language: (typeof targetLanguages)[number],
  source: FlatCatalog,
  model: string,
): Promise<FlatCatalog> => {
  const claude = Bun.spawn(
    [
      "claude",
      "-p",
      "--model",
      model,
      "--system-prompt",
      SYSTEM_PROMPT,
      "--tools",
      "",
      "--strict-mcp-config",
      "--setting-sources",
      "",
      "--no-session-persistence",
      "--output-format",
      "json",
    ],
    {
      stdin: new TextEncoder().encode(
        `Translate this JSON from English to ${language.nativeName} (${language.bcp47}):\n${JSON.stringify(source, null, 2)}`,
      ),
      stdout: "pipe",
      stderr: "pipe",
    },
  )
  const [stdout, stderr, exitCode] = await Promise.all([
    new Response(claude.stdout).text(),
    new Response(claude.stderr).text(),
    claude.exited,
  ])
  if (exitCode !== 0) {
    throw new Error(`claude exited with ${exitCode}: ${stderr.trim()}`)
  }
  const { result, is_error } = JSON.parse(stdout) as {
    result: string
    is_error: boolean
  }
  if (is_error) throw new Error(`claude returned an error: ${result}`)
  return extractJson(result)
}

const englishSource = flattenCatalog(english)
const staleBases = new Set(
  findStaleEnglishKeys(englishSource, await readTranslationSources()).map(
    pluralBase,
  ),
)

// Translates a locale's missing and stale strings, retrying only the strings a reply
// got wrong. Returns the keys that still failed; they are left out of the file so the
// next run picks them up as missing.
const translateLocale = async (
  language: (typeof targetLanguages)[number],
): Promise<string[]> => {
  const source = sourceForLocale(englishSource, language.bcp47)
  const existing =
    forcedLocale === language.bcp47 ? {} : await readCatalog(language.bcp47)
  const preserved = Object.fromEntries(
    Object.keys(source)
      .filter((key) => key in existing && !staleBases.has(pluralBase(key)))
      .map((key) => [key, existing[key]]),
  )
  let pending = Object.fromEntries(
    Object.entries(source).filter(([key]) => !(key in preserved)),
  )
  const requested = Object.keys(pending).length
  const translated: FlatCatalog = {}

  for (
    let attempt = 1;
    attempt <= MAX_ATTEMPTS && Object.keys(pending).length > 0;
    attempt++
  ) {
    try {
      const reply = await translate(
        language,
        pending,
        attempt === 1 ? MODEL : RETRY_MODEL,
      )
      for (const key of validKeys(pending, reply)) translated[key] = reply[key]
    } catch (error) {
      console.warn(`${language.bcp47}: attempt ${attempt} failed: ${error}`)
    }
    pending = Object.fromEntries(
      Object.entries(pending).filter(([key]) => !(key in translated)),
    )
  }

  // Write in English key order so diffs show only real changes.
  const merged: FlatCatalog = { ...preserved, ...translated }
  const ordered = Object.fromEntries(
    Object.keys(source)
      .filter((key) => key in merged)
      .map((key) => [key, merged[key]]),
  )
  await Bun.write(
    new URL(`${language.bcp47}.json`, LOCALES_DIRECTORY),
    `${JSON.stringify(buildCatalog(ordered), null, 2)}\n`,
  )
  console.log(
    `${language.bcp47}: translated ${requested - Object.keys(pending).length}/${requested} strings`,
  )
  return Object.keys(pending)
}

const queue = targetLanguages.filter(
  ({ bcp47 }) => forcedLocale === null || bcp47 === forcedLocale,
)
const failures: string[] = []
await Promise.all(
  Array.from({ length: CONCURRENCY }, async () => {
    for (let language = queue.shift(); language; language = queue.shift()) {
      const failed = await translateLocale(language)
      if (failed.length > 0)
        failures.push(`${language.bcp47}: ${failed.join(", ")}`)
    }
  }),
)

// Strings that failed are missing from their locale files rather than stale, so the
// next run retries just those even though the English is now recorded as current.
if (forcedLocale === null) await writeTranslationSources(englishSource)

if (failures.length > 0) {
  console.error("\nCould not translate:")
  for (const failure of failures) console.error(`  ${failure}`)
  console.error("\nRun `bun run translate` again to retry just these.")
  process.exit(1)
}
