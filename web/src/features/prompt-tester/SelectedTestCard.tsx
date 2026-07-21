import { FileText } from "lucide-react"

import { Button } from "@/components/ui/Button"
import { openAnkiBrowser } from "@/services/commands"
import type { SelectedNote, Selection } from "@/types/api"

interface SelectedTestCardProps {
  deckName: string
  note: SelectedNote | null
  noteTypeName: string
  referencedFieldNames: Set<string>
  selection: Selection | null
}

export const SelectedTestCard = ({
  deckName,
  note,
  noteTypeName,
  referencedFieldNames,
  selection,
}: SelectedTestCardProps) => {
  if (note === null) {
    return (
      <div className="flex items-center gap-2.5 rounded-lg border border-dashed border-white/[0.18] px-3 py-2.5">
        <FileText aria-hidden className="size-3.5 shrink-0 text-ink-muted" />
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold text-ink">
            Pick a card in the Anki Browser
          </p>
          <p className="mt-0.5 text-[11px] leading-[1.5] text-ink-muted">
            {selection !== null &&
            selection.note === null &&
            selection.count > 1
              ? `${selection.count} notes selected — narrow it to one.`
              : "Your selection appears here automatically."}
          </p>
        </div>
        <Button
          className="shrink-0 px-3 py-[5px] text-[11.5px]"
          onClick={() => void openAnkiBrowser()}
        >
          Open Anki Browser
        </Button>
      </div>
    )
  }

  const referencedFields = Object.entries(note.fields).filter(([fieldName]) =>
    referencedFieldNames.has(fieldName),
  )

  return (
    <div className="rounded-lg border border-white/[0.09] bg-black/20">
      <p className="truncate px-3 pt-[9px] font-mono text-[13px] text-ink">
        {Object.values(note.fields)[0] ?? "(empty card)"}
      </p>
      <div className="flex gap-3.5 px-3 pt-1 pb-[9px] text-[11px] text-zinc-400">
        <span>
          <span className="text-ink-faint">Note type</span> {noteTypeName}
        </span>
        <span className="truncate">
          <span className="text-ink-faint">Deck</span> {deckName}
        </span>
      </div>
      {referencedFields.length > 0 && (
        <div className="flex flex-col gap-[5px] border-t border-white/[0.06] px-3 pt-[7px] pb-[9px]">
          {referencedFields.map(([fieldName, value]) => (
            <div
              className="flex gap-2.5 text-[11.5px] leading-[1.4]"
              key={fieldName}
            >
              <span className="shrink-0 rounded bg-indigo/14 px-[3px] font-mono text-[11px] text-indigo-soft">
                {fieldName}
              </span>
              {value === "" ? (
                <span className="text-zinc-600 italic">empty</span>
              ) : (
                <span className="truncate text-zinc-200">{value}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
