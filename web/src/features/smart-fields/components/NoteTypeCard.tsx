import { ChevronDown, FileText, Plus } from "lucide-react"
import { useState } from "react"

import { SmartFieldRow } from "./SmartFieldRow"

import { Card } from "@/components/ui/Card"
import type { SmartField } from "@/types/api"

import type { NoteTypeGroup } from "../groupSmartFields"

interface NoteTypeCardProps {
  group: NoteTypeGroup
  onCreate: (noteTypeId: number) => void
  onDelete: (field: SmartField) => Promise<void>
  onDuplicate: (field: SmartField) => void
  onEdit: (field: SmartField) => void
  onToggleEnabled: (field: SmartField) => Promise<void>
  onError: (message: string) => void
}

export const NoteTypeCard = ({
  group,
  onCreate,
  onDelete,
  onDuplicate,
  onEdit,
  onToggleEnabled,
  onError,
}: NoteTypeCardProps) => {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <Card as="section" className="mb-5">
      <header
        className={`flex items-center gap-2.5 bg-white/[0.035] px-3.5 py-2.5 ${
          collapsed ? "rounded-xl" : "rounded-t-xl border-b border-white/[0.07]"
        }`}
      >
        <FileText aria-hidden className="size-3.5 text-zinc-500" />
        <div className="min-w-0 flex-1">
          <p className="text-[8px] leading-none font-semibold tracking-[0.1em] text-ink-faint uppercase">
            Note type
          </p>
          <h3 className="mt-1 truncate text-[12.5px] leading-none font-semibold text-zinc-100">
            {group.noteType.name}
          </h3>
        </div>
        <button
          aria-label={`Add Smart Field to ${group.noteType.name}`}
          className="inline-flex size-6 items-center justify-center rounded text-zinc-500 transition hover:bg-white/[0.05] hover:text-zinc-300"
          onClick={() => onCreate(group.noteType.id)}
        >
          <Plus aria-hidden className="size-3.5" />
        </button>
        <button
          aria-expanded={!collapsed}
          aria-label={`${collapsed ? "Expand" : "Collapse"} ${group.noteType.name}`}
          className="inline-flex size-6 items-center justify-center rounded text-zinc-500 transition hover:bg-white/[0.05] hover:text-zinc-300"
          onClick={() => setCollapsed((value) => !value)}
        >
          <ChevronDown
            aria-hidden
            className={`size-3.5 transition ${collapsed ? "-rotate-90" : ""}`}
          />
        </button>
      </header>

      {!collapsed && (
        <div className="p-1">
          {group.fields.map((field) => (
            <SmartFieldRow
              field={field}
              key={field.id}
              onDelete={onDelete}
              onDuplicate={onDuplicate}
              onEdit={onEdit}
              onError={onError}
              onToggleEnabled={onToggleEnabled}
            />
          ))}
        </div>
      )}
    </Card>
  )
}
