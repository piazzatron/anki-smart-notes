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

import { useEffect, useRef, useState } from "react"

import { errorMessage } from "@/lib/errors"
import { previewTTSVoice } from "@/services/commands"
import type { VoiceCatalogItem } from "@/types/api"

import { previewTextForLanguage, voiceKey } from "./voiceDefaults"

interface VoicePreviewState {
  error: string | null
  loadingKey: string | null
}

export const useVoicePreview = () => {
  const [state, setState] = useState<VoicePreviewState>({
    error: null,
    loadingKey: null,
  })
  const previewAudio = useRef<HTMLAudioElement | null>(null)

  useEffect(
    () => () => {
      previewAudio.current?.pause()
    },
    [],
  )

  const preview = async (voice: VoiceCatalogItem) => {
    previewAudio.current?.pause()
    setState({ error: null, loadingKey: voiceKey(voice) })
    try {
      const result = await previewTTSVoice({
        text: previewTextForLanguage(voice.language),
        settings: {
          provider: voice.provider,
          model: voice.model,
          voiceId: voice.voiceId,
        },
      })
      previewAudio.current = new Audio(result.dataUrl)
      await previewAudio.current.play()
    } catch (error) {
      setState({
        error: errorMessage(error, "Could not preview this voice"),
        loadingKey: null,
      })
      return
    }
    setState({ error: null, loadingKey: null })
  }

  return {
    dismissError: () => setState((current) => ({ ...current, error: null })),
    error: state.error,
    loadingKey: state.loadingKey,
    preview,
  }
}
