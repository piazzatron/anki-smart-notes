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
import { VoicePicker } from "@/features/defaults/VoicePicker"
import { voiceMatchesSettings } from "@/features/defaults/voiceDefaults"
import { ImageModelSelect } from "@/features/image-generation/ImageModelSelect"
import { TextModelPicker } from "@/features/text-generation/TextModelPicker"
import {
  chatSettingsMatch,
  intelligenceLevelOf,
} from "@/features/text-generation/intelligence"
import { modelLabel } from "@/lib/catalog"
import type { AppState, Catalog, VoiceCatalog } from "@/types/api"

import { pinUnlessDefault } from "./fieldEditor"
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
        onOpenChange={setIsOpen}
        open={isOpen}
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
            <span className="mb-2 block text-[11px] font-semibold tracking-[0.08em] text-ink-muted uppercase">
              {t("fieldEditor.modelSettings.model")}
            </span>
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
                listMaxHeight={260}
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
  onOpenChange,
  open,
  title,
}: {
  children: ReactNode
  onOpenChange: (open: boolean) => void
  open: boolean
  title: string
}) => (
  <Dialog onOpenChange={onOpenChange} open={open}>
    {/* Title only: the settings below explain themselves. */}
    <DialogContent
      aria-describedby={undefined}
      className="max-h-[80vh] w-[min(520px,92vw)]"
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
        <Button onClick={() => onOpenChange(false)} variant="success">
          {i18next.t("common.done")}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
)

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
}: Omit<ModelSettingsSectionProps, "catalog">): {
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
    const settings = pinnedSettings.tts ?? state.defaults.tts
    return {
      detail: null,
      label:
        voiceCatalog?.voices.find((voice) =>
          voiceMatchesSettings(voice, settings),
        )?.name ?? settings.voiceId,
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
