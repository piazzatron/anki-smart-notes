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

import * as amplitude from "@amplitude/analytics-browser"
import { sessionReplayPlugin } from "@amplitude/plugin-session-replay-browser"

// The production project's browser key. Browser keys are public: the site ships the same one.
const AMPLITUDE_KEY = "471123b7b0e6f2dc0b7357ba6e111cbb"

let initialized = false

/**
 * Starts Session Replay for the web UI in production builds, with all text and
 * inputs masked and media blocked, because the UI shows users' own prompts and
 * note content. The install ID is the device ID and the email the user ID, so
 * replays join the same Amplitude user as the server's events. Later calls only
 * update the user ID: the install ID never changes.
 */
export const syncAmplitudeIdentity = ({
  installId,
  email,
}: {
  installId: string
  email: string | null
}): void => {
  if (import.meta.env.DEV) return

  if (initialized) {
    amplitude.setUserId(email ?? undefined)
    return
  }

  amplitude.add(
    sessionReplayPlugin({
      sampleRate: 1,
      // Text masking also comes from data-amp-mask on <body> (index.html),
      // which no mask level set in Amplitude's dashboard can override
      privacyConfig: {
        defaultMaskLevel: "conservative",
        // Attributes are only masked when listed. aria-labels and radio values
        // carry field and note type names.
        maskAttributes: ["aria-label", "title", "value", "placeholder", "alt"],
        blockSelector: ["img", "audio", "video"],
      },
    }),
  )
  amplitude.init(AMPLITUDE_KEY, email ?? undefined, {
    deviceId: installId,
    fetchRemoteConfig: false,
    // Precision events go through the server; autocapture only adds the
    // sessions that replays hang off
    autocapture: {
      attribution: false,
      pageViews: false,
      sessions: true,
      formInteractions: false,
      fileDownloads: false,
      elementInteractions: false,
    },
  })
  initialized = true
}
