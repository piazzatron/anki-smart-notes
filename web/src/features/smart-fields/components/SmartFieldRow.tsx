import { MoreHorizontal } from "lucide-react"
import { useState } from "react"
import { Trans, useTranslation } from "react-i18next"

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
import {
  openUpgradeSheet,
  UpgradeLockIcon,
  useIsFreePlan,
} from "@/components/shared/UpgradeSheet"
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
  // The free plan is text only: its voice and image fields stay listed, greyed
  // out with a lock, and open the upgrade sheet instead of the editor.
  const isFree = useIsFreePlan()
  const locked = isFree && field.fieldType !== "chat"
  const model = smartFieldModelLabel(field, isFree)
  const openUpgrade = () =>
    openUpgradeSheet(field.fieldType === "tts" ? "voice" : "images")
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

  // The edge columns hold the row's side padding: the icon sits as far from the card
  // edge as from the text (one column gap), and the menu 18px from the right edge.
  // The prompt sits on a second line under the name.
  return (
    <div
      className={`relative grid min-h-11 grid-cols-[40px_minmax(0,1fr)_minmax(90px,180px)_46px] items-center gap-x-6 gap-y-1 py-3 max-[800px]:grid-cols-[34px_minmax(0,1fr)_minmax(90px,180px)_46px] max-[800px]:gap-x-[18px] ${
        !field.enabled || locked ? "opacity-40" : ""
      } ${
        hasDivider
          ? "before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-hairline"
          : ""
      }`}
    >
      <button
        aria-label={t(
          locked ? "smartFields.lockedAriaLabel" : "smartFields.editAriaLabel",
          { field: field.targetFieldName },
        )}
        className="absolute inset-0 transition hover:bg-white/[0.05] focus-visible:-outline-offset-2"
        onClick={() => (locked ? openUpgrade() : onEdit(field))}
      />
      <FieldTypeIcon fieldType={field.fieldType} />
      <span className="pointer-events-none col-start-2 row-start-1 flex min-w-0 items-center gap-1.5 text-sm leading-4 font-medium text-ink">
        <span className="truncate">{field.targetFieldName}</span>
        {locked && <UpgradeLockIcon />}
      </span>
      <span className="pointer-events-none col-start-2 row-start-2 truncate text-xs leading-[14px] text-ink-muted">
        {smartFieldDescription(field)}
      </span>
      {/* The model name truncates; the default marker after it never does. */}
      <span
        className={`pointer-events-none col-start-3 row-span-2 row-start-1 flex min-w-0 justify-end text-xs whitespace-pre ${
          field.settings.usesDefaultGenerationSettings
            ? "text-indigo-soft"
            : "text-ink-muted"
        }`}
      >
        {field.settings.usesDefaultGenerationSettings ? (
          <Trans
            components={{ model: <span className="truncate" /> }}
            i18nKey="smartFields.followsDefault"
            values={{ model }}
          />
        ) : (
          <span className="truncate">{model}</span>
        )}
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
          <DropdownMenuItem
            onSelect={() => (locked ? openUpgrade() : onEdit(field))}
          >
            {t("common.edit")}
          </DropdownMenuItem>
          <DropdownMenuItem
            onSelect={() => (locked ? openUpgrade() : onDuplicate(field))}
          >
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
