import { MoreHorizontal } from "lucide-react"
import { useEffect, useRef, useState } from "react"

import { FieldTypeIcon } from "./FieldTypeIcon"

import {
  smartFieldDescription,
  smartFieldModelLabel,
} from "../fieldPresentation"
import type { SmartField } from "../types"

interface SmartFieldRowProps {
  field: SmartField
  onDelete: (field: SmartField) => Promise<void>
  onToggleEnabled: (field: SmartField) => Promise<void>
  onError: (message: string) => void
}

export const SmartFieldRow = ({
  field,
  onDelete,
  onToggleEnabled,
  onError,
}: SmartFieldRowProps) => {
  const [menuOpen, setMenuOpen] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [pending, setPending] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!menuOpen) return

    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) setMenuOpen(false)
    }
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenuOpen(false)
    }

    document.addEventListener("mousedown", closeOnOutsideClick)
    document.addEventListener("keydown", closeOnEscape)
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick)
      document.removeEventListener("keydown", closeOnEscape)
    }
  }, [menuOpen])

  const runAction = async (action: () => Promise<void>) => {
    setPending(true)
    try {
      await action()
      setMenuOpen(false)
      setConfirmingDelete(false)
    } catch (error) {
      onError(
        error instanceof Error ? error.message : "Smart Field command failed",
      )
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

      <div className="relative justify-self-end" ref={menuRef}>
        <button
          aria-expanded={menuOpen}
          aria-haspopup="menu"
          aria-label={`Actions for ${field.targetFieldName}`}
          className="inline-flex size-7 items-center justify-center rounded-md text-ink-faint transition hover:bg-white/[0.07] hover:text-zinc-300"
          disabled={pending}
          onClick={() => {
            setConfirmingDelete(false)
            setMenuOpen((open) => !open)
          }}
        >
          <MoreHorizontal aria-hidden className="size-4" />
        </button>

        {menuOpen && (
          <div
            className="absolute top-8 right-0 z-20 min-w-40 rounded-lg border border-white/10 bg-panel-raised p-1 shadow-2xl shadow-black/50"
            role="menu"
          >
            {confirmingDelete ? (
              <div className="p-2">
                <p className="max-w-44 text-[11px] leading-4 text-zinc-300">
                  Delete <strong>{field.targetFieldName}</strong>?
                </p>
                <div className="mt-2 flex justify-end gap-1.5">
                  <button
                    className="rounded px-2 py-1 text-[10px] text-zinc-400 hover:bg-white/[0.06]"
                    onClick={() => setConfirmingDelete(false)}
                  >
                    Cancel
                  </button>
                  <button
                    className="rounded bg-red-300/10 px-2 py-1 text-[10px] font-semibold text-danger hover:bg-red-300/15"
                    disabled={pending}
                    onClick={() => void runAction(() => onDelete(field))}
                  >
                    {pending ? "Deleting…" : "Delete"}
                  </button>
                </div>
              </div>
            ) : (
              <>
                <button
                  className="w-full rounded px-2.5 py-1.5 text-left text-xs text-zinc-300 hover:bg-white/[0.07]"
                  disabled={pending}
                  role="menuitem"
                  onClick={() => void runAction(() => onToggleEnabled(field))}
                >
                  {field.enabled ? "Disable" : "Enable"}
                </button>
                <button
                  className="w-full rounded px-2.5 py-1.5 text-left text-xs text-danger hover:bg-white/[0.07]"
                  role="menuitem"
                  onClick={() => setConfirmingDelete(true)}
                >
                  Delete
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
