import { FlaskConical } from "lucide-react"
import { useState } from "react"

import type { FieldEditorRequest } from "@/features/field-editor/FieldEditorScreen"
import { bootOptions } from "@/lib/boot"

import { setMockFixture, setMockSelection } from "./mockData"

const FIXTURES = [
  { id: "populated", label: "Trial (default)" },
  { id: "signed-out-empty", label: "Welcome" },
  { id: "trial-healthy", label: "Trial · healthy" },
  { id: "trial-ending", label: "Trial · ending" },
  { id: "trial-expired", label: "Trial · expired" },
  { id: "trial-capacity", label: "Trial · capacity" },
  { id: "free", label: "Free · post-trial" },
  { id: "paid", label: "Paid" },
  { id: "paid-expired", label: "Paid · expired" },
  { id: "paid-capacity", label: "Paid · capacity" },
  { id: "signed-out", label: "Signed out" },
  { id: "loading", label: "Loading" },
  { id: "empty", label: "Empty" },
  { id: "reconnecting", label: "Offline" },
]

const SELECTIONS = [
  { id: "selected", label: "One card" },
  { id: "none", label: "No card" },
  { id: "multiple", label: "3 cards" },
  { id: "mismatch", label: "Wrong note type" },
]

interface MockPanelProps {
  onOpenEditor: (editor: FieldEditorRequest) => void
}

const MockPanel = ({ onOpenEditor }: MockPanelProps) => {
  const [activeFixture, setActiveFixture] = useState(bootOptions.fixture)
  const [activeSelection, setActiveSelection] = useState(bootOptions.selection)
  const [editorStep, setEditorStep] = useState<1 | 2 | 3>(
    bootOptions.editorStep ?? 1,
  )

  return (
    <aside className="fixed right-3 bottom-3 z-50 w-48 rounded-lg border border-indigo/25 bg-panel-raised/95 p-2.5 shadow-2xl shadow-black/60">
      <div className="mb-2 flex items-center gap-1.5 text-[10px] font-semibold tracking-wide text-indigo-soft uppercase">
        <FlaskConical aria-hidden className="size-3.5" />
        Mock state
      </div>
      <label className="block text-[9px] font-semibold tracking-wide text-ink-faint uppercase">
        Fixture
        <select
          className="mt-1 w-full rounded border border-white/[0.08] bg-panel px-2 py-1.5 text-[10px] font-normal tracking-normal text-zinc-300 normal-case outline-none focus:border-indigo/50"
          onChange={(event) => {
            setActiveFixture(event.target.value)
            setMockFixture(event.target.value)
          }}
          value={activeFixture}
        >
          {FIXTURES.map((fixture) => (
            <option key={fixture.id} value={fixture.id}>
              {fixture.label}
            </option>
          ))}
        </select>
      </label>
      <div className="mt-2 border-t border-white/[0.07] pt-2">
        <p className="mb-1.5 text-[9px] font-semibold tracking-wide text-ink-faint uppercase">
          Browser selection
        </p>
        <div className="grid grid-cols-3 gap-1">
          {SELECTIONS.map((selection) => (
            <button
              className={`rounded px-1 py-1.5 text-[9px] transition ${
                selection.id === activeSelection
                  ? "bg-indigo/20 text-indigo-soft"
                  : "bg-white/[0.035] text-zinc-400 hover:bg-white/[0.065]"
              }`}
              key={selection.id}
              onClick={() => {
                setActiveSelection(selection.id)
                setMockSelection(selection.id)
              }}
            >
              {selection.label}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-2 border-t border-white/[0.07] pt-2">
        <div className="mb-1.5 flex items-center justify-between gap-2">
          <p className="text-[9px] font-semibold tracking-wide text-ink-faint uppercase">
            Field editor
          </p>
          <label className="flex items-center gap-1 text-[9px] text-zinc-500">
            Step
            <select
              className="rounded border border-white/[0.08] bg-panel px-1 py-0.5 text-zinc-300 outline-none focus:border-indigo/50"
              onChange={(event) =>
                setEditorStep(Number(event.target.value) as 1 | 2 | 3)
              }
              value={editorStep}
            >
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
            </select>
          </label>
        </div>
        <div className="grid grid-cols-3 gap-1">
          {(["create", "edit", "duplicate"] as const).map((mode) => (
            <button
              className="rounded bg-white/[0.035] px-1 py-1.5 text-[9px] text-zinc-400 capitalize transition hover:bg-white/[0.065]"
              key={mode}
              onClick={() => onOpenEditor({ mode, step: editorStep })}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}

export default MockPanel
