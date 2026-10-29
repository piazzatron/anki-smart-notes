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
import { useTranslation } from "react-i18next"

import { ValidPromptFields } from "@/components/shared/ValidPromptFields"
import { Button } from "@/components/ui/Button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { SparklesIcon } from "@/components/shared/Icons"
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
  chat: "fieldEditor.modelSettings.descriptionChat",
  image: "fieldEditor.modelSettings.descriptionImage",
  tts: "fieldEditor.modelSettings.descriptionTts",
}

export const StepPrompt = ({
  catalog,
  controls,
  state,
  voiceCatalog,
}: StepPromptProps) => {
  const { t } = useTranslation()
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
          <EditorSection label={t("fieldEditor.sections.whichFieldToSpeak")}>
            <Select
              onValueChange={(sourceFieldName) =>
                controls.update({ sourceFieldName })
              }
              value={controls.form.sourceFieldName}
            >
              <SelectTrigger aria-label={t("fieldEditor.sourceField")}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {getValidPromptFields({
                  deckId: target.deckId,
                  globalDeckId: state.globalDeckId,
                  ignoreFieldId: controls.form.editingFieldId,
                  noteType,
                  smartFields: state.smartFields,
                  targetFieldName: target.targetFieldName,
                }).map((fieldName) => (
                  <SelectItem key={fieldName} value={fieldName}>
                    {fieldName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </EditorSection>
        ) : (
          <>
            <div className="hang mb-7 rounded-xl bg-indigo/[0.06] py-5">
              <label
                className="text-[15px] leading-tight font-semibold text-zinc-100"
                htmlFor="field-editor-write-prompt"
              >
                {t("fieldEditor.writePromptForMe")}
                <SparklesIcon
                  className="ms-1.5 inline-block align-[-2px]"
                  size={15}
                />
              </label>
              <p className="mt-1 text-[13px] leading-[1.45] text-ink-muted">
                {t("fieldEditor.writePromptForMeHint")}
              </p>
              <div className="mt-3 flex gap-2">
                <input
                  className="h-11 min-w-0 flex-1 rounded-md bg-black/[0.28] px-3 text-[13px] text-zinc-200 transition outline-none placeholder:text-zinc-600 focus:bg-black/[0.45]"
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
                  placeholder={t("fieldEditor.writePromptPlaceholder")}
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
                  {controls.form.isGenerating
                    ? t("fieldEditor.writing")
                    : t("fieldEditor.writePrompt")}
                </Button>
              </div>
            </div>

            <EditorSection label={t("common.prompt")}>
              <textarea
                className="hang max-h-[46vh] min-h-[150px] w-[calc(100%+2*var(--spacing-hang))] resize-y rounded-xl bg-white/[0.05] py-3.5 font-mono text-[13px] leading-[1.55] text-zinc-200 outline-none placeholder:text-zinc-700 focus:bg-white/[0.07]"
                onChange={(event) =>
                  controls.update({ prompt: event.target.value })
                }
                onFocus={() => {
                  if (!controls.form.validPromptFieldsRevealed) {
                    controls.update({ validPromptFieldsRevealed: true })
                  }
                }}
                aria-label={t("common.prompt")}
                rows={6}
                value={controls.form.prompt}
              />
              {controls.form.validPromptFieldsRevealed && (
                <div className="animate-fade-in">
                  <ValidPromptFields
                    fieldNames={getValidPromptFields({
                      deckId: target.deckId,
                      globalDeckId: state.globalDeckId,
                      ignoreFieldId: controls.form.editingFieldId,
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
          description={t(MODEL_SECTION_DESCRIPTIONS[target.fieldType])}
          label={t("fieldEditor.modelSettings.model")}
        >
          <ModelSettingsSection
            catalog={catalog}
            controls={controls}
            state={state}
            voiceCatalog={voiceCatalog}
          />
        </EditorSection>
      </div>

      <div className="mt-7 border-t border-hairline pt-6">
        <PromptTesterStrip
          field={field}
          saveTargetFieldName={
            target.fieldType === "tts" ? undefined : target.targetFieldName
          }
          title={t("fieldEditor.testSmartField")}
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
  const { deckId, noteTypeId: requiredNoteTypeId } = target

  if (target.fieldType === "chat") {
    return {
      deckId,
      fieldType: "chat",
      prompt,
      requiredNoteTypeId,
      settings: pinnedSettings.chat ?? state.defaults.chat,
    }
  }
  if (target.fieldType === "image") {
    return {
      deckId,
      fieldType: "image",
      prompt,
      requiredNoteTypeId,
      settings: pinnedSettings.image ?? state.defaults.image,
    }
  }

  const settings = pinnedSettings.tts ?? state.defaults.tts
  return {
    deckId,
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
