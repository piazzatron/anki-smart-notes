import { useStore } from "./store"
import type { Selection, SmartField } from "./types"

// Deliberately unstyled-skeleton UI: this proves the data flow end-to-end.
// Real screens replace this wholesale.

export default function App() {
  const connection = useStore((s) => s.connection)
  const state = useStore((s) => s.state)
  const selection = useStore((s) => s.selection)

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", margin: "2rem", lineHeight: 1.5 }}>
      <header style={{ display: "flex", alignItems: "baseline", gap: "1rem" }}>
        <h1 style={{ margin: 0 }}>Smart Notes</h1>
        <ConnectionBadge connection={connection} />
      </header>

      <section>
        <h2>Smart Fields</h2>
        {state === null ? (
          <p>Waiting for state…</p>
        ) : state.smartFields.length === 0 ? (
          <p>No smart fields configured.</p>
        ) : (
          <ul>
            {state.smartFields.map((field) => (
              <SmartFieldRow key={field.id} field={field} />
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Anki Browser Selection</h2>
        <SelectionPanel selection={selection} />
      </section>
    </main>
  )
}

function ConnectionBadge({ connection }: { connection: string }) {
  const color = connection === "connected" ? "#16a34a" : "#d97706"
  return (
    <span style={{ color, fontWeight: 600 }}>
      ● {connection}
    </span>
  )
}

function SmartFieldRow({ field }: { field: SmartField }) {
  return (
    <li>
      <strong>{field.targetFieldName}</strong> — {field.fieldType}
      {field.enabled ? "" : " (disabled)"}
      <details>
        <summary>settings</summary>
        <pre style={{ background: "#f4f4f5", padding: "0.5rem" }}>
          {JSON.stringify(field, null, 2)}
        </pre>
      </details>
    </li>
  )
}

function SelectionPanel({ selection }: { selection: Selection | null }) {
  if (selection === null) {
    return <p>Select a note in the Anki browser to see it here.</p>
  }
  if (selection.note === null) {
    return <p>{selection.count} notes selected.</p>
  }
  return (
    <table style={{ borderCollapse: "collapse" }}>
      <tbody>
        {Object.entries(selection.note.fields).map(([name, value]) => (
          <tr key={name}>
            <td style={{ border: "1px solid #d4d4d8", padding: "0.25rem 0.75rem", fontWeight: 600 }}>
              {name}
            </td>
            <td
              style={{ border: "1px solid #d4d4d8", padding: "0.25rem 0.75rem" }}
              dangerouslySetInnerHTML={{ __html: value }}
            />
          </tr>
        ))}
      </tbody>
    </table>
  )
}
