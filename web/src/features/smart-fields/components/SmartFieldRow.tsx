import { MoreHorizontal } from "lucide-react"
import { useState } from "react"
import { useTranslation } from "react-i18next"

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
  const { t } = useTranslation()
  const [menuOpen, setMenuOpen] = useState(false)
  const [pending, setPending] = useState(false)

  const runAction = async (action: () => Promise<void>) => {
    setPending(true)
    try {
      await action()
      setMenuOpen(false)
    } catch (error) {
      onError(errorMessage(error, t("smartFields.errors.commandFailed")))
    } finally {
      setPending(false)
    }
  }

  // The edge columns hold the row's side padding (16px before the icon, 18px after
  // the menu). The prompt sits on a second line under the name.
  return (
    <div
      className={`relative grid min-h-11 grid-cols-[32px_minmax(0,1fr)_minmax(90px,132px)_46px] items-center gap-x-6 gap-y-0.5 py-2.5 max-[800px]:gap-x-[18px] ${
        field.enabled ? "" : "opacity-40"
      } ${
        hasDivider
          ? "before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-white/[0.05]"
          : ""
      }`}
    >
      <button
        aria-label={t("smartFields.editAriaLabel", {
          field: field.targetFieldName,
        })}
        className="absolute inset-0 transition hover:bg-white/[0.05] focus-visible:-outline-offset-2"
        onClick={() => onEdit(field)}
      />
      <FieldTypeIcon fieldType={field.fieldType} />
      <span className="pointer-events-none col-start-2 row-start-1 truncate text-[13px] font-medium text-[#e0dfe2]">
        {field.targetFieldName}
      </span>
      <span className="pointer-events-none col-start-2 row-start-2 truncate text-[11px] text-ink-muted">
        {smartFieldDescription(field)}
      </span>
      <span className="pointer-events-none col-start-3 row-span-2 row-start-1 min-w-0 justify-self-end text-end">
        <span className="block text-[9px] leading-none font-semibold tracking-[0.055em] text-ink-faint uppercase">
          {t("fieldEditor.modelSettings.model")}
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
            aria-label={t("smartFields.actionsAriaLabel", {
              field: field.targetFieldName,
            })}
            className="relative z-10 col-start-4 row-span-2 row-start-1 inline-flex size-7 items-center justify-center justify-self-start rounded-md text-ink-faint transition hover:bg-white/[0.07] hover:text-zinc-300 data-[state=open]:bg-white/[0.07] data-[state=open]:text-zinc-300"
            disabled={pending}
          >
            <MoreHorizontal aria-hidden className="size-4" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onSelect={() => onEdit(field)}>
            {t("common.edit")}
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => onDuplicate(field)}>
            {t("common.duplicate")}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            disabled={pending}
            onSelect={(event) => {
              event.preventDefault()
              void runAction(() => onToggleEnabled(field))
            }}
          >
            {field.enabled ? t("smartFields.disable") : t("smartFields.enable")}
          </DropdownMenuItem>
          <DropdownMenuItem
            className="text-danger"
            disabled={pending}
            onSelect={(event) => {
              event.preventDefault()
              void runAction(() => onDelete(field))
            }}
          >
            {pending ? t("smartFields.deleting") : t("common.delete")}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
