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

import english from "@/locales/en.json"

type CatalogModule = { default: typeof english }

export const catalogLoaders = import.meta.glob<CatalogModule>(
  "../locales/*.json",
)
