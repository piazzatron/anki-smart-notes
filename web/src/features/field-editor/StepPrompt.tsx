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

import { LoaderCircle, WandSparkles } from "lucide-react"

import { Button } from "@/components/ui/Button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { ImagePromptTester } from "@/features/prompt-tester/ImagePromptTester"
import { PromptTester } from "@/features/prompt-tester/PromptTester"
import { VoicePromptTester } from "@/features/prompt-tester/VoicePromptTester"
import { voiceMatchesSettings } from "@/features/voice-defaults/voiceDefaults"
import type { AppState, Catalog, VoiceCatalog } from "@/types/api"

import { ModelSettingsSection } from "./ModelSettingsSection"
import type { FieldEditorControls } from "./useFieldEditor"

interface StepPromptProps {
  catalog: Catalog
  controls: FieldEditorControls
  state: AppState
  voiceCatalog: VoiceCatalog | null
}

const TYPE_LABELS = { chat: "Text", image: "Image", tts: "Audio" }

export const StepPrompt = ({
  catalog,
  controls,
  state,
  voiceCatalog,
}: StepPromptProps) => {
  const { target } = controls.form
  const noteType = state.noteTypes.find((item) => item.id === target.noteTypeId)
  const deck = state.decks.find((item) => item.id === target.deckId)

  return (
    <div>
      <p className="mb-4 text-xs text-ink-muted">
        {TYPE_LABELS[target.fieldType]} · fills{" "}
        <strong className="font-mono font-medium text-zinc-200">
          {target.targetFieldName}
        </strong>{" "}
        on{" "}
        <strong className="font-medium text-zinc-200">{noteType?.name}</strong>{" "}
        notes
        {target.deckId !== state.globalDeckId && deck !== undefined && (
          <> · {deck.name}</>
        )}
      </p>

      {target.fieldType === "tts" ? (
        <label className="mb-4 block">
          <span className="mb-2 block text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
            Source field
          </span>
          <Select
            onValueChange={(sourceFieldName) =>
              controls.update({ sourceFieldName })
            }
            value={controls.form.sourceFieldName}
          >
            <SelectTrigger aria-label="Source field">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {noteType?.fields
                .filter((fieldName) => fieldName !== target.targetFieldName)
                .map((fieldName) => (
                  <SelectItem key={fieldName} value={fieldName}>
                    {fieldName}
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
        </label>
      ) : (
        <>
          <div className="mb-4">
            <label
              className="mb-2 block text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase"
              htmlFor="field-editor-write-prompt"
            >
              Write My Prompt For Me
            </label>
            <div className="flex gap-2">
              <input
                className="h-10 min-w-0 flex-1 rounded-md border border-white/[0.09] bg-white/[0.035] px-3 text-xs text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-indigo/45"
                id="field-editor-write-prompt"
                onChange={(event) =>
                  controls.update({ writePrompt: event.target.value })
                }
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault()
                    void controls.generateDraftPrompt()
                  }
                }}
                placeholder='"Translate to natural English…"'
                value={controls.form.writePrompt}
              />
              <Button
                className="h-10 shrink-0 px-3.5"
                disabled={
                  controls.form.writePrompt.trim() === "" ||
                  controls.form.isGenerating
                }
                onClick={() => void controls.generateDraftPrompt()}
              >
                {controls.form.isGenerating ? (
                  <LoaderCircle aria-hidden className="size-3.5 animate-spin" />
                ) : (
                  <WandSparkles aria-hidden className="size-3.5" />
                )}
                {controls.form.isGenerating ? "Writing…" : "Write Prompt"}
              </Button>
            </div>
          </div>

          <label className="mb-4 block">
            <span className="mb-2 block text-[11px] font-semibold text-zinc-200">
              Prompt
            </span>
            <textarea
              className="max-h-[40vh] min-h-20 w-full resize-y rounded-md border border-white/10 bg-white/[0.03] px-3 py-2.5 font-mono text-[11px] leading-[1.55] text-zinc-200 outline-none placeholder:text-zinc-700 focus:border-indigo/45"
              onChange={(event) =>
                controls.update({ prompt: event.target.value })
              }
              rows={4}
              value={controls.form.prompt}
            />
          </label>
        </>
      )}

      <div className="mb-4">
        <p className="mb-2 text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
          Test on a real card
        </p>
        <ControlledTester
          controls={controls}
          state={state}
          voiceCatalog={voiceCatalog}
        />
      </div>

      <ModelSettingsSection
        catalog={catalog}
        controls={controls}
        state={state}
        voiceCatalog={voiceCatalog}
      />
    </div>
  )
}

const ControlledTester = ({
  controls,
  state,
  voiceCatalog,
}: Pick<StepPromptProps, "controls" | "state" | "voiceCatalog">) => {
  const { fieldType } = controls.form.target
  if (fieldType === "chat") {
    return (
      <PromptTester
        hidePromptInput
        prompt={controls.form.prompt}
        settings={controls.form.pinnedSettings.chat ?? state.defaults.chat}
      />
    )
  }
  if (fieldType === "image") {
    return (
      <ImagePromptTester
        hidePromptInput
        prompt={controls.form.prompt}
        settings={controls.form.pinnedSettings.image ?? state.defaults.image}
      />
    )
  }

  const settings = controls.form.pinnedSettings.tts ?? state.defaults.tts
  const voiceName =
    voiceCatalog?.voices.find((voice) => voiceMatchesSettings(voice, settings))
      ?.name ?? settings.voiceId
  return (
    <VoicePromptTester
      hidePromptInput
      prompt={`{{${controls.form.sourceFieldName}}}`}
      settings={settings}
      voiceName={voiceName}
    />
  )
}
