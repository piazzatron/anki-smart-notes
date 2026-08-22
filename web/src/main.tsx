import { createRoot } from "react-dom/client"
import { DirectionProvider } from "@radix-ui/react-direction"
import { useTranslation } from "react-i18next"

import App from "./App"
import "@/assets/styles/globals.css"
import { bootOptions } from "@/lib/boot"
import { initializeI18n } from "@/lib/i18n"
import { getLocaleDirection } from "@/lib/i18n/locale"
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

const AppRoot = () => {
  const { i18n } = useTranslation()
  return (
    <DirectionProvider dir={getLocaleDirection(i18n.language)}>
      <App />
    </DirectionProvider>
  )
}

const startApp = async () => {
  await initializeI18n()
  await startDataSource()
  createRoot(document.getElementById("root")!).render(<AppRoot />)
}

void startApp()
