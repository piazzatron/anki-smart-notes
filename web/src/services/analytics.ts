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

import { useAppStore } from "@/store/appStore"
import type { SmartField } from "@/types/api"

export type AnalyticsEvent =
  | {
      event: "smart_field_saved"
      properties: { field_type: SmartField["fieldType"] }
    }
  | {
      event: "smart_field_completion_shown"
      properties: { field_type: SmartField["fieldType"] }
    }

export const trackAnalyticsEvent = async (
  event: AnalyticsEvent,
): Promise<void> => {
  const state = useAppStore.getState().state
  if (state === null || state.account.authToken === null) return

  try {
    const response = await fetch(`${SERVER_URL}/api/events`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${state.account.authToken}`,
        "Content-Type": "application/json",
        "x-sn-plugin-version": state.appVersion,
        "x-sn-source": "anki-plugin",
      },
      body: JSON.stringify(event),
    })

    if (!response.ok) {
      console.debug("Analytics event request failed", {
        event: event.event,
        status: response.status,
      })
    }
  } catch (error) {
    console.debug("Analytics event request failed", {
      error,
      event: event.event,
    })
  }
}

const SERVER_URL = import.meta.env.DEV
  ? "http://localhost:3003"
  : "https://api.smart-notes.xyz"
