import { useStore } from "./store"

// The session token arrives once via the webview URL; EventSource can't set
// headers, so it rides as a query param.
const token = new URLSearchParams(window.location.search).get("token") ?? ""

export function connectToAnki(): void {
  const es = new EventSource(`/api/events?token=${encodeURIComponent(token)}`)

  es.addEventListener("state", (e) => {
    useStore.setState({ state: JSON.parse(e.data), connection: "connected" })
  })

  es.addEventListener("anki.browserSelectionChanged", (e) => {
    useStore.setState({ selection: JSON.parse(e.data) })
  })

  es.onopen = () => useStore.setState({ connection: "connected" })

  es.onerror = () => {
    useStore.setState({ connection: "reconnecting" })
    // EventSource auto-reconnects on transient errors, but a rejected
    // connection (e.g. 401) closes it for good — recreate after a beat.
    if (es.readyState === EventSource.CLOSED) {
      setTimeout(connectToAnki, 2000)
    }
  }
}
