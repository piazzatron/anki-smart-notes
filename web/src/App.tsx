import { lazy, Suspense, useState } from "react"

import { AppShell } from "@/components/shared/AppShell"
import { PlaceholderScreen } from "@/components/shared/PlaceholderScreen"
import { SmartFieldsScreen } from "@/features/smart-fields/SmartFieldsScreen"
import { TextDefaultsScreen } from "@/features/text-defaults/TextDefaultsScreen"
import { readBootOptions, type ScreenId } from "@/lib/boot"
import { useAppStore } from "@/store/appStore"
import type { AccountState } from "@/types/api"

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
        {activeScreen === "fields" && <SmartFieldsScreen state={state} />}
        {activeScreen === "defaults-text" && <TextDefaultsScreen />}
        {activeScreen !== "fields" && activeScreen !== "defaults-text" && (
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
