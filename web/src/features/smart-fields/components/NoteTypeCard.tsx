import { Plus } from "lucide-react"
import { useTranslation } from "react-i18next"

import { Pill } from "@/components/ui/Pill"

import { SmartFieldRow } from "./SmartFieldRow"

import type { SmartField } from "@/types/api"

import type { NoteTypeGroup } from "../groupSmartFields"

interface NoteTypeCardProps {
  deckName: string
  group: NoteTypeGroup
  isDeckOverride: boolean
  onCreate: (noteTypeId: number) => void
  onDelete: (field: SmartField) => Promise<void>
  onDuplicate: (field: SmartField) => void
  onEdit: (field: SmartField) => void
  onToggleEnabled: (field: SmartField) => Promise<void>
  onError: (message: string) => void
}

export const NoteTypeCard = ({
  deckName,
  group,
  isDeckOverride,
  onCreate,
  onDelete,
  onDuplicate,
  onEdit,
  onToggleEnabled,
  onError,
}: NoteTypeCardProps) => {
  const { t } = useTranslation()

  return (
    <section className="mb-5">
      <header className="flex items-center pt-0.5 pb-2.5">
        <h3 className="truncate text-[17px] leading-[1.2] font-extrabold tracking-[-0.018em] text-ink">
          {group.noteType.name}
        </h3>
        <Pill className="ms-2.5" tone={isDeckOverride ? "sky" : "indigo"}>
          {deckName}
        </Pill>
        <button
          aria-label={t("smartFields.addToNoteType", {
            noteType: group.noteType.name,
          })}
          className="ms-1.5 inline-flex size-6 items-center justify-center rounded-md text-zinc-500 transition hover:bg-white/[0.05] hover:text-zinc-300"
          onClick={() => onCreate(group.noteType.id)}
        >
          <Plus aria-hidden className="size-3.5" />
        </button>
      </header>

      {/* Rows run edge to edge so a hovered row highlights like a table row; the card
          clips the corners. */}
      <div className="-mx-hang overflow-hidden rounded-xl bg-white/[0.05]">
        {group.fields.map((field, index) => (
          <SmartFieldRow
            field={field}
            hasDivider={index > 0}
            key={field.id}
            onDelete={onDelete}
            onDuplicate={onDuplicate}
            onEdit={onEdit}
            onError={onError}
            onToggleEnabled={onToggleEnabled}
          />
        ))}
      </div>
    </section>
  )
}
