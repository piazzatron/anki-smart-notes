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

import { ValidPromptFields } from "@/components/shared/ValidPromptFields"
import { Button } from "@/components/ui/Button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { PromptTesterStrip } from "@/features/prompt-tester/PromptTesterStrip"
import {
  usePromptTester,
  type PromptTesterArgs,
} from "@/features/prompt-tester/usePromptTester"
import { voiceMatchesSettings } from "@/features/defaults/voiceDefaults"
import { getValidPromptFields } from "@/lib/promptFields"
import type { AppState, Catalog, VoiceCatalog } from "@/types/api"

import { EditorSection } from "./EditorSection"
import type { FieldType } from "./fieldEditor"
import { ModelSettingsSection } from "./ModelSettingsSection"
import type { FieldEditorControls } from "./useFieldEditor"

interface StepPromptProps {
  catalog: Catalog
  controls: FieldEditorControls
  state: AppState
  voiceCatalog: VoiceCatalog | null
}

// Most people never touch this, so the section says so rather than explaining models.
const MODEL_SECTION_DESCRIPTIONS: Record<FieldType, string> = {
  chat: "Set the AI that writes this field. Most fields can stay on the default.",
  image:
    "Set the AI that draws this field. Most fields can stay on the default.",
  tts: "Set the voice that reads this field. Most fields can stay on the default.",
}

export const StepPrompt = ({
  catalog,
  controls,
  state,
  voiceCatalog,
}: StepPromptProps) => {
  const { target } = controls.form
  const noteType = state.noteTypes.find((item) => item.id === target.noteTypeId)
  // One tester for the whole step. The model modal runs the same one as the strip below,
  // so a model can be tried without closing it and the result survives the trip back.
  const field = usePromptTester(
    getTesterArgs({ controls, state, voiceCatalog }),
  )

  return (
    <div>
      <div>
        {target.fieldType === "tts" ? (
          <EditorSection label="Which field should it speak?">
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
          </EditorSection>
        ) : (
          <>
            <div className="mb-7 rounded-[10px] border border-indigo/30 bg-indigo/[0.06] px-4 py-4">
              <label
                className="text-[15px] leading-tight font-semibold text-zinc-100"
                htmlFor="field-editor-write-prompt"
              >
                Write my prompt for me
                <span aria-hidden className="ml-1.5">
                  ✨
                </span>
              </label>
              <p className="mt-1 text-[12px] leading-[1.45] text-ink-muted">
                Say what you want in plain English — we&apos;ll write the prompt
                below.
              </p>
              <div className="mt-3 flex gap-2">
                <input
                  className="h-11 min-w-0 flex-1 rounded-md border border-indigo/25 bg-black/[0.28] px-3 text-xs text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-indigo/45"
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
                  className="h-11 shrink-0 px-4"
                  disabled={
                    controls.form.writePrompt.trim() === "" ||
                    controls.form.isGenerating
                  }
                  onClick={() => void controls.generateDraftPrompt()}
                  variant="primary"
                >
                  {controls.form.isGenerating ? (
                    <LoaderCircle
                      aria-hidden
                      className="size-3.5 animate-spin"
                    />
                  ) : (
                    <WandSparkles aria-hidden className="size-3.5" />
                  )}
                  {controls.form.isGenerating ? "Writing…" : "Write Prompt"}
                </Button>
              </div>
            </div>

            <EditorSection label="Prompt">
              <textarea
                className="max-h-[46vh] min-h-[150px] w-full resize-y rounded-md border border-white/10 bg-white/[0.03] px-3 py-2.5 font-mono text-[12px] leading-[1.55] text-zinc-200 outline-none placeholder:text-zinc-700 focus:border-indigo/45"
                onChange={(event) =>
                  controls.update({ prompt: event.target.value })
                }
                onFocus={() => {
                  if (!controls.form.validPromptFieldsRevealed) {
                    controls.update({ validPromptFieldsRevealed: true })
                  }
                }}
                aria-label="Prompt"
                rows={6}
                value={controls.form.prompt}
              />
              {controls.form.validPromptFieldsRevealed && (
                <div className="animate-fade-in">
                  <ValidPromptFields
                    fieldNames={getValidPromptFields({
                      deckId: target.deckId,
                      noteType,
                      smartFields: state.smartFields,
                      targetFieldName: target.targetFieldName,
                    })}
                  />
                </div>
              )}
            </EditorSection>
          </>
        )}

        <EditorSection
          className="mt-7"
          description={MODEL_SECTION_DESCRIPTIONS[target.fieldType]}
          label="Model"
        >
          <ModelSettingsSection
            catalog={catalog}
            controls={controls}
            field={field}
            state={state}
            voiceCatalog={voiceCatalog}
          />
        </EditorSection>
      </div>

      <div className="mt-7 border-t border-white/[0.06] pt-6">
        <PromptTesterStrip
          field={field}
          saveTargetFieldName={
            target.fieldType === "tts" ? undefined : target.targetFieldName
          }
          title="Test your Smart Field"
        />
      </div>
    </div>
  )
}

// The tester this step runs: the prompt the editor already owns, against the settings the
// field would generate with.
const getTesterArgs = ({
  controls,
  state,
  voiceCatalog,
}: Pick<
  StepPromptProps,
  "controls" | "state" | "voiceCatalog"
>): PromptTesterArgs => {
  const { pinnedSettings, prompt, sourceFieldName, target } = controls.form
  const requiredNoteTypeId = target.noteTypeId

  if (target.fieldType === "chat") {
    return {
      fieldType: "chat",
      prompt,
      requiredNoteTypeId,
      settings: pinnedSettings.chat ?? state.defaults.chat,
    }
  }
  if (target.fieldType === "image") {
    return {
      fieldType: "image",
      prompt,
      requiredNoteTypeId,
      settings: pinnedSettings.image ?? state.defaults.image,
    }
  }

  const settings = pinnedSettings.tts ?? state.defaults.tts
  return {
    fieldType: "tts",
    prompt: `{{${sourceFieldName}}}`,
    requiredNoteTypeId,
    settings,
    voiceName:
      voiceCatalog?.voices.find((voice) =>
        voiceMatchesSettings(voice, settings),
      )?.name ?? settings.voiceId,
  }
}
