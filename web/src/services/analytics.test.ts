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

import { afterEach, describe, expect, mock, test } from "bun:test"

import {
  trackSmartFieldCompletionShown,
  trackSmartFieldSaved,
} from "./analytics"

const originalFetch = global.fetch

afterEach(() => {
  global.fetch = originalFetch
})

describe("Smart Field activation analytics", () => {
  test.each([
    {
      expectedEvent: "smart_field_saved",
      fieldType: "chat" as const,
      track: trackSmartFieldSaved,
    },
    {
      expectedEvent: "smart_field_completion_shown",
      fieldType: "tts" as const,
      track: trackSmartFieldCompletionShown,
    },
  ])(
    "posts $expectedEvent to the authenticated Smart Notes event endpoint",
    async ({ expectedEvent, fieldType, track }) => {
      const requests: Array<{ init: RequestInit; url: string }> = []
      global.fetch = mock(async (url: string, init: RequestInit) => {
        requests.push({ init, url })
        return new Response(null, { status: 204 })
      }) as unknown as typeof fetch

      await track({
        appVersion: "2.24.0",
        authToken: "plugin-jwt",
        fieldType,
      })

      expect(requests).toHaveLength(1)
      const [{ init, url }] = requests
      expect(url).toBe("https://api.smart-notes.xyz/api/events")
      expect(init.method).toBe("POST")
      expect(new Headers(init.headers)).toEqual(
        new Headers({
          Authorization: "Bearer plugin-jwt",
          "Content-Type": "application/json",
          "x-sn-plugin-version": "2.24.0",
          "x-sn-source": "anki-plugin",
        }),
      )
      expect(JSON.parse(init.body as string)).toEqual({
        event: expectedEvent,
        properties: { field_type: fieldType },
      })
    },
  )

  test("does nothing when the user is signed out", async () => {
    const fetchMock = mock(async () => new Response(null, { status: 204 }))
    global.fetch = fetchMock as unknown as typeof fetch

    await trackSmartFieldSaved({
      appVersion: "2.24.0",
      authToken: null,
      fieldType: "image",
    })

    expect(fetchMock).not.toHaveBeenCalled()
  })
})
