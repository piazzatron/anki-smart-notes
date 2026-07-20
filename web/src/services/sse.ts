import { useAppStore } from "@/store/appStore"
import type { AppState, Catalog, Selection } from "@/store/appStore"

const sessionToken =
  new URLSearchParams(window.location.search).get("token") ?? ""

export const connectToAnki = (): (() => void) => {
  let source: EventSource | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let stopped = false

  const connect = () => {
    source = new EventSource(
      `/api/events?token=${encodeURIComponent(sessionToken)}`,
    )

    source.addEventListener("state", (event) => {
      useAppStore.setState({
        state: JSON.parse(event.data) as AppState,
        connection: "connected",
      })
    })

    source.addEventListener("catalog", (event) => {
      useAppStore.setState({ catalog: JSON.parse(event.data) as Catalog })
    })

    source.addEventListener("anki.browserSelectionChanged", (event) => {
      useAppStore.setState({ selection: JSON.parse(event.data) as Selection })
    })

    source.onopen = () => useAppStore.setState({ connection: "connected" })
    source.onerror = () => {
      useAppStore.setState({ connection: "reconnecting" })
      if (source?.readyState === EventSource.CLOSED && !stopped) {
        reconnectTimer = setTimeout(connect, 2000)
      }
    }
  }

  connect()

  return () => {
    stopped = true
    source?.close()
    if (reconnectTimer !== null) clearTimeout(reconnectTimer)
  }
}
