import { lazy, Suspense, useState } from "react"

import { AppShell } from "@/components/shared/AppShell"
import type { AccountState } from "@/components/shared/planPresentation"
import { PlaceholderScreen } from "@/components/shared/PlaceholderScreen"
import { SmartFieldsScreen } from "@/features/smart-fields/SmartFieldsScreen"
import { readBootOptions, type ScreenId } from "@/lib/boot"
import { useAppStore } from "@/store/appStore"

const MockPanel = import.meta.env.DEV
  ? lazy(() => import("@/dev/MockPanel"))
  : null
const LOADING_ACCOUNT: AccountState = { subscription: "LOADING", plan: null }

const App = () => {
  const bootOptions = readBootOptions()
  const [activeScreen, setActiveScreen] = useState<ScreenId>(bootOptions.screen)
  const connection = useAppStore((store) => store.connection)
  const state = useAppStore((store) => store.state)

  return (
    <>
      <AppShell
        account={state?.account ?? LOADING_ACCOUNT}
        activeScreen={activeScreen}
        connection={connection}
        onNavigate={setActiveScreen}
      >
        {activeScreen === "fields" ? (
          <SmartFieldsScreen state={state} />
        ) : (
          <PlaceholderScreen screen={activeScreen} />
        )}
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
