import { AlertCircle, FileText } from "lucide-react"
import i18next from "i18next"
import { Fragment, type ReactNode } from "react"
import { Trans, useTranslation } from "react-i18next"

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
  referencedFields: [string, string][]
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
  referencedFields,
  requiredNoteTypeName,
  selection,
  showNoteTypeMismatch,
}: SelectedTestCardProps) => {
  const { t } = useTranslation()
  if (note === null) {
    return (
      <>
        <Button
          className={`w-full gap-2 text-[13px] ${compact ? "h-full" : "py-2.5"}`}
          onClick={() => void openAnkiBrowser()}
        >
          <FileText aria-hidden className="size-3.5 shrink-0" />
          {t("promptTester.selectCardInBrowser")}
        </Button>
        {!compact && emptySlotHint({ requiredNoteTypeName, selection })}
      </>
    )
  }

  const firstFieldValue = Object.values(note.fields)[0]?.trim()
  const cannotRun = showNoteTypeMismatch || missingFieldNames.length > 0
  const cardTitle =
    firstFieldValue === undefined || firstFieldValue === "" ? (
      <span className="text-ink-muted italic">
        {t("promptTester.emptyCard")}
      </span>
    ) : (
      firstFieldValue
    )

  if (compact && cannotRun) {
    return (
      <div className="flex h-[54px] min-w-0 items-center gap-2.5 rounded-lg bg-caution/[0.08] px-3">
        <AlertCircle
          aria-hidden
          className="size-3.5 shrink-0 text-caution-soft"
        />
        {/* The row keeps its height beside the browser action, so this is one line that
            ellipsizes — what the card is missing leads, where it always survives. */}
        <p className="min-w-0 flex-1 truncate text-[12.5px] text-ink-muted">
          {showNoteTypeMismatch ? (
            <Trans
              components={{ noteTypeName: <NoteTypeName /> }}
              i18nKey="promptTester.selectRequiredNoteType"
              values={{
                noteType:
                  requiredNoteTypeName ?? t("promptTester.anotherNoteType"),
              }}
            />
          ) : (
            <>
              {t("promptTester.needsFields", {
                count: missingFieldNames.length,
              })}{" "}
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
          className="shrink-0 px-3 py-[5px] text-[12.5px]"
          onClick={() => void openAnkiBrowser()}
        >
          {t("promptTester.selectNewCard")}
        </Button>
      </div>
    )
  }

  if (compact && !cannotRun) {
    return (
      <div className="flex h-[54px] min-w-0 items-center gap-3 rounded-lg bg-white/[0.04] px-3">
        <div className="min-w-0 flex-1">
          <p className="mb-[3px] text-[11px] font-medium tracking-[0.04em] text-ink-muted uppercase">
            {t("promptTester.currentlySelectedCard")}
          </p>
          <div className="flex min-w-0 items-baseline gap-2">
            <p className="min-w-0 shrink truncate font-mono text-[13.5px] text-ink">
              {cardTitle}
            </p>
            <p className="min-w-0 shrink-[2] truncate text-xs text-zinc-500">
              · {noteTypeName} · {deckName}
            </p>
            {compactAction}
          </div>
        </div>
        <Button
          className="shrink-0 px-3 py-[5px] text-[12.5px]"
          onClick={() => void openAnkiBrowser()}
        >
          {t("promptTester.selectNewCard")}
        </Button>
      </div>
    )
  }

  return (
    <div
      className={`overflow-hidden rounded-lg ${cannotRun ? "bg-caution/[0.06]" : "bg-white/[0.04]"}`}
    >
      <p className="truncate px-3 pt-[9px] font-mono text-sm text-ink">
        {cardTitle}
      </p>
      <div className="flex gap-3.5 px-3 pt-1 pb-[9px] text-xs text-zinc-400">
        <span
          className={showNoteTypeMismatch ? "text-caution-soft" : undefined}
        >
          <span className="text-ink-muted">{t("common.noteType")}</span>{" "}
          <span className={showNoteTypeMismatch ? "font-semibold" : undefined}>
            {noteTypeName}
          </span>
        </span>
        <span className="truncate">
          <span className="text-ink-muted">{t("common.deck")}</span> {deckName}
        </span>
      </div>

      {referencedFields.length > 0 && (
        <div className="flex flex-col gap-[5px] border-t border-hairline px-3 pt-[7px] pb-[9px]">
          {referencedFields.map(([fieldName, value]) => (
            <div
              className="flex gap-2.5 text-[12.5px] leading-[1.4]"
              key={fieldName}
            >
              <span className="shrink-0 rounded bg-indigo/14 px-[3px] font-mono text-xs text-indigo-soft">
                {fieldName}
              </span>
              {value === "" ? (
                <span className="text-ink-muted italic">
                  {t("common.empty")}
                </span>
              ) : (
                <span className="truncate text-zinc-200">{value}</span>
              )}
            </div>
          ))}
        </div>
      )}

      {showNoteTypeMismatch && (
        <CardProblem title={t("promptTester.wrongNoteType")}>
          <Trans
            components={{ noteTypeName: <NoteTypeName /> }}
            i18nKey="promptTester.fieldRunsOnNoteType"
            values={{
              noteType:
                requiredNoteTypeName ?? t("promptTester.anotherNoteType"),
            }}
          />
        </CardProblem>
      )}

      {!showNoteTypeMismatch && missingFieldNames.length > 0 && (
        <CardProblem
          title={t("promptTester.missingFieldsTitle", {
            count: missingFieldNames.length,
          })}
        >
          <Trans
            count={missingFieldNames.length}
            i18nKey="promptTester.selectCardWithFields"
          />
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
  <div className="flex items-start gap-2.5 bg-caution/[0.08] px-3 py-2.5">
    <AlertCircle
      aria-hidden
      className="mt-[1px] size-3.5 shrink-0 text-caution-soft"
    />
    <div className="min-w-0 flex-1">
      <p className="text-[12.5px] font-semibold text-caution-soft">{title}</p>
      <p className="mt-1 flex flex-wrap items-baseline gap-x-1.5 gap-y-1 text-xs leading-[1.5] text-ink-muted">
        {children}
      </p>
    </div>
    <Button
      className="shrink-0 self-center px-3 py-[5px] text-[12.5px]"
      onClick={() => void openAnkiBrowser()}
    >
      {i18next.t("promptTester.selectNewCard")}
    </Button>
  </div>
)

// The line under the select-a-card button. A multi-note selection is the most
// actionable thing to say; otherwise the panel states which note type this field needs.
const emptySlotHint = ({
  requiredNoteTypeName,
  selection,
}: Pick<SelectedTestCardProps, "requiredNoteTypeName" | "selection">) => {
  if (selection !== null && selection.note === null && selection.count > 1) {
    return (
      <p className="mt-0.5 text-xs leading-[1.5] text-ink-muted">
        {i18next.t("promptTester.notesSelected", { count: selection.count })}
      </p>
    )
  }

  if (requiredNoteTypeName === undefined) {
    return (
      <p className="mt-0.5 text-xs leading-[1.5] text-ink-muted">
        {i18next.t("promptTester.selectionAppearsAutomatically")}
      </p>
    )
  }

  return (
    <p className="mt-1 flex flex-wrap items-baseline gap-x-1.5 gap-y-1 text-xs leading-[1.5] text-ink-muted">
      <Trans
        components={{ noteTypeName: <NoteTypeName /> }}
        i18nKey="promptTester.fieldRunsOnNoteType"
        values={{ noteType: requiredNoteTypeName }}
      />
    </p>
  )
}

// Anki note-type names get long and parenthesized ("Japanese (recognition) (japanese
// support)"), so a name is set apart from the sentence around it and wraps as one unit.
const NoteTypeName = ({ children }: { children?: ReactNode }) => (
  <span className="rounded bg-white/[0.08] px-1.5 py-px font-medium text-ink">
    {children}
  </span>
)

// A field name wears the same chip as the prompt's {{…}} references above it.
const FieldName = ({ name }: { name: string }) => (
  <span className="rounded bg-indigo/14 px-[3px] font-mono text-xs text-indigo-soft">
    {name}
  </span>
)
