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

import { CATALOG_LOCALES, type CatalogLocale } from "@/lib/languages"

const catalogLocaleSet = new Set<string>(CATALOG_LOCALES)
const RTL_LOCALES = new Set(["ar", "he", "fa"])

export const matchCatalogLocale = (requestedLocale: string): CatalogLocale => {
  const normalized = requestedLocale.replace("_", "-")
  const exact = CATALOG_LOCALES.find(
    (locale) => locale.toLowerCase() === normalized.toLowerCase(),
  )
  if (exact !== undefined) return exact

  const primary = normalized.split("-", 1)[0].toLowerCase()
  return catalogLocaleSet.has(primary) ? (primary as CatalogLocale) : "en"
}

export const getLocaleDirection = (locale: string): "ltr" | "rtl" =>
  RTL_LOCALES.has(locale.split("-", 1)[0]) ? "rtl" : "ltr"
