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
import type { AppState } from "@/types/api"

import { EditorSection } from "./EditorSection"
import { getFirstSourceField, hasSmartFieldCollision } from "./fieldEditor"
import type { FieldType } from "./fieldEditor"
import type { FieldEditorControls } from "./useFieldEditor"

interface StepTargetProps {
  controls: FieldEditorControls
  state: AppState
}

const FIELD_TYPES: Array<{
  emoji: string
  label: string
  value: FieldType
}> = [
  { emoji: "💬", label: "Text", value: "chat" },
  { emoji: "🔈", label: "Audio", value: "tts" },
  { emoji: "🖼️", label: "Image", value: "image" },
]

export const StepTarget = ({ controls, state }: StepTargetProps) => {
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
      <EditorSection label="What do you want to generate?">
        <div className="flex gap-1.5" role="radiogroup">
          {FIELD_TYPES.map(({ emoji, label, value }) => {
            const selected = target.fieldType === value
            return (
              <button
                aria-checked={selected}
                className={`flex flex-1 items-center justify-center gap-[7px] rounded-md border py-[11px] text-[12.5px] font-semibold transition ${
                  selected
                    ? "border-white/25 bg-white/[0.07] text-zinc-100"
                    : "border-white/[0.08] bg-white/[0.025] text-zinc-400 hover:border-white/15 hover:text-zinc-200"
                }`}
                key={value}
                onClick={() => controls.setTarget({ fieldType: value })}
                role="radio"
              >
                <span
                  aria-hidden
                  className={`text-[15px] leading-none ${selected ? "" : "opacity-70"}`}
                >
                  {emoji}
                </span>
                {label}
              </button>
            )
          })}
        </div>
      </EditorSection>

      <EditorSection className="mt-7" label="On which notes?">
        <div className="grid grid-cols-[1.6fr_1fr] gap-3">
          <FieldLabel label="Note Type">
            <Select
              onValueChange={(value) =>
                controls.setTarget({ noteTypeId: Number(value) })
              }
              value={String(target.noteTypeId)}
            >
              <SelectTrigger aria-label="Note Type" className="min-h-9 py-1.5">
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

          <FieldLabel label="Deck" optional>
            <Select
              onValueChange={(value) =>
                controls.setTarget({ deckId: Number(value) })
              }
              value={String(target.deckId)}
            >
              <SelectTrigger aria-label="Deck" className="min-h-9 py-1.5">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {state.decks.map((deck) => (
                  <SelectItem key={deck.id} value={String(deck.id)}>
                    {deck.id === state.globalDeckId ? "All Decks" : deck.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FieldLabel>
        </div>
      </EditorSection>

      <EditorSection className="mt-7" label="Which field should it fill?">
        <Select
          onValueChange={(targetFieldName) => {
            controls.setTarget({ targetFieldName })
            if (targetFieldName === controls.form.sourceFieldName) {
              controls.update({
                sourceFieldName: getFirstSourceField(noteType, targetFieldName),
              })
            }
          }}
          value={target.targetFieldName}
        >
          <SelectTrigger
            aria-label="Field"
            className="py-[11px] font-mono text-sm font-semibold"
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {noteType?.fields.map((fieldName) => {
              const bound = fieldIsBound(fieldName)
              return (
                <SelectItem
                  className="font-mono text-[13px]"
                  disabled={bound}
                  key={fieldName}
                  suffix={
                    bound ? (
                      <span className="ml-3 shrink-0 text-[11px] text-zinc-300">
                        Already a Smart Field ✨
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
          <p className="mt-2 text-[11px] leading-4 text-amber/85">
            <strong className="font-semibold">{target.targetFieldName}</strong>{" "}
            already has a Smart Field — pick a different field, deck, or note
            type
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
    <span className="mb-2 block text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
      {label}
      {optional && (
        <span className="ml-1 font-normal tracking-normal text-zinc-600 normal-case">
          (optional)
        </span>
      )}
    </span>
    {children}
  </label>
)
