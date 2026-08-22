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

import i18next from "i18next"
import { initReactI18next } from "react-i18next"

import { bootOptions } from "@/lib/boot"
import { catalogLoaders } from "@/lib/catalogLoaders"
import type { CatalogLocale } from "@/lib/languages"
import { getLocaleDirection, matchCatalogLocale } from "@/lib/locale"
import english from "@/locales/en.json"

const loadCatalog = async (locale: CatalogLocale) => {
  if (locale === "en" || i18next.hasResourceBundle(locale, "translation"))
    return

  const load = catalogLoaders[`../locales/${locale}.json`]
  if (load === undefined)
    throw new Error(`Missing translation catalog: ${locale}`)
  i18next.addResourceBundle(locale, "translation", (await load()).default)
}

const updateDocumentLocale = (locale: string) => {
  document.documentElement.lang = locale
  document.documentElement.dir = getLocaleDirection(locale)
}

export const initializeI18n = async () => {
  const locale = matchCatalogLocale(bootOptions.locale)
  await i18next.use(initReactI18next).init({
    fallbackLng: "en",
    lng: locale,
    resources: { en: { translation: english } },
    interpolation: { escapeValue: false },
  })
  await loadCatalog(locale)
  if (locale !== "en") await i18next.changeLanguage(locale)
  updateDocumentLocale(locale)
}

export const changeAppLanguage = async (requestedLocale: string) => {
  const locale = matchCatalogLocale(
    requestedLocale === "auto" ? bootOptions.ankiLocale : requestedLocale,
  )
  await loadCatalog(locale)
  await i18next.changeLanguage(locale)
  updateDocumentLocale(locale)
}

export default i18next
