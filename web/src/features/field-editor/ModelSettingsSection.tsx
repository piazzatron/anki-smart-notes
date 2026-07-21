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

import { ChevronDown, ChevronRight, LoaderCircle } from "lucide-react"
import { useState } from "react"

import { hasGenerationAccess } from "@/components/shared/planPresentation"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { VoicePicker } from "@/features/voice-defaults/VoicePicker"
import { voiceMatchesSettings } from "@/features/voice-defaults/voiceDefaults"
import { modelLabel } from "@/lib/catalog"
import type { AppState, Catalog, VoiceCatalog } from "@/types/api"

import { TextModelSettings } from "./TextModelSettings"
import type { FieldEditorControls } from "./useFieldEditor"

interface ModelSettingsSectionProps {
  catalog: Catalog
  controls: FieldEditorControls
  state: AppState
  voiceCatalog: VoiceCatalog | null
}

export const ModelSettingsSection = ({
  catalog,
  controls,
  state,
  voiceCatalog,
}: ModelSettingsSectionProps) => {
  const [expanded, setExpanded] = useState(false)
  const { fieldType } = controls.form.target
  const pinned = controls.form.pinnedSettings[fieldType]
  const isDefault = pinned === null
  const chatSettings = controls.form.pinnedSettings.chat ?? state.defaults.chat
  const imageSettings =
    controls.form.pinnedSettings.image ?? state.defaults.image
  const ttsSettings = controls.form.pinnedSettings.tts ?? state.defaults.tts
  const modalityLabel =
    fieldType === "chat" ? "Text" : fieldType === "image" ? "Image" : "Voice"
  const voice =
    fieldType === "tts"
      ? voiceCatalog?.voices.find((item) =>
          voiceMatchesSettings(item, ttsSettings),
        )
      : undefined
  const choiceLabel =
    fieldType === "tts"
      ? (voice?.name ?? ttsSettings.voiceId)
      : modelLabel(
          fieldType === "chat" ? chatSettings.model : imageSettings.model,
        )
  const summary =
    fieldType === "chat"
      ? ` · web search ${chatSettings.webSearchEnabled ? "on" : "off"}${
          chatSettings.provider === "auto"
            ? ` · reasoning ${chatSettings.reasoningLevel}`
            : ""
        }`
      : ""

  const setUseDefault = (useDefault: boolean) => {
    if (fieldType === "chat") {
      controls.setPinnedChat(useDefault ? null : { ...state.defaults.chat })
    } else if (fieldType === "image") {
      controls.setPinnedImage(useDefault ? null : { ...state.defaults.image })
    } else {
      controls.setPinnedTTS(useDefault ? null : { ...state.defaults.tts })
    }
  }

  return (
    <div>
      <p className="mb-2 text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
        Model
      </p>
      <div className="overflow-hidden rounded-lg border border-white/[0.075] bg-white/[0.022]">
        <button
          aria-expanded={expanded}
          className="flex w-full items-center justify-between gap-3 px-3.5 py-3 text-left transition hover:bg-white/[0.025]"
          onClick={() => setExpanded((value) => !value)}
        >
          <span className="min-w-0">
            <span className="block truncate text-xs font-medium text-zinc-200">
              {isDefault ? `Default (${choiceLabel})` : choiceLabel}
            </span>
            {summary !== "" && (
              <span className="mt-0.5 block text-[10.5px] text-ink-muted">
                {summary.slice(3)}
              </span>
            )}
          </span>
          {expanded ? (
            <ChevronDown
              aria-hidden
              className="size-4 shrink-0 text-zinc-600"
            />
          ) : (
            <ChevronRight
              aria-hidden
              className="size-4 shrink-0 text-zinc-600"
            />
          )}
        </button>

        {expanded && (
          <div className="border-t border-white/[0.065] px-3.5 py-4">
            <div className="mb-4 grid grid-cols-2 gap-2" role="radiogroup">
              {[true, false].map((useDefault) => (
                <button
                  aria-checked={isDefault === useDefault}
                  className={`rounded-md border px-3 py-2 text-[11px] font-semibold transition ${
                    isDefault === useDefault
                      ? "border-indigo/40 bg-indigo/12 text-indigo-soft"
                      : "border-white/[0.08] bg-white/[0.025] text-zinc-400 hover:text-zinc-200"
                  }`}
                  key={String(useDefault)}
                  onClick={() => setUseDefault(useDefault)}
                  role="radio"
                >
                  {useDefault
                    ? `Use my ${modalityLabel} default`
                    : "Choose for this field"}
                </button>
              ))}
            </div>

            {!isDefault && fieldType === "chat" && (
              <TextModelSettings
                catalog={catalog}
                onChange={controls.setPinnedChat}
                value={controls.form.pinnedSettings.chat!}
              />
            )}
            {!isDefault && fieldType === "image" && (
              <ImageModelPicker catalog={catalog} controls={controls} />
            )}
            {!isDefault &&
              fieldType === "tts" &&
              (voiceCatalog === null ? (
                <div className="flex items-center justify-center gap-2 py-8 text-xs text-ink-muted">
                  <LoaderCircle aria-hidden className="size-4 animate-spin" />
                  Loading voices…
                </div>
              ) : (
                <VoicePicker
                  canPreview={hasGenerationAccess(state.account)}
                  catalog={voiceCatalog}
                  listMaxHeight={260}
                  onSelect={controls.setPinnedTTS}
                  value={controls.form.pinnedSettings.tts!}
                />
              ))}
          </div>
        )}
      </div>
    </div>
  )
}

const ImageModelPicker = ({
  catalog,
  controls,
}: Pick<ModelSettingsSectionProps, "catalog" | "controls">) => (
  <label className="block">
    <span className="mb-2 block text-[10px] font-semibold tracking-[0.06em] text-ink-faint uppercase">
      Model
    </span>
    <Select
      onValueChange={(model) => {
        const selected = catalog.image.models.find((item) => item.id === model)
        if (selected === undefined)
          throw new Error(`Image catalog is missing model ${model}`)
        controls.setPinnedImage({ model, provider: selected.provider })
      }}
      value={controls.form.pinnedSettings.image!.model}
    >
      <SelectTrigger aria-label="Image model">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {catalog.image.models.map((model) => (
          <SelectItem key={`${model.provider}:${model.id}`} value={model.id}>
            {modelLabel(model.id)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  </label>
)
