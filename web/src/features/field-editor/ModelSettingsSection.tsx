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

import { LoaderCircle, Play, Settings2 } from "lucide-react"
import i18next from "i18next"
import { useState, type ReactNode } from "react"
import { useTranslation } from "react-i18next"

import { Button } from "@/components/ui/Button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
} from "@/components/ui/Dialog"
import { Disclosure } from "@/components/ui/Disclosure"
import { StripHtmlToggle } from "@/components/shared/StripHtmlToggle"
import { Pill } from "@/components/ui/Pill"
import { FieldLabel } from "@/components/ui/FieldLabel"
import { VoicePicker } from "@/features/defaults/VoicePicker"
import {
  allowedVoicesOf,
  shownVoice,
  voiceMatchesSettings,
} from "@/features/defaults/voiceDefaults"
import { ImageModelSelect } from "@/features/image-generation/ImageModelSelect"
import { TextModelPicker } from "@/features/text-generation/TextModelPicker"
import {
  chatSettingsMatch,
  intelligenceLevelOf,
} from "@/features/text-generation/intelligence"
import { usePromptTestCardState } from "@/features/prompt-tester/promptTestCard"
import type { PromptTester } from "@/features/prompt-tester/usePromptTester"
import { modelLabel } from "@/lib/catalog"
import {
  saveChatDefaults,
  saveImageDefaults,
  saveTTSDefaults,
} from "@/services/commands"
import type { AppState, Catalog, VoiceCatalog } from "@/types/api"

import { pinUnlessDefault } from "./fieldEditor"
import type { FieldEditorControls } from "./useFieldEditor"

interface ModelSettingsSectionProps {
  catalog: Catalog
  controls: FieldEditorControls
  state: AppState
  /** The step's tester, which the voice modal runs from its own button. */
  tester: PromptTester
  voiceCatalog: VoiceCatalog | null
}

// One row on the page: what this field generates with, and a way in. Everything that
// configures it lives in a modal, so the prompt above keeps the screen.
export const ModelSettingsSection = ({
  catalog,
  controls,
  state,
  tester,
  voiceCatalog,
}: ModelSettingsSectionProps) => {
  const { t } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const { fieldType } = controls.form.target
  const { pinnedSettings } = controls.form
  const isCustom = pinnedSettings[fieldType] !== null
  const summary = getModelSummary({ controls, state, voiceCatalog })
  const imageSettings = pinnedSettings.image ?? state.defaults.image
  const pinImage = (settings: typeof imageSettings) =>
    controls.setPinnedImage(pinUnlessDefault(settings, state.defaults.image))

  return (
    <>
      <button
        aria-haspopup="dialog"
        className="hang flex min-h-11 w-[calc(100%+2*var(--spacing-hang))] cursor-pointer items-center gap-3 rounded-xl bg-white/[0.05] py-2 text-start transition hover:bg-white/[0.07]"
        onClick={() => setIsOpen(true)}
      >
        <StatusPill isCustom={isCustom} />
        <span className="min-w-0 flex-1 truncate text-[13px] font-semibold text-ink">
          {summary.label}
        </span>
        {summary.detail !== null && (
          <span className="shrink-0 truncate text-xs text-ink-muted">
            {summary.detail}
          </span>
        )}
        <Settings2 aria-hidden className="size-4 shrink-0 text-ink-faint" />
      </button>

      <SettingsDialog
        footerStart={fieldType === "tts" && <VoiceTestButton tester={tester} />}
        footerEnd={isCustom && <SetAsDefaultButton controls={controls} />}
        onOpenChange={setIsOpen}
        open={isOpen}
        // The voice list needs room for names, their language and the provider.
        wide={fieldType === "tts"}
        title={
          fieldType === "tts"
            ? t("fieldEditor.modelSettings.voice")
            : t("fieldEditor.modelSettings.settings")
        }
      >
        <DefaultStatus isCustom={isCustom} />

        {/* The pickers show what the field generates with now. Changing anything gives
            the field its own copy, and changing it back to the default follows again. */}
        <div className="mt-4">
          {fieldType !== "tts" && (
            <FieldLabel as="span">
              {t("fieldEditor.modelSettings.model")}
            </FieldLabel>
          )}
          {fieldType === "chat" && (
            <TextModelPicker
              catalog={catalog.chat}
              onChange={(settings) =>
                controls.setPinnedChat(
                  pinUnlessDefault(
                    settings,
                    state.defaults.chat,
                    chatSettingsMatch,
                  ),
                )
              }
              value={pinnedSettings.chat ?? state.defaults.chat}
            />
          )}
          {fieldType === "image" && (
            <>
              <ImageModelSelect
                ariaLabel={t("fieldEditor.modelSettings.imageModel")}
                catalog={catalog.image}
                onValueChange={(model) =>
                  pinImage({ ...imageSettings, ...model })
                }
                value={imageSettings.model}
              />
              <Disclosure
                className="mt-5"
                defaultOpen={!imageSettings.stripHtml}
                label={t("common.advancedOptions")}
              >
                <StripHtmlToggle
                  checked={imageSettings.stripHtml}
                  onCheckedChange={(stripHtml) =>
                    pinImage({ ...imageSettings, stripHtml })
                  }
                />
              </Disclosure>
            </>
          )}
          {fieldType === "tts" &&
            (voiceCatalog === null ? (
              <div className="flex items-center justify-center gap-2 py-8 text-[13px] text-ink-muted">
                <LoaderCircle aria-hidden className="size-4 animate-spin" />
                {t("fieldEditor.modelSettings.loadingVoices")}
              </div>
            ) : (
              <VoicePicker
                catalog={voiceCatalog}
                listMaxHeight={360}
                onSelect={(settings) =>
                  controls.setPinnedTTS(
                    pinUnlessDefault(settings, state.defaults.tts),
                  )
                }
                value={pinnedSettings.tts ?? state.defaults.tts}
              />
            ))}
        </div>
      </SettingsDialog>
    </>
  )
}

const SettingsDialog = ({
  children,
  footerEnd,
  footerStart,
  onOpenChange,
  open,
  title,
  wide = false,
}: {
  children: ReactNode
  footerEnd?: ReactNode
  footerStart?: ReactNode
  onOpenChange: (open: boolean) => void
  open: boolean
  title: string
  wide?: boolean
}) => (
  <Dialog onOpenChange={onOpenChange} open={open}>
    {/* Title only: the settings below explain themselves. */}
    <DialogContent
      aria-describedby={undefined}
      className={`max-h-[80vh] ${wide ? "w-[min(720px,92vw)]" : "w-[min(520px,92vw)]"}`}
      // Focus the dialog itself: the text picker opens with an ⓘ first, whose tip
      // opens on focus.
      onOpenAutoFocus={(event) => {
        event.preventDefault()
        if (event.currentTarget instanceof HTMLElement)
          event.currentTarget.focus()
      }}
    >
      <DialogHeader title={title} />

      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">{children}</div>

      <DialogFooter>
        {footerStart}
        {footerEnd}
        <Button onClick={() => onOpenChange(false)} variant="success">
          {i18next.t("common.done")}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
)

// Makes this field's own settings the default for its type. The field then follows the
// default again, along with every field that already did.
const SetAsDefaultButton = ({
  controls,
}: {
  controls: FieldEditorControls
}) => {
  const { t } = useTranslation()
  const [status, setStatus] = useState<"error" | "idle" | "saving">("idle")
  const { pinnedSettings, target } = controls.form

  const setAsDefault = async () => {
    setStatus("saving")
    try {
      if (target.fieldType === "chat" && pinnedSettings.chat !== null) {
        await saveChatDefaults(pinnedSettings.chat)
        controls.setPinnedChat(null)
      } else if (
        target.fieldType === "image" &&
        pinnedSettings.image !== null
      ) {
        await saveImageDefaults(pinnedSettings.image)
        controls.setPinnedImage(null)
      } else if (target.fieldType === "tts" && pinnedSettings.tts !== null) {
        await saveTTSDefaults(pinnedSettings.tts)
        controls.setPinnedTTS(null)
      }
      setStatus("idle")
    } catch {
      setStatus("error")
    }
  }

  return (
    <>
      {status === "error" && (
        <span className="text-xs text-danger">
          {t("fieldEditor.modelSettings.setAsDefaultError")}
        </span>
      )}
      <Button
        disabled={status === "saving"}
        onClick={() => void setAsDefault()}
      >
        {t("fieldEditor.modelSettings.setAsDefault")}
      </Button>
    </>
  )
}

// Runs the page's tester (the selected card, read in the voice chosen here) without
// leaving the modal. The result plays as soon as it arrives.
const VoiceTestButton = ({ tester }: { tester: PromptTester }) => {
  const { t } = useTranslation()
  const card = usePromptTestCardState(tester)

  return (
    <div className="me-auto flex min-w-0 items-center gap-2">
      <Button disabled={card.runDisabled} onClick={() => void tester.runTest()}>
        {tester.isTesting ? (
          <LoaderCircle aria-hidden className="size-3.5 animate-spin" />
        ) : (
          <Play aria-hidden className="size-3.5" />
        )}
        {t("fieldEditor.modelSettings.testVoice")}
      </Button>
      {tester.error !== null ? (
        <span className="truncate text-xs text-danger">{tester.error}</span>
      ) : (
        tester.selectedNote === null && (
          <span className="truncate text-xs text-ink-muted">
            {t("promptTester.selectCardInBrowser")}
          </span>
        )
      )}
    </div>
  )
}

// Whether the field follows its default. Leaving it has to be impossible to miss, since
// the field then stops picking up changes to the default.
const DefaultStatus = ({ isCustom }: { isCustom: boolean }) => {
  const { t } = useTranslation()

  return (
    <p className="flex items-center gap-2 text-xs leading-4 text-ink-muted">
      <StatusPill isCustom={isCustom} />
      {isCustom
        ? t("fieldEditor.modelSettings.customDescription")
        : t("fieldEditor.modelSettings.followingDefault")}
    </p>
  )
}

const StatusPill = ({ isCustom }: { isCustom: boolean }) => {
  const { t } = useTranslation()

  return (
    <Pill tone={isCustom ? "caution" : "indigo"}>
      {isCustom
        ? t("fieldEditor.modelSettings.custom")
        : t("fieldEditor.modelSettings.default")}
    </Pill>
  )
}

// What the row says when the modal is closed: the model or voice in use, and the
// settings that would otherwise be invisible from out here.
const getModelSummary = ({
  controls,
  state,
  voiceCatalog,
}: Omit<ModelSettingsSectionProps, "catalog" | "tester">): {
  detail: string | null
  label: string
} => {
  const { pinnedSettings, target } = controls.form
  const keepsHtml = i18next.t("fieldEditor.modelSettings.keepsHtml")

  if (target.fieldType === "image") {
    const settings = pinnedSettings.image ?? state.defaults.image
    return {
      detail: settings.stripHtml ? null : keepsHtml,
      label: modelLabel(settings.model),
    }
  }

  if (target.fieldType === "tts") {
    const settings = shownVoice(
      pinnedSettings.tts ?? state.defaults.tts,
      voiceCatalog?.voices ?? [],
      allowedVoicesOf(state),
    )
    const voice = voiceCatalog?.voices.find((item) =>
      voiceMatchesSettings(item, settings),
    )
    // Voice names leave out their language, so the row adds it.
    return {
      detail:
        voice === undefined || voice.language === "All" ? null : voice.language,
      label: voice?.name ?? settings.voiceId,
    }
  }

  // Auto reads as its level ("Standard intelligence"); a specific model by its name.
  const settings = pinnedSettings.chat ?? state.defaults.chat
  const details = [
    settings.webSearchEnabled
      ? i18next.t("fieldEditor.modelSettings.webSearch")
      : null,
    settings.stripHtml ? null : keepsHtml,
  ].filter((detail) => detail !== null)
  return {
    detail: details.length > 0 ? details.join(" · ") : null,
    label:
      settings.provider === "auto"
        ? i18next.t("fieldEditor.modelSettings.intelligenceLevel", {
            level: i18next.t(
              `intelligence.levels.${intelligenceLevelOf(settings)}`,
            ),
          })
        : modelLabel(settings.model),
  }
}
