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

import { Pause, Play } from "lucide-react"
import { useRef, useState } from "react"

interface AudioPlayerProps {
  autoPlay?: boolean
  dataUrl: string
  label?: string
}

export const AudioPlayer = ({
  autoPlay = false,
  dataUrl,
  label = "Voice preview",
}: AudioPlayerProps) => {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [duration, setDuration] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)

  const toggle = async () => {
    const audio = audioRef.current
    if (audio === null) return
    if (audio.paused) await audio.play()
    else audio.pause()
  }

  return (
    <div className="flex items-center gap-3 rounded-lg border border-white/[0.08] bg-black/20 p-2.5">
      <audio
        autoPlay={autoPlay}
        onEnded={() => setIsPlaying(false)}
        onLoadedMetadata={(event) => setDuration(event.currentTarget.duration)}
        onPause={() => setIsPlaying(false)}
        onPlay={() => setIsPlaying(true)}
        ref={audioRef}
        src={dataUrl}
      />
      <button
        aria-label={isPlaying ? `Pause ${label}` : `Play ${label}`}
        className="flex size-8 shrink-0 cursor-pointer items-center justify-center rounded-full border border-indigo/35 bg-indigo/15 text-indigo-soft transition hover:bg-indigo/25"
        onClick={() => void toggle()}
      >
        {isPlaying ? (
          <Pause aria-hidden className="size-3.5 fill-current" />
        ) : (
          <Play aria-hidden className="ml-0.5 size-3.5 fill-current" />
        )}
      </button>
      <p className="min-w-0 flex-1 truncate text-xs font-semibold text-zinc-200">
        {label}
      </p>
      <span className="shrink-0 font-mono text-[10.5px] text-ink-faint">
        {formatDuration(duration)}
      </span>
    </div>
  )
}

const formatDuration = (seconds: number) => {
  if (!Number.isFinite(seconds)) return "0:00"
  const roundedSeconds = Math.floor(seconds)
  const minutes = Math.floor(roundedSeconds / 60)
  return `${minutes}:${String(roundedSeconds % 60).padStart(2, "0")}`
}
