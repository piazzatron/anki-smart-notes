interface ValidPromptFieldsProps {
  fieldNames: string[]
}

/** The {{Field}} references a prompt may use, listed under the box it is written in. */
export const ValidPromptFields = ({ fieldNames }: ValidPromptFieldsProps) => {
  if (fieldNames.length === 0) return null

  return (
    <p className="mt-2 flex flex-wrap items-center gap-x-1.5 gap-y-1 text-[11px] leading-[1.5] text-ink-muted">
      Valid fields:
      {fieldNames.map((fieldName) => (
        <span
          className="rounded bg-indigo/14 px-[3px] font-mono text-[11px] text-indigo-soft"
          key={fieldName}
        >
          {`{{${fieldName}}}`}
        </span>
      ))}
    </p>
  )
}
