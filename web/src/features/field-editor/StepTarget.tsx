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

import { Image, MessageSquareText, Volume2 } from "lucide-react"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import type { AppState } from "@/types/api"

import { getFirstSourceField, hasSmartFieldCollision } from "./fieldEditor"
import type { FieldType } from "./fieldEditor"
import type { FieldEditorControls } from "./useFieldEditor"

interface StepTargetProps {
  controls: FieldEditorControls
  state: AppState
}

const FIELD_TYPES: Array<{
  Icon: typeof MessageSquareText
  label: string
  value: FieldType
}> = [
  { Icon: MessageSquareText, label: "Text", value: "chat" },
  { Icon: Volume2, label: "Audio", value: "tts" },
  { Icon: Image, label: "Image", value: "image" },
]

export const StepTarget = ({ controls, state }: StepTargetProps) => {
  const { target } = controls.form
  const noteType = state.noteTypes.find((item) => item.id === target.noteTypeId)
  const collision = hasSmartFieldCollision(state.smartFields, target)

  const fieldIsBound = (fieldName: string) =>
    hasSmartFieldCollision(state.smartFields, {
      deckId: target.deckId,
      noteTypeId: target.noteTypeId,
      targetFieldName: fieldName,
    })

  return (
    <div className="mx-auto max-w-[580px]">
      <div className="mb-6 text-center">
        <h2 className="text-lg font-bold tracking-[-0.02em] text-zinc-100">
          What are we generating?
        </h2>
        <p className="mt-1.5 text-xs text-ink-muted">
          Pick the note type and field this Smart Field fills.
        </p>
      </div>

      <div className="grid grid-cols-[1.45fr_1fr] gap-3">
        <FieldLabel label="Note Type">
          <Select
            onValueChange={(value) =>
              controls.setTarget({ noteTypeId: Number(value) })
            }
            value={String(target.noteTypeId)}
          >
            <SelectTrigger aria-label="Note Type">
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
            <SelectTrigger aria-label="Deck">
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

      <div className="mt-5">
        <p className="mb-2 text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
          Type
        </p>
        <div className="grid grid-cols-3 gap-2" role="radiogroup">
          {FIELD_TYPES.map(({ Icon, label, value }) => {
            const selected = target.fieldType === value
            return (
              <button
                aria-checked={selected}
                className={`flex min-h-11 items-center justify-center gap-2 rounded-md border text-xs font-semibold transition ${
                  selected
                    ? "border-indigo/45 bg-indigo/14 text-indigo-soft"
                    : "border-white/[0.09] bg-white/[0.03] text-zinc-400 hover:border-white/15 hover:text-zinc-200"
                }`}
                key={value}
                onClick={() => controls.setTarget({ fieldType: value })}
                role="radio"
              >
                <Icon aria-hidden className="size-3.5" />
                {label}
              </button>
            )
          })}
        </div>
      </div>

      <div className="mt-5">
        <FieldLabel label="Field">
          <Select
            onValueChange={(targetFieldName) => {
              controls.setTarget({ targetFieldName })
              if (targetFieldName === controls.form.sourceFieldName) {
                controls.update({
                  sourceFieldName: getFirstSourceField(
                    noteType,
                    targetFieldName,
                  ),
                })
              }
            }}
            value={target.targetFieldName}
          >
            <SelectTrigger aria-label="Field">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {noteType?.fields.map((fieldName) => {
                const bound = fieldIsBound(fieldName)
                return (
                  <SelectItem
                    disabled={bound}
                    key={fieldName}
                    value={fieldName}
                  >
                    {fieldName}
                    {bound && (
                      <span className="ml-auto text-[10px] text-ink-faint">
                        · already smart
                      </span>
                    )}
                  </SelectItem>
                )
              })}
            </SelectContent>
          </Select>
        </FieldLabel>
        {collision && (
          <p className="mt-2 text-[11px] leading-4 text-amber/85">
            <strong className="font-semibold">{target.targetFieldName}</strong>{" "}
            already has a Smart Field — pick a different field, deck, or note
            type
          </p>
        )}
      </div>
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
