import { createRoot } from "react-dom/client"

// Entry code only: a component defined here would make this module a Fast Refresh
// boundary, and a hot update reaching it would re-run startApp and mount a second app
// over the first instead of reloading the page.
import { AppRoot } from "./AppRoot"
import "@/assets/styles/globals.css"
import { bootOptions } from "@/lib/boot"
import { initializeI18n } from "@/lib/i18n"
import { setCommandSender } from "@/services/commands"
import { connectToAnki } from "@/services/sse"

const startDataSource = async () => {
  if (import.meta.env.DEV && bootOptions.mock) {
    const { sendMockCommand, setMockFixture } = await import("@/dev/mockData")
    setCommandSender(sendMockCommand)
    setMockFixture(bootOptions.fixture)
    return
  }

  connectToAnki()
}

const startApp = async () => {
  await initializeI18n()
  await startDataSource()
  createRoot(document.getElementById("root")!).render(<AppRoot />)
}

void startApp()
