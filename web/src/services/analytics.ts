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

import type { SmartField } from "@/types/api"

interface TrackSmartFieldActivationArgs {
  appVersion: string
  authToken: string | null
  fieldType: SmartField["fieldType"]
}

export const trackSmartFieldSaved = (
  args: TrackSmartFieldActivationArgs,
): Promise<void> => trackAnalyticsEvent({ ...args, event: "smart_field_saved" })

export const trackSmartFieldCompletionShown = (
  args: TrackSmartFieldActivationArgs,
): Promise<void> =>
  trackAnalyticsEvent({ ...args, event: "smart_field_completion_shown" })

interface TrackAnalyticsEventArgs extends TrackSmartFieldActivationArgs {
  event: "smart_field_saved" | "smart_field_completion_shown"
}

const trackAnalyticsEvent = async ({
  appVersion,
  authToken,
  event,
  fieldType,
}: TrackAnalyticsEventArgs): Promise<void> => {
  if (authToken === null) return

  await fetch(`${SERVER_URL}/api/events`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${authToken}`,
      "Content-Type": "application/json",
      "x-sn-plugin-version": appVersion,
      "x-sn-source": "anki-plugin",
    },
    body: JSON.stringify({
      event,
      properties: { field_type: fieldType },
    }),
  })
}

const SERVER_URL = import.meta.env.DEV
  ? "http://localhost:3003"
  : "https://api.smart-notes.xyz"
