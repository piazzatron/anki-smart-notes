import { FlaskConical } from "lucide-react"
import { useState } from "react"

import { setMockFixture, setMockSelection } from "./mockData"

const FIXTURES = [
  { id: "populated", label: "Trial" },
  { id: "paid", label: "Paid" },
  { id: "signed-out", label: "Signed out" },
  { id: "empty", label: "Empty" },
  { id: "reconnecting", label: "Offline" },
]

const SELECTIONS = [
  { id: "selected", label: "One card" },
  { id: "none", label: "No card" },
  { id: "multiple", label: "3 cards" },
]

const MockPanel = () => {
  const [activeFixture, setActiveFixture] = useState(
    () =>
      new URLSearchParams(window.location.search).get("fixture") ?? "populated",
  )
  const [activeSelection, setActiveSelection] = useState(
    () =>
      new URLSearchParams(window.location.search).get("selection") ??
      "selected",
  )

  return (
    <aside className="fixed right-3 bottom-3 z-50 w-48 rounded-lg border border-indigo/25 bg-panel-raised/95 p-2.5 shadow-2xl shadow-black/60 backdrop-blur">
      <div className="mb-2 flex items-center gap-1.5 text-[10px] font-semibold tracking-wide text-indigo-soft uppercase">
        <FlaskConical aria-hidden className="size-3.5" />
        Mock state
      </div>
      <div className="grid grid-cols-2 gap-1">
        {FIXTURES.map((fixture) => (
          <button
            className={`rounded px-2 py-1.5 text-[10px] transition ${
              fixture.id === activeFixture
                ? "bg-indigo/20 text-indigo-soft"
                : "bg-white/[0.035] text-zinc-400 hover:bg-white/[0.065]"
            }`}
            key={fixture.id}
            onClick={() => {
              setActiveFixture(fixture.id)
              setMockFixture(fixture.id)
            }}
          >
            {fixture.label}
          </button>
        ))}
      </div>
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
    </aside>
  )
}

export default MockPanel
