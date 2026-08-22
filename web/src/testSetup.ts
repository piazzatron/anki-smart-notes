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

import { mock } from "bun:test"
import i18next from "i18next"
import { initReactI18next } from "react-i18next"

import english from "@/lib/i18n/locales/en.json"

mock.module("@/lib/i18n/catalogLoaders", () => ({ catalogLoaders: {} }))

void i18next.use(initReactI18next).init({
  fallbackLng: "en",
  initAsync: false,
  lng: "en",
  resources: { en: { translation: english } },
  interpolation: { escapeValue: false },
})
