/*
 * Copyright (C) 2024 Michael Piazza
 *
 * This file is part of Smart Notes.
 *
 * Smart Notes is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Smart Notes is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Smart Notes. If not, see <https://www.gnu.org/licenses/>.
 */

import { DirectionProvider } from "@radix-ui/react-direction"
import { useTranslation } from "react-i18next"

import App from "./App"
import { getLocaleDirection } from "@/lib/i18n/locale"

export const AppRoot = () => {
  const { i18n } = useTranslation()
  return (
    <DirectionProvider dir={getLocaleDirection(i18n.language)}>
      <App />
    </DirectionProvider>
  )
}
