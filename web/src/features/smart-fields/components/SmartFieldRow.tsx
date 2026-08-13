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
  onDelete: (field: SmartField) => Promise<void>
  onDuplicate: (field: SmartField) => void
  onEdit: (field: SmartField) => void
  onToggleEnabled: (field: SmartField) => Promise<void>
  onError: (message: string) => void
}

export const SmartFieldRow = ({
  field,
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
      className={`relative grid min-h-11 cursor-pointer grid-cols-[22px_minmax(80px,120px)_minmax(80px,1fr)_minmax(110px,150px)_28px] items-center gap-2.5 rounded-md px-2.5 py-2 transition hover:bg-white/[0.04] max-[800px]:grid-cols-[22px_minmax(80px,1fr)_minmax(100px,130px)_28px] ${
        field.enabled ? "" : "opacity-40"
      }`}
    >
      <FieldTypeIcon fieldType={field.fieldType} />
      <span className="truncate font-mono text-xs text-zinc-200">
        {field.targetFieldName}
      </span>
      <span className="truncate text-[11px] text-ink-muted max-[800px]:hidden">
        {smartFieldDescription(field)}
      </span>
      <span className="min-w-0 justify-self-end text-right">
        <span className="block text-[8px] leading-none font-semibold tracking-[0.1em] text-ink-faint uppercase">
          Model
        </span>
        <span
          className={`mt-1 block truncate text-[10.5px] ${
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
            className="inline-flex size-7 items-center justify-center justify-self-end rounded-md text-ink-faint transition hover:bg-white/[0.07] hover:text-zinc-300"
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
