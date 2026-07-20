import { FlaskConical } from "lucide-react"
import { useState } from "react"

import { setMockFixture } from "./mockData"

const FIXTURES = [
  { id: "populated", label: "Trial" },
  { id: "paid", label: "Paid" },
  { id: "signed-out", label: "Signed out" },
  { id: "empty", label: "Empty" },
  { id: "reconnecting", label: "Offline" },
]

const MockPanel = () => {
  const [activeFixture, setActiveFixture] = useState(
    () =>
      new URLSearchParams(window.location.search).get("fixture") ?? "populated",
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
    </aside>
  )
}

export default MockPanel
