import { MoreHorizontal } from "lucide-react"
import { useState } from "react"

import { FieldTypeIcon } from "./FieldTypeIcon"

import {
  smartFieldDescription,
  smartFieldModelLabel,
} from "../fieldPresentation"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/DropdownMenu"
import { errorMessage } from "@/lib/errors"
import type { SmartField } from "@/types/api"

interface SmartFieldRowProps {
  field: SmartField
  hasDivider: boolean
  onDelete: (field: SmartField) => Promise<void>
  onDuplicate: (field: SmartField) => void
  onEdit: (field: SmartField) => void
  onToggleEnabled: (field: SmartField) => Promise<void>
  onError: (message: string) => void
}

export const SmartFieldRow = ({
  field,
  hasDivider,
  onDelete,
  onDuplicate,
  onEdit,
  onToggleEnabled,
  onError,
}: SmartFieldRowProps) => {
  const [menuOpen, setMenuOpen] = useState(false)
  const [pending, setPending] = useState(false)

  const runAction = async (action: () => Promise<void>) => {
    setPending(true)
    try {
      await action()
      setMenuOpen(false)
    } catch (error) {
      onError(errorMessage(error, "Smart Field command failed"))
    } finally {
      setPending(false)
    }
  }

  return (
    <div
      className={`relative grid min-h-11 grid-cols-[22px_120px_minmax(80px,1fr)_132px_28px] items-center gap-[9px] rounded-[7px] py-2 pr-2.5 pl-[18px] max-[800px]:grid-cols-[22px_minmax(80px,1fr)_minmax(100px,130px)_28px] ${
        field.enabled ? "" : "opacity-40"
      } ${
        hasDivider
          ? "before:absolute before:top-0 before:right-2.5 before:left-2.5 before:h-px before:bg-white/[0.05]"
          : ""
      }`}
    >
      <button
        aria-label={`Edit ${field.targetFieldName} Smart Field`}
        className="absolute inset-0 rounded-[7px] transition hover:bg-white/[0.05]"
        onClick={() => onEdit(field)}
      />
      <FieldTypeIcon fieldType={field.fieldType} />
      <span className="pointer-events-none truncate text-[13px] font-medium text-[#cfcfd6]">
        {field.targetFieldName}
      </span>
      <span className="pointer-events-none truncate text-[11px] text-ink-muted max-[800px]:hidden">
        {smartFieldDescription(field)}
      </span>
      <span className="pointer-events-none min-w-0 justify-self-end text-right">
        <span className="block text-[9px] leading-none font-semibold tracking-[0.055em] text-ink-faint uppercase">
          Model
        </span>
        <span
          className={`mt-[3px] block truncate text-[11px] ${
            field.settings.usesDefaultGenerationSettings
              ? "text-indigo-soft"
              : "text-zinc-400"
          }`}
        >
          {smartFieldModelLabel(field)}
        </span>
      </span>

      <DropdownMenu onOpenChange={setMenuOpen} open={menuOpen}>
        <DropdownMenuTrigger asChild>
          <button
            aria-label={`Actions for ${field.targetFieldName}`}
            className="relative z-10 inline-flex size-7 items-center justify-center justify-self-end rounded-md text-ink-faint transition hover:bg-white/[0.07] hover:text-zinc-300"
            disabled={pending}
          >
            <MoreHorizontal aria-hidden className="size-4" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onSelect={() => onEdit(field)}>
            Edit
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => onDuplicate(field)}>
            Duplicate
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            disabled={pending}
            onSelect={(event) => {
              event.preventDefault()
              void runAction(() => onToggleEnabled(field))
            }}
          >
            {field.enabled ? "Disable" : "Enable"}
          </DropdownMenuItem>
          <DropdownMenuItem
            className="text-danger"
            disabled={pending}
            onSelect={(event) => {
              event.preventDefault()
              void runAction(() => onDelete(field))
            }}
          >
            {pending ? "Deleting…" : "Delete"}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
