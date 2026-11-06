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

import { LoaderCircle } from "lucide-react"
import { useEffect, useId, useRef, useState } from "react"
import { Trans, useTranslation } from "react-i18next"

import { CardIcon } from "@/components/shared/Icons"
import { ValidPromptFields } from "@/components/shared/ValidPromptFields"
import { GuideTip } from "@/components/ui/InfoTip"
import { Card } from "@/components/ui/Card"
import { OptionGroup, OptionGroupItem } from "@/components/ui/OptionList"
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
import { CARD_TITLE_CLASSES, EditorSection } from "./EditorSection"
import type { FieldEditorDraft, FieldType } from "./fieldEditor"
import { ModelSettingsSection } from "./ModelSettingsSection"
import type { FieldEditorControls } from "./useFieldEditor"

interface StepPromptProps {
  catalog: Catalog
  controls: FieldEditorControls
  state: AppState
  voiceCatalog: VoiceCatalog | null
}

const PROMPT_MODES: FieldEditorDraft["promptMode"][] = ["describe", "write"]

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
  const field = usePromptTester({
    ...getTesterArgs({ controls, state, voiceCatalog }),
    preparePrompt: controls.preparePrompt,
  })

  const [isTesterOpen, setIsTesterOpen] = useState(true)
  const [isTipDismissed, setIsTipDismissed] = useState(false)
  const promptRef = useRef<HTMLTextAreaElement>(null)
  const { promptMode, writePrompt } = controls.form
  const { fieldType, targetFieldName } = target
  const { suggestion } = controls

  // Points at the guess until the user dismisses it or changes the description.
  const isTipShown =
    !isTipDismissed &&
    !state.settings.didSeeGeneratedPromptTip &&
    promptMode === "describe" &&
    suggestion !== null &&
    suggestion !== "" &&
    writePrompt === suggestion

  const dismissTip = () => {
    if (!isTipShown) return
    setIsTipDismissed(true)
    void controls.markPromptTipSeen()
  }

  // The note's fields show once the user starts on the description, not before.
  const [hasFocusedDescription, setHasFocusedDescription] = useState(false)

  // A new field starts with our guess at what it's for already filled in and written up.
  // With no guess (the field's name gave nothing away, or the call failed), the empty
  // box takes focus and its placeholder shows the kind of thing to type.
  const didGuess = useRef(false)
  const describeRef = useRef<HTMLTextAreaElement>(null)
  const titleId = useId()
  useEffect(() => {
    if (didGuess.current || suggestion === null) return
    if (promptMode !== "describe" || writePrompt !== "" || prompt !== "") return
    didGuess.current = true
    if (suggestion === "") {
      describeRef.current?.focus()
      return
    }
    controls.update({ writePrompt: suggestion })
    void controls.generateDraftPrompt(suggestion)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- controls is new each render; didGuess keeps this to once
  }, [prompt, promptMode, suggestion, writePrompt])

  const setPromptMode = (mode: FieldEditorDraft["promptMode"]) => {
    dismissTip()
    controls.setPromptMode(mode)
    if (mode === "write") {
      requestAnimationFrame(() => {
        const textarea = promptRef.current
        textarea?.focus()
        textarea?.setSelectionRange(
          textarea.value.length,
          textarea.value.length,
        )
      })
    }
  }

  // A textarea keeps its selection when it loses focus, so a chip reached by Tab still
  // inserts where the cursor was.
  const insertReference = (reference: string) => {
    const isDescribe = promptMode === "describe"
    const textarea = isDescribe ? describeRef.current : promptRef.current
    const text = isDescribe ? writePrompt : prompt
    const start = textarea?.selectionStart ?? text.length
    const end = textarea?.selectionEnd ?? start
    const next = text.slice(0, start) + reference + text.slice(end)
    if (isDescribe) controls.describe(next)
    else controls.update({ prompt: next })
    requestAnimationFrame(() => {
      textarea?.focus()
      textarea?.setSelectionRange(
        start + reference.length,
        start + reference.length,
      )
    })
  }

  const placeholder =
    validFields[0] === undefined
      ? t("fieldEditor.describe.exampleNoFields")
      : t(
          fieldType === "image"
            ? "fieldEditor.describe.exampleImage"
            : "fieldEditor.describe.exampleChat",
          { source: validFields[0] },
        )

  return (
    <div className="grid grid-cols-1 gap-3">
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
        <Card as="section" className="hang pb-5">
          <div className="flex items-center gap-3 py-4">
            <div className="min-w-0 flex-1">
              <h2 className={CARD_TITLE_CLASSES} id={titleId}>
                <Trans
                  components={{
                    code: (
                      <code className="rounded bg-white/[0.08] px-1.5 font-mono text-[15px] font-medium" />
                    ),
                  }}
                  i18nKey="fieldEditor.describe.title"
                  values={{ field: targetFieldName }}
                />
              </h2>
              {promptMode === "write" && (
                <p className="mt-0.5 truncate text-xs text-ink-muted">
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
              )}
            </div>
            <OptionGroup
              aria-labelledby={titleId}
              className="flex shrink-0 rounded-lg bg-white/[0.04] p-0.5"
              onValueChange={(mode) =>
                setPromptMode(mode as FieldEditorDraft["promptMode"])
              }
              value={promptMode}
            >
              {PROMPT_MODES.map((mode) => (
                <OptionGroupItem
                  className="cursor-pointer rounded-md px-3 py-1.5 text-[13px] font-medium transition data-[state=checked]:bg-white/[0.1] data-[state=checked]:text-ink data-[state=unchecked]:text-ink-muted data-[state=unchecked]:hover:text-ink"
                  key={mode}
                  value={mode}
                >
                  {t(
                    mode === "describe"
                      ? "fieldEditor.describe.modeDescribe"
                      : "fieldEditor.describe.modeWrite",
                  )}
                </OptionGroupItem>
              ))}
            </OptionGroup>
          </div>

          {promptMode === "describe" ? (
            <>
              <div className="relative">
                <GuideTip
                  message={t("fieldEditor.describe.guessTip")}
                  onDismiss={dismissTip}
                  open={isTipShown}
                >
                  <textarea
                    aria-labelledby={titleId}
                    className="block w-full resize-none rounded-lg bg-white/[0.06] px-3 py-2.5 text-[14px] leading-[1.5] text-ink transition outline-none placeholder:text-ink-faint focus:bg-white/[0.09]"
                    onChange={(event) => {
                      dismissTip()
                      controls.describe(event.target.value)
                    }}
                    onFocus={() => setHasFocusedDescription(true)}
                    onKeyDown={(event) => {
                      // Enter also confirms an IME conversion; leave that alone.
                      if (event.nativeEvent.isComposing) return
                      // Enter writes it now; Shift+Enter is a new line.
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault()
                        void controls.generateDraftPrompt()
                      }
                    }}
                    placeholder={suggestion === null ? "" : placeholder}
                    ref={describeRef}
                    rows={2}
                    value={writePrompt}
                  />
                </GuideTip>
                {writePrompt === "" && suggestion === null && (
                  <LoaderCircle
                    aria-hidden
                    className="pointer-events-none absolute start-3 top-3 size-4 animate-spin text-ink-faint"
                  />
                )}
                {/* The prompt is being written from the description. */}
                {controls.form.isGenerating && (
                  <LoaderCircle
                    aria-label={t("fieldEditor.describe.writing")}
                    className="pointer-events-none absolute end-3 top-3 size-4 animate-spin text-ink-faint"
                    role="status"
                  />
                )}
              </div>
              {hasFocusedDescription && (
                <ValidPromptFields
                  fieldNames={validFields}
                  label={t("fieldEditor.describe.fieldsHint")}
                  onInsert={insertReference}
                  plain
                />
              )}
            </>
          ) : (
            <>
              <textarea
                aria-label={t("common.prompt")}
                className="block max-h-[46vh] min-h-[150px] w-full resize-y rounded-lg bg-white/[0.06] px-3 py-3 font-mono text-[13px] leading-[1.55] text-ink outline-none focus:bg-white/[0.09]"
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
            </>
          )}
        </Card>
      )}

      <EditorPanel
        accessory={<RecentImagePills field={field} />}
        icon={<CardIcon className="text-ink-muted" size={17} />}
        isOpen={isTesterOpen}
        onToggle={() => setIsTesterOpen(!isTesterOpen)}
        title={t("fieldEditor.testSmartField")}
      >
        <PromptTesterStrip
          field={field}
          saveTargetFieldName={
            target.fieldType === "tts" ? undefined : target.targetFieldName
          }
        />
      </EditorPanel>

      <EditorSection
        className="mt-4"
        description={t(MODEL_SECTION_DESCRIPTIONS[target.fieldType])}
        label={t("fieldEditor.modelSettings.settings")}
      >
        <ModelSettingsSection
          catalog={catalog}
          controls={controls}
          state={state}
          tester={field}
          voiceCatalog={voiceCatalog}
        />
      </EditorSection>
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
