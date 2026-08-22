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

export interface Catalog {
  [key: string]: string | Catalog
}
export type FlatCatalog = Record<string, string>

const PLURAL_SUFFIX = /_(zero|one|two|few|many|other)$/

export const flattenCatalog = (catalog: Catalog, prefix = ""): FlatCatalog =>
  Object.fromEntries(
    Object.entries(catalog).flatMap(([key, value]) => {
      const path = prefix === "" ? key : `${prefix}.${key}`
      return typeof value === "string"
        ? [[path, value]]
        : Object.entries(flattenCatalog(value, path))
    }),
  )

export const placeholders = (value: string): string[] =>
  [...value.matchAll(/{{[^{}]+}}|<\/?[A-Za-z][A-Za-z0-9]*>/g)]
    .map(([placeholder]) => placeholder)
    .sort()

export const sourceForLocale = (
  source: FlatCatalog,
  locale: string,
): FlatCatalog => {
  const pluralCategories = new Set(
    new Intl.PluralRules(locale).resolvedOptions().pluralCategories,
  )
  const localizedSource: FlatCatalog = {}

  for (const [key, value] of Object.entries(source)) {
    const match = key.match(PLURAL_SUFFIX)
    if (match === null) {
      localizedSource[key] = value
      continue
    }

    const baseKey = key.slice(0, -match[0].length)
    for (const category of pluralCategories) {
      const localizedKey = `${baseKey}_${category}`
      localizedSource[localizedKey] =
        source[localizedKey] ?? source[`${baseKey}_other`]
    }
  }

  return localizedSource
}
