import { createRoot } from "react-dom/client"

import App from "./App"
import "@/assets/styles/globals.css"
import { readBootOptions } from "@/lib/boot"
import { connectToAnki } from "@/services/sse"

const startDataSource = async () => {
  const bootOptions = readBootOptions()
  if (import.meta.env.DEV && bootOptions.mock) {
    const { setMockFixture } = await import("@/dev/mockData")
    setMockFixture(bootOptions.fixture)
    return
  }

  connectToAnki()
}

void startDataSource()
createRoot(document.getElementById("root")!).render(<App />)
