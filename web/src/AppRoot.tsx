import { DirectionProvider } from "@radix-ui/react-direction"
import { useTranslation } from "react-i18next"

import App from "./App"
import { getLocaleDirection } from "@/lib/i18n/locale"

export const AppRoot = () => {
  const { i18n } = useTranslation()
  return (
    <DirectionProvider dir={getLocaleDirection(i18n.language)}>
      <App />
    </DirectionProvider>
  )
}
