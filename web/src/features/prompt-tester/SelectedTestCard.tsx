import { AlertCircle, FileText } from "lucide-react"
import { Fragment, type ReactNode } from "react"

import { Button } from "@/components/ui/Button"
import { openAnkiBrowser } from "@/services/commands"
import type { SelectedNote, Selection } from "@/types/api"

interface SelectedTestCardProps {
  compact?: boolean
  compactAction?: ReactNode
  deckName: string
  missingFieldNames: string[]
  note: SelectedNote | null
  noteTypeName: string
  referencedFieldNames: Set<string>
  requiredNoteTypeName?: string
  selection: Selection | null
  showNoteTypeMismatch: boolean
}

// The card a test runs against: nothing picked, a picked card, or a picked card the
// prompt cannot run against — the wrong note type, or one without the fields the
// prompt references. The compact field-editor version always occupies one fixed row;
// the larger standalone version includes the selected card details.
export const SelectedTestCard = ({
  compact = false,
  compactAction,
  deckName,
  missingFieldNames,
  note,
  noteTypeName,
  referencedFieldNames,
  requiredNoteTypeName,
  selection,
  showNoteTypeMismatch,
}: SelectedTestCardProps) => {
  if (note === null) {
    return (
      <div
        className={`flex items-center gap-2.5 rounded-lg border border-dashed border-white/[0.18] px-3 ${compact ? "py-2" : "py-2.5"}`}
      >
        <FileText aria-hidden className="size-3.5 shrink-0 text-ink-muted" />
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold text-ink">
            Pick a card in the Anki Browser
          </p>
          {!compact && emptySlotHint({ requiredNoteTypeName, selection })}
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
  const firstFieldValue = Object.values(note.fields)[0]?.trim()
  const cannotRun = showNoteTypeMismatch || missingFieldNames.length > 0
  const cardTitle =
    firstFieldValue === undefined || firstFieldValue === "" ? (
      <span className="text-zinc-600 italic">(empty card)</span>
    ) : (
      firstFieldValue
    )

  if (compact && cannotRun) {
    return (
      <div className="flex h-[54px] min-w-0 items-center gap-2.5 rounded-lg border border-amber/25 bg-amber/[0.06] px-3">
        <AlertCircle aria-hidden className="size-3.5 shrink-0 text-amber" />
        {/* The row keeps its height beside the browser action, so this is one line that
            ellipsizes — what the card is missing leads, where it always survives. */}
        <p className="min-w-0 flex-1 truncate text-[11.5px] text-ink-muted">
          {showNoteTypeMismatch ? (
            <>
              Please select a note of type{" "}
              <NoteTypeName
                name={requiredNoteTypeName ?? "another note type"}
              />
            </>
          ) : (
            <>
              Needs {missingFieldNames.length === 1 ? "field" : "fields"}{" "}
              {missingFieldNames.map((fieldName, index) => (
                <Fragment key={fieldName}>
                  {index > 0 && " "}
                  <FieldName name={fieldName} />
                </Fragment>
              ))}
            </>
          )}
        </p>
        <Button
          className="shrink-0 px-3 py-[5px] text-[11.5px]"
          onClick={() => void openAnkiBrowser()}
        >
          Open Anki Browser
        </Button>
      </div>
    )
  }

  if (compact && !cannotRun) {
    return (
      <div className="h-[54px] min-w-0 rounded-lg border border-white/10 bg-white/[0.02] px-3 pt-[7px] pb-2">
        <p className="mb-[3px] text-[10px] font-medium tracking-[0.04em] text-ink-muted uppercase">
          Currently selected card
        </p>
        <div className="flex min-w-0 items-baseline gap-2">
          <p className="min-w-0 shrink truncate font-mono text-[12.5px] text-ink">
            {cardTitle}
          </p>
          <p className="min-w-0 shrink-[2] truncate text-[11px] text-zinc-500">
            · {noteTypeName} · {deckName}
          </p>
          {compactAction}
        </div>
      </div>
    )
  }

  return (
    <div
      className={`overflow-hidden rounded-lg bg-black/20 ${cannotRun ? "border border-amber/25" : "border border-white/[0.09]"}`}
    >
      <p className="truncate px-3 pt-[9px] font-mono text-[13px] text-ink">
        {cardTitle}
      </p>
      <div className="flex gap-3.5 px-3 pt-1 pb-[9px] text-[11px] text-zinc-400">
        <span className={showNoteTypeMismatch ? "text-amber" : undefined}>
          <span className="text-ink-faint">Note type</span>{" "}
          <span className={showNoteTypeMismatch ? "font-semibold" : undefined}>
            {noteTypeName}
          </span>
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

      {showNoteTypeMismatch && (
        <CardProblem title="Wrong note type">
          This field runs on{" "}
          <NoteTypeName name={requiredNoteTypeName ?? "another note type"} />
        </CardProblem>
      )}

      {!showNoteTypeMismatch && missingFieldNames.length > 0 && (
        <CardProblem
          title={`Missing field${missingFieldNames.length === 1 ? "" : "s"}`}
        >
          Please select a card type with{" "}
          {missingFieldNames.length === 1 ? "field" : "fields"}{" "}
          {missingFieldNames.map((fieldName) => (
            <FieldName key={fieldName} name={fieldName} />
          ))}
        </CardProblem>
      )}
    </div>
  )
}

// Why the picked card cannot run, docked to the bottom of the card itself, with the
// action that fixes it.
const CardProblem = ({
  children,
  title,
}: {
  children: ReactNode
  title: string
}) => (
  <div className="flex items-start gap-2.5 border-t border-amber/20 bg-amber/[0.06] px-3 py-2.5">
    <AlertCircle
      aria-hidden
      className="mt-[1px] size-3.5 shrink-0 text-amber"
    />
    <div className="min-w-0 flex-1">
      <p className="text-[11.5px] font-semibold text-amber">{title}</p>
      <p className="mt-1 flex flex-wrap items-baseline gap-x-1.5 gap-y-1 text-[11px] leading-[1.5] text-ink-muted">
        {children}
      </p>
    </div>
    <Button
      className="shrink-0 self-center px-3 py-[5px] text-[11.5px]"
      onClick={() => void openAnkiBrowser()}
    >
      Open Anki Browser
    </Button>
  </div>
)

// The line under "Pick a card in the Anki Browser". A multi-note selection is the most
// actionable thing to say; otherwise the panel states which note type this field needs.
const emptySlotHint = ({
  requiredNoteTypeName,
  selection,
}: Pick<SelectedTestCardProps, "requiredNoteTypeName" | "selection">) => {
  if (selection !== null && selection.note === null && selection.count > 1) {
    return (
      <p className="mt-0.5 text-[11px] leading-[1.5] text-ink-muted">
        {selection.count} notes selected — narrow it to one.
      </p>
    )
  }

  if (requiredNoteTypeName === undefined) {
    return (
      <p className="mt-0.5 text-[11px] leading-[1.5] text-ink-muted">
        Your selection appears here automatically.
      </p>
    )
  }

  return (
    <p className="mt-1 flex flex-wrap items-baseline gap-x-1.5 gap-y-1 text-[11px] leading-[1.5] text-ink-muted">
      This field runs on <NoteTypeName name={requiredNoteTypeName} />
    </p>
  )
}

// Anki note-type names get long and parenthesized ("Japanese (recognition) (japanese
// support)"), so a name is set apart from the sentence around it and wraps as one unit.
const NoteTypeName = ({ name }: { name: string }) => (
  <span className="rounded border border-white/10 bg-white/[0.06] px-1.5 py-px font-medium text-ink">
    {name}
  </span>
)

// A field name wears the same chip as the prompt's {{…}} references above it.
const FieldName = ({ name }: { name: string }) => (
  <span className="rounded bg-indigo/14 px-[3px] font-mono text-[11px] text-indigo-soft">
    {name}
  </span>
)
