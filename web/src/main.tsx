import { createRoot } from "react-dom/client"

import App from "./App"
import "@/assets/styles/globals.css"
import { bootOptions } from "@/lib/boot"
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

void startDataSource()
createRoot(document.getElementById("root")!).render(<App />)
