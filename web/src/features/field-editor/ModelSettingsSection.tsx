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

import { LoaderCircle, Settings2 } from "lucide-react"
import { useState, type ReactNode } from "react"

import { Button } from "@/components/ui/Button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/Dialog"
import { VoicePicker } from "@/features/defaults/VoicePicker"
import { voiceMatchesSettings } from "@/features/defaults/voiceDefaults"
import { ImageModelSelect } from "@/features/image-generation/ImageModelSelect"
import { modelLabel } from "@/lib/catalog"
import type { AppState, Catalog, VoiceCatalog } from "@/types/api"

import type { FieldType } from "./fieldEditor"
import { TextModelSettings } from "./TextModelSettings"
import type { FieldEditorControls } from "./useFieldEditor"

interface ModelSettingsSectionProps {
  catalog: Catalog
  controls: FieldEditorControls
  state: AppState
  voiceCatalog: VoiceCatalog | null
}

// One row on the page: what this field generates with, and a way in. Everything that
// configures it lives in a modal, so the prompt above keeps the screen.
export const ModelSettingsSection = ({
  catalog,
  controls,
  state,
  voiceCatalog,
}: ModelSettingsSectionProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const { fieldType } = controls.form.target
  const summary = getModelSummary({ controls, state, voiceCatalog })

  return (
    <>
      <button
        aria-haspopup="dialog"
        className="flex min-h-11 w-full cursor-pointer items-center gap-3 rounded-md border border-white/[0.09] bg-white/[0.04] px-3 py-2 text-left transition hover:border-white/16"
        onClick={() => setIsOpen(true)}
      >
        <span className="min-w-0 flex-1 truncate text-xs font-semibold text-zinc-100">
          {summary.label}
        </span>
        {summary.detail !== null && (
          <span className="shrink-0 truncate text-[11px] text-ink-muted">
            {summary.detail}
          </span>
        )}
        <Settings2 aria-hidden className="size-4 shrink-0 text-ink-faint" />
      </button>

      <SettingsDialog
        onOpenChange={setIsOpen}
        open={isOpen}
        subtitle="Applies to this Smart Field only."
        title={fieldType === "tts" ? "Voice" : "Model"}
      >
        <PinnedOrDefault
          controls={controls}
          defaultLabel={getDefaultLabel({ fieldType, state, voiceCatalog })}
          fieldType={fieldType}
          state={state}
        />

        {controls.form.pinnedSettings[fieldType] === null ? (
          <p className="mt-3 text-[11px] leading-4 text-ink-muted">
            Your {MODALITIES[fieldType].name} is shared by every Smart Field
            that uses it. Change it in{" "}
            <span className="font-semibold text-indigo-soft">
              {MODALITIES[fieldType].where}
            </span>
            .
          </p>
        ) : (
          <div className="mt-4">
            {fieldType === "chat" &&
              controls.form.pinnedSettings.chat !== null && (
                <TextModelSettings
                  catalog={catalog.chat}
                  onChange={controls.setPinnedChat}
                  value={controls.form.pinnedSettings.chat}
                />
              )}
            {fieldType === "image" &&
              controls.form.pinnedSettings.image !== null && (
                <label className="block">
                  <span className="mb-2 block text-[10px] font-semibold tracking-[0.06em] text-ink-faint uppercase">
                    Model
                  </span>
                  <ImageModelSelect
                    ariaLabel="Image model"
                    catalog={catalog.image}
                    onValueChange={controls.setPinnedImage}
                    value={controls.form.pinnedSettings.image.model}
                  />
                </label>
              )}
            {fieldType === "tts" &&
              controls.form.pinnedSettings.tts !== null &&
              (voiceCatalog === null ? (
                <div className="flex items-center justify-center gap-2 py-8 text-xs text-ink-muted">
                  <LoaderCircle aria-hidden className="size-4 animate-spin" />
                  Loading voices…
                </div>
              ) : (
                <VoicePicker
                  catalog={voiceCatalog}
                  listMaxHeight={260}
                  onSelect={controls.setPinnedTTS}
                  value={controls.form.pinnedSettings.tts}
                />
              ))}
          </div>
        )}
      </SettingsDialog>
    </>
  )
}

const SettingsDialog = ({
  children,
  onOpenChange,
  open,
  subtitle,
  title,
}: {
  children: ReactNode
  onOpenChange: (open: boolean) => void
  open: boolean
  subtitle: string
  title: string
}) => (
  <Dialog onOpenChange={onOpenChange} open={open}>
    <DialogContent className="max-h-[80vh] w-[min(520px,92vw)]">
      <header className="shrink-0 border-b border-white/[0.07] py-3.5 pr-10 pl-5">
        <DialogTitle className="text-[13px] font-bold text-ink">
          {title}
        </DialogTitle>
        <DialogDescription className="mt-0.5 text-[11px] text-ink-faint">
          {subtitle}
        </DialogDescription>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">{children}</div>

      <footer className="flex shrink-0 justify-end border-t border-white/[0.07] px-5 py-3">
        <Button onClick={() => onOpenChange(false)} variant="success">
          Done
        </Button>
      </footer>
    </DialogContent>
  </Dialog>
)

// Where a field's settings come from: the shared default, or this field's own pick.
// Every field type asks it the same way.
const PinnedOrDefault = ({
  controls,
  defaultLabel,
  fieldType,
  state,
}: {
  controls: FieldEditorControls
  defaultLabel: string
  fieldType: FieldType
  state: AppState
}) => {
  const isDefault = controls.form.pinnedSettings[fieldType] === null

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
    <div className="grid grid-cols-2 gap-2" role="radiogroup">
      {[true, false].map((useDefault) => (
        <button
          aria-checked={isDefault === useDefault}
          className={`cursor-pointer rounded-md border px-3 py-2 text-[11px] font-semibold transition ${
            isDefault === useDefault
              ? "border-indigo/40 bg-indigo/12 text-indigo-soft"
              : "border-white/[0.08] bg-white/[0.025] text-zinc-400 hover:text-zinc-200"
          }`}
          key={String(useDefault)}
          onClick={() => setUseDefault(useDefault)}
          role="radio"
        >
          {useDefault ? (
            <>
              Use my {MODALITIES[fieldType].name}
              <span className="mt-0.5 block truncate text-[10px] font-medium opacity-75">
                {defaultLabel}
              </span>
            </>
          ) : (
            "Pick a custom model for this field"
          )}
        </button>
      ))}
    </div>
  )
}

const MODALITIES: Record<FieldType, { name: string; where: string }> = {
  chat: { name: "text default", where: "Defaults › Text" },
  image: { name: "image default", where: "Defaults › Images" },
  tts: { name: "voice default", where: "Defaults › Voice" },
}

// The value a field inherits when it follows its default.
const getDefaultLabel = ({
  fieldType,
  state,
  voiceCatalog,
}: {
  fieldType: FieldType
  state: AppState
  voiceCatalog: VoiceCatalog | null
}): string => {
  if (fieldType === "tts") {
    return (
      voiceCatalog?.voices.find((voice) =>
        voiceMatchesSettings(voice, state.defaults.tts),
      )?.name ?? state.defaults.tts.voiceId
    )
  }

  return modelLabel(
    fieldType === "image"
      ? state.defaults.image.model
      : state.defaults.chat.model,
  )
}

// What the row says when the modal is closed: the model or voice in use, and the
// settings that would otherwise be invisible from out here.
const getModelSummary = ({
  controls,
  state,
  voiceCatalog,
}: Omit<ModelSettingsSectionProps, "catalog">): {
  detail: string | null
  label: string
} => {
  const { pinnedSettings } = controls.form

  if (controls.form.target.fieldType === "image") {
    const settings = pinnedSettings.image ?? state.defaults.image
    const label = modelLabel(settings.model)
    return {
      detail: null,
      label: pinnedSettings.image === null ? `Default (${label})` : label,
    }
  }

  if (controls.form.target.fieldType === "tts") {
    const settings = pinnedSettings.tts ?? state.defaults.tts
    const label =
      voiceCatalog?.voices.find((voice) =>
        voiceMatchesSettings(voice, settings),
      )?.name ?? settings.voiceId
    return {
      detail: null,
      label: pinnedSettings.tts === null ? `Default (${label})` : label,
    }
  }

  const settings = pinnedSettings.chat ?? state.defaults.chat
  const extras = [
    settings.provider === "auto" && settings.reasoningLevel !== "off"
      ? `${settings.reasoningLevel} reasoning`
      : null,
    settings.webSearchEnabled ? "web search" : null,
  ].filter((extra) => extra !== null)

  return {
    detail: extras.length === 0 ? null : extras.join(" · "),
    label:
      pinnedSettings.chat === null
        ? `Default (${modelLabel(settings.model)})`
        : modelLabel(settings.model),
  }
}
