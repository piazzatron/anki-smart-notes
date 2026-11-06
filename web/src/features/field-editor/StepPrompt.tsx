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
import { useEffect, useId, useRef, useState } from "react"
import { Trans, useTranslation } from "react-i18next"

import { CodeIcon, PlayIcon, SparklesIcon } from "@/components/shared/Icons"
import { ValidPromptFields } from "@/components/shared/ValidPromptFields"
import { Button } from "@/components/ui/Button"
import { TOOLTIP_SURFACE, TooltipCaret } from "@/components/ui/InfoTip"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import {
  PromptTesterStrip,
  RecentImagePills,
} from "@/features/prompt-tester/PromptTesterStrip"
import {
  usePromptTester,
  type PromptTesterArgs,
} from "@/features/prompt-tester/usePromptTester"
import {
  allowedVoicesOf,
  shownVoice,
  voiceMatchesSettings,
} from "@/features/defaults/voiceDefaults"
import { getValidPromptFields } from "@/lib/promptFields"
import type { AppState, Catalog, VoiceCatalog } from "@/types/api"

import { EditorPanel } from "./EditorPanel"
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
  const { prompt, target } = controls.form
  const noteType = state.noteTypes.find((item) => item.id === target.noteTypeId)
  const validFields = getValidPromptFields({
    deckId: target.deckId,
    globalDeckId: state.globalDeckId,
    ignoreFieldId: controls.form.editingFieldId,
    noteType,
    smartFields: state.smartFields,
    targetFieldName: target.targetFieldName,
  })
  // One tester for the whole step. The model modal runs the same one as the strip below,
  // so a model can be tried without closing it and the result survives the trip back.
  const field = usePromptTester(
    getTesterArgs({ controls, state, voiceCatalog }),
  )

  // A new field starts on describing it; one that has a prompt starts on the prompt.
  const [isDescribeOpen, setIsDescribeOpen] = useState(prompt === "")
  const [isPromptOpen, setIsPromptOpen] = useState(prompt !== "")
  const [isTesterOpen, setIsTesterOpen] = useState(false)
  const [isTipShown, setIsTipShown] = useState(false)
  const promptRef = useRef<HTMLTextAreaElement>(null)
  const describeId = useId()

  // An untouched prompt's cursor sits at 0; start it at the end so a chip appends.
  useEffect(() => {
    const textarea = promptRef.current
    textarea?.setSelectionRange(textarea.value.length, textarea.value.length)
  }, [isPromptOpen])

  const dismissTip = () => {
    if (!isTipShown) return
    setIsTipShown(false)
    void controls.markPromptTipSeen()
  }

  const openPrompt = () => {
    dismissTip()
    setIsPromptOpen(true)
    setIsDescribeOpen(false)
    requestAnimationFrame(() => promptRef.current?.focus())
  }

  // The written prompt stays folded so new users aren't faced with it; the first time,
  // a tip points at where it went.
  const generate = async (description?: string) => {
    const wrote = await controls.generateDraftPrompt(description)
    if (wrote && !isPromptOpen && !state.settings.didSeeGeneratedPromptTip) {
      setIsTipShown(true)
    }
  }

  // A textarea keeps its selection when it loses focus, so a chip reached by Tab still
  // inserts where the cursor was.
  const insertReference = (reference: string) => {
    const textarea = promptRef.current
    const start = textarea?.selectionStart ?? prompt.length
    const end = textarea?.selectionEnd ?? start
    controls.update({
      prompt: prompt.slice(0, start) + reference + prompt.slice(end),
    })
    requestAnimationFrame(() => {
      textarea?.focus()
      textarea?.setSelectionRange(
        start + reference.length,
        start + reference.length,
      )
    })
  }

  const { fieldType, targetFieldName } = target
  const { suggestion } = controls

  // Without a suggestion (signed out, or it failed), a template built from the same
  // fields stands in.
  const example =
    suggestion === null || validFields.length === 0
      ? (suggestion ?? "")
      : suggestion ||
        t(
          fieldType === "image"
            ? "fieldEditor.describe.exampleImage"
            : "fieldEditor.describe.exampleChat",
          { source: validFields[0], target: targetFieldName },
        )

  const canGenerate =
    controls.form.writePrompt.trim() !== "" && !controls.form.isGenerating

  return (
    <div className="grid gap-3">
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
              {validFields.map((fieldName) => (
                <SelectItem key={fieldName} value={fieldName}>
                  {fieldName}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </EditorSection>
      ) : (
        <>
          <EditorPanel
            icon={<SparklesIcon className="text-indigo" size={17} />}
            isOpen={isDescribeOpen}
            onToggle={() => setIsDescribeOpen(!isDescribeOpen)}
            subtitle={t("fieldEditor.describe.hint")}
            subtitleId={`${describeId}-hint`}
            title={t("fieldEditor.describe.title")}
            tone="indigo"
          >
            <div className="relative">
              <textarea
                aria-describedby={`${describeId}-hint ${describeId}-tab`}
                aria-label={t("fieldEditor.describe.title")}
                className="block w-full resize-none rounded-lg bg-white/[0.06] px-3 py-2.5 text-[14px] leading-[1.5] text-ink transition outline-none placeholder:text-ink-faint focus:bg-white/[0.09]"
                onChange={(event) =>
                  controls.update({ writePrompt: event.target.value })
                }
                onKeyDown={(event) => {
                  // Enter and Tab also confirm an IME conversion; leave those alone.
                  if (event.nativeEvent.isComposing) return
                  // Enter generates; Shift+Enter is a new line.
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault()
                    if (canGenerate) void generate()
                  }
                  // Tab takes the example and generates from it, but only while the
                  // box is empty, so it still moves focus once something is typed.
                  if (
                    event.key === "Tab" &&
                    !event.shiftKey &&
                    controls.form.writePrompt === "" &&
                    example !== ""
                  ) {
                    event.preventDefault()
                    controls.update({ writePrompt: example })
                    void generate(example)
                  }
                }}
                placeholder={example}
                rows={3}
                value={controls.form.writePrompt}
              />
              {controls.form.writePrompt === "" && example !== "" && (
                <p
                  className="pointer-events-none absolute end-3 bottom-2.5 text-xs text-ink-muted"
                  id={`${describeId}-tab`}
                >
                  <Trans
                    components={{
                      kbd: (
                        <kbd className="rounded bg-white/[0.08] px-1.5 py-0.5 font-sans text-[11.5px] font-medium text-ink" />
                      ),
                    }}
                    i18nKey="fieldEditor.describe.tabToUse"
                  />
                </p>
              )}
              {/* Where the example and its Tab hint will land, while the guess loads. */}
              {controls.form.writePrompt === "" && suggestion === null && (
                <LoaderCircle
                  aria-hidden
                  className="pointer-events-none absolute start-3 top-3 size-4 animate-spin text-ink-faint"
                />
              )}
            </div>
            <div className="mt-2.5 flex items-center justify-between gap-3">
              <button
                className="cursor-pointer text-xs font-medium text-ink-muted transition hover:text-ink"
                onClick={openPrompt}
                type="button"
              >
                {t("fieldEditor.describe.writeYourself")}
              </button>
              <Button
                className="h-9 shrink-0 px-4"
                disabled={!canGenerate}
                onClick={() => void generate()}
                variant="primary"
              >
                {controls.form.isGenerating ? (
                  <LoaderCircle aria-hidden className="size-3.5 animate-spin" />
                ) : (
                  <WandSparkles aria-hidden className="size-3.5" />
                )}
                {controls.form.isGenerating
                  ? t("fieldEditor.describe.generating")
                  : prompt.trim() === ""
                    ? t("fieldEditor.describe.generate")
                    : t("fieldEditor.describe.regenerate")}
              </Button>
            </div>
          </EditorPanel>

          <div className="relative">
            <EditorPanel
              icon={<CodeIcon className="text-ink-muted" size={17} />}
              isOpen={isPromptOpen}
              onToggle={() =>
                isPromptOpen ? setIsPromptOpen(false) : openPrompt()
              }
              subtitle={
                isPromptOpen
                  ? undefined
                  : prompt.trim() === ""
                    ? t("fieldEditor.promptPanel.writeYourself")
                    : prompt.replace(/\s+/g, " ")
              }
              title={t("common.prompt")}
            >
              <p className="mb-3 text-xs text-ink-muted">
                <Trans
                  components={{
                    code: (
                      <code className="font-mono text-xs text-indigo-soft" />
                    ),
                  }}
                  i18nKey="fieldEditor.promptPanel.description"
                  values={{ example: "{{Field}}" }}
                />
              </p>
              <textarea
                aria-label={t("common.prompt")}
                className="block max-h-[46vh] min-h-[150px] w-full resize-y rounded-lg bg-white/[0.05] px-3 py-3 font-mono text-[13px] leading-[1.55] text-zinc-200 outline-none focus:bg-white/[0.08]"
                onChange={(event) =>
                  controls.update({ prompt: event.target.value })
                }
                ref={promptRef}
                rows={6}
                value={prompt}
              />
              <ValidPromptFields
                fieldNames={validFields}
                label={t("fieldEditor.promptPanel.fieldsOnNote")}
                onInsert={insertReference}
              />
            </EditorPanel>

            {isTipShown && !isPromptOpen && (
              <div
                className={`absolute start-0 top-full z-10 mt-2.5 flex max-w-[320px] animate-fade-in flex-col items-start gap-2.5 ${TOOLTIP_SURFACE}`}
                role="status"
              >
                {/* Pointing up at the panel. */}
                <TooltipCaret className="absolute start-5 -top-[5px] rotate-180" />
                {t("fieldEditor.promptPanel.tip")}
                <button
                  className="cursor-pointer rounded-md bg-white/20 px-2.5 py-1 text-xs font-medium transition hover:bg-white/30"
                  onClick={dismissTip}
                  type="button"
                >
                  {t("fieldEditor.promptPanel.gotIt")}
                </button>
              </div>
            )}
          </div>
        </>
      )}

      <EditorSection
        className="mt-4"
        description={t(MODEL_SECTION_DESCRIPTIONS[target.fieldType])}
        label={t("fieldEditor.modelSettings.settings")}
      >
        <ModelSettingsSection
          catalog={catalog}
          controls={controls}
          state={state}
          voiceCatalog={voiceCatalog}
        />
      </EditorSection>

      <EditorPanel
        accessory={<RecentImagePills field={field} />}
        icon={<PlayIcon className="text-ink-muted" size={17} />}
        isOpen={isTesterOpen}
        onToggle={() => setIsTesterOpen(!isTesterOpen)}
        subtitle={t("fieldEditor.testerHint")}
        title={t("fieldEditor.testSmartField")}
      >
        <PromptTesterStrip
          field={field}
          saveTargetFieldName={
            target.fieldType === "tts" ? undefined : target.targetFieldName
          }
        />
      </EditorPanel>
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

  // Test with the voice the field reads with on this plan.
  const settings = shownVoice(
    pinnedSettings.tts ?? state.defaults.tts,
    voiceCatalog?.voices ?? [],
    allowedVoicesOf(state),
  )
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
