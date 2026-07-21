import { lazy, Suspense, useState, type ComponentType } from "react"

import { AppShell } from "@/components/shared/AppShell"
import { PlaceholderScreen } from "@/components/shared/PlaceholderScreen"
import { SmartFieldsScreen } from "@/features/smart-fields/SmartFieldsScreen"
import { TextDefaultsScreen } from "@/features/text-defaults/TextDefaultsScreen"
import { bootOptions, type ScreenId } from "@/lib/boot"
import { useAppStore } from "@/store/appStore"
import type { AccountState } from "@/types/api"

const MockPanel = import.meta.env.DEV
  ? lazy(() => import("@/dev/MockPanel"))
  : null
const LOADING_ACCOUNT: AccountState = { subscription: "LOADING", plan: null }

interface ScreenProps {
  screen: ScreenId
}

const SmartFieldsRoute = () => {
  const state = useAppStore((store) => store.state)

  return <SmartFieldsScreen state={state} />
}

const SCREENS: Partial<Record<ScreenId, ComponentType<ScreenProps>>> = {
  fields: SmartFieldsRoute,
  "defaults-text": TextDefaultsScreen,
}

const App = () => {
  const [activeScreen, setActiveScreen] = useState<ScreenId>(bootOptions.screen)
  const connection = useAppStore((store) => store.connection)
  const state = useAppStore((store) => store.state)
  const ActiveScreen = SCREENS[activeScreen] ?? PlaceholderScreen

  return (
    <>
      <AppShell
        account={state?.account ?? LOADING_ACCOUNT}
        activeScreen={activeScreen}
        connection={connection}
        onNavigate={setActiveScreen}
      >
        <ActiveScreen screen={activeScreen} />
      </AppShell>
      {MockPanel !== null && bootOptions.mock && (
        <Suspense fallback={null}>
          <MockPanel />
        </Suspense>
      )}
    </>
  )
}

export default App
