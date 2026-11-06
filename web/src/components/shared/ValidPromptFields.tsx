import { useTranslation } from "react-i18next"

const CHIP = "rounded bg-indigo/14 px-[3px] font-mono text-xs text-indigo-soft"

interface ValidPromptFieldsProps {
  fieldNames: string[]
  label?: string
  // Makes each reference a button that inserts it into the prompt.
  onInsert?: (reference: string) => void
}

/** The {{Field}} references a prompt may use, listed under the box it is written in. */
export const ValidPromptFields = ({
  fieldNames,
  label,
  onInsert,
}: ValidPromptFieldsProps) => {
  const { t } = useTranslation()
  if (fieldNames.length === 0) return null

  return (
    <p className="mt-2 flex flex-wrap items-center gap-x-1.5 gap-y-1 text-xs leading-[1.5] text-ink-muted">
      {label ?? t("common.validFields")}
      {fieldNames.map((fieldName) => {
        const reference = `{{${fieldName}}}`
        return onInsert === undefined ? (
          <span className={CHIP} key={fieldName}>
            {reference}
          </span>
        ) : (
          <button
            aria-label={t("fieldEditor.promptPanel.insertField", {
              field: fieldName,
            })}
            className={`${CHIP} cursor-pointer transition hover:bg-indigo/25`}
            key={fieldName}
            onClick={() => onInsert(reference)}
            // Keeps the cursor in the prompt so the reference lands where it was.
            onMouseDown={(event) => event.preventDefault()}
            type="button"
          >
            {reference}
          </button>
        )
      })}
    </p>
  )
}
