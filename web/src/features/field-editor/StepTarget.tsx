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

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import {
  ChatIcon,
  GalleryIcon,
  type IconProps,
  SparklesIcon,
  VolumeIcon,
} from "@/components/shared/Icons"
import { OptionGroup, OptionGroupItem } from "@/components/ui/OptionList"
import i18next from "i18next"
import type { ComponentType } from "react"
import type { AppState } from "@/types/api"
import { useTranslation } from "react-i18next"

import { EditorSection } from "./EditorSection"
import { getFirstSourceField, hasSmartFieldCollision } from "./fieldEditor"
import type { FieldType } from "./fieldEditor"
import type { FieldEditorControls } from "./useFieldEditor"

interface StepTargetProps {
  controls: FieldEditorControls
  state: AppState
}

const FIELD_TYPES: Array<{
  icon: ComponentType<IconProps>
  labelKey: string
  value: FieldType
}> = [
  { icon: ChatIcon, labelKey: "fieldEditor.fieldTypes.text", value: "chat" },
  { icon: VolumeIcon, labelKey: "fieldEditor.fieldTypes.audio", value: "tts" },
  {
    icon: GalleryIcon,
    labelKey: "fieldEditor.fieldTypes.image",
    value: "image",
  },
]

export const StepTarget = ({ controls, state }: StepTargetProps) => {
  const { t } = useTranslation()
  const { target } = controls.form
  const noteType = state.noteTypes.find((item) => item.id === target.noteTypeId)
  const collision = hasSmartFieldCollision(
    state.smartFields,
    target,
    controls.form.editingFieldId,
  )

  const fieldIsBound = (fieldName: string) =>
    hasSmartFieldCollision(
      state.smartFields,
      {
        deckId: target.deckId,
        noteTypeId: target.noteTypeId,
        targetFieldName: fieldName,
      },
      controls.form.editingFieldId,
    )

  return (
    <div className="mx-auto w-full max-w-[600px]">
      <EditorSection label={t("fieldEditor.sections.whatToGenerate")}>
        <OptionGroup
          aria-label={t("fieldEditor.sections.whatToGenerate")}
          className="flex gap-1.5"
          onValueChange={(fieldType) => {
            const type = FIELD_TYPES.find((item) => item.value === fieldType)
            if (type !== undefined)
              controls.setTarget({ fieldType: type.value })
          }}
          value={target.fieldType}
        >
          {FIELD_TYPES.map(({ icon: Icon, labelKey, value }) => (
            <OptionGroupItem
              className="group flex flex-1 cursor-pointer items-center justify-center gap-[7px] rounded-md py-[11px] text-[13.5px] font-semibold transition data-[state=checked]:bg-white/[0.1] data-[state=checked]:text-zinc-100 data-[state=unchecked]:bg-white/[0.04] data-[state=unchecked]:text-zinc-400 data-[state=unchecked]:hover:bg-white/[0.06] data-[state=unchecked]:hover:text-zinc-200"
              key={value}
              value={value}
            >
              <Icon
                className="group-data-[state=unchecked]:opacity-70"
                size={16}
              />
              {t(labelKey)}
            </OptionGroupItem>
          ))}
        </OptionGroup>
      </EditorSection>

      <EditorSection
        className="mt-7"
        label={t("fieldEditor.sections.onWhichNotes")}
      >
        <div className="grid grid-cols-[1.6fr_1fr] gap-3">
          <FieldLabel label={t("common.noteType")}>
            <Select
              onValueChange={(value) =>
                controls.setTarget({ noteTypeId: Number(value) })
              }
              value={String(target.noteTypeId)}
            >
              <SelectTrigger
                aria-label={t("common.noteType")}
                className="min-h-9 py-1.5"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {state.noteTypes.map((item) => (
                  <SelectItem key={item.id} value={String(item.id)}>
                    {item.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FieldLabel>

          <FieldLabel label={t("common.deck")} optional>
            <Select
              onValueChange={(value) =>
                controls.setTarget({ deckId: Number(value) })
              }
              value={String(target.deckId)}
            >
              <SelectTrigger
                aria-label={t("common.deck")}
                className="min-h-9 py-1.5"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {state.decks.map((deck) => (
                  <SelectItem key={deck.id} value={String(deck.id)}>
                    {deck.id === state.globalDeckId
                      ? t("common.allDecks")
                      : deck.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FieldLabel>
        </div>
      </EditorSection>

      <EditorSection
        className="mt-7"
        label={t("fieldEditor.sections.whichFieldToFill")}
      >
        <Select
          onValueChange={(targetFieldName) => {
            controls.setTarget({ targetFieldName })
            if (targetFieldName === controls.form.sourceFieldName) {
              controls.update({
                sourceFieldName: getFirstSourceField({
                  deckId: target.deckId,
                  globalDeckId: state.globalDeckId,
                  ignoreFieldId: controls.form.editingFieldId,
                  noteType,
                  smartFields: state.smartFields,
                  targetFieldName,
                }),
              })
            }
          }}
          value={target.targetFieldName}
        >
          <SelectTrigger
            aria-label={t("common.field")}
            className="py-[11px] font-mono text-sm font-semibold"
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {noteType?.fields.map((fieldName) => {
              const bound = fieldIsBound(fieldName)
              return (
                <SelectItem
                  className="font-mono text-sm"
                  disabled={bound}
                  key={fieldName}
                  suffix={
                    bound ? (
                      <span className="ms-3 shrink-0 text-xs text-zinc-300">
                        {t("fieldEditor.alreadySmartField")}
                        <SparklesIcon
                          className="ms-1 inline-block align-[-2px]"
                          size={12}
                        />
                      </span>
                    ) : undefined
                  }
                  value={fieldName}
                >
                  {fieldName}
                </SelectItem>
              )
            })}
          </SelectContent>
        </Select>
        {collision && (
          <p className="mt-2 text-xs leading-4 text-caution-soft">
            <strong className="font-semibold">{target.targetFieldName}</strong>{" "}
            {t("fieldEditor.collisionHint")}
          </p>
        )}
      </EditorSection>
    </div>
  )
}

interface FieldLabelProps {
  children: React.ReactNode
  label: string
  optional?: boolean
}

const FieldLabel = ({ children, label, optional }: FieldLabelProps) => (
  <label className="block">
    <span className="mb-2 block text-[11px] font-semibold tracking-[0.08em] text-ink-muted uppercase">
      {label}
      {optional && (
        <span className="ms-1 font-normal tracking-normal text-ink-muted normal-case">
          {i18next.t("common.optional")}
        </span>
      )}
    </span>
    {children}
  </label>
)
