import { lazy, Suspense, useState, type ComponentType } from "react"

import { AppShell } from "@/components/shared/AppShell"
import { PlaceholderScreen } from "@/components/shared/PlaceholderScreen"
import { getInitialEditorRequest } from "@/dev/initialEditor"
import { ImageDefaultsScreen } from "@/features/defaults/ImageDefaultsScreen"
import { TextDefaultsScreen } from "@/features/defaults/TextDefaultsScreen"
import { VoiceDefaultsScreen } from "@/features/defaults/VoiceDefaultsScreen"
import type { FieldEditorRequest } from "@/features/field-editor/FieldEditorScreen"
import { SmartFieldsScreen } from "@/features/smart-fields/SmartFieldsScreen"
import { SettingsScreen } from "@/features/settings/SettingsScreen"
import { SubscriptionScreen } from "@/features/subscription/SubscriptionScreen"
import { SupportScreen } from "@/features/support/SupportScreen"
import { bootOptions, type ScreenId } from "@/lib/boot"
import { useAppStore } from "@/store/appStore"
import type { AccountState } from "@/types/api"

const MockPanel = import.meta.env.DEV
  ? lazy(() => import("@/dev/MockPanel"))
  : null
const LOADING_ACCOUNT: AccountState = { subscription: "LOADING", plan: null }

interface SmartFieldsRouteProps {
  initialEditor?: FieldEditorRequest
}

interface EditorRequest {
  id: number
  editor?: FieldEditorRequest
}

const SmartFieldsRoute = ({ initialEditor }: SmartFieldsRouteProps) => {
  const state = useAppStore((store) => store.state)

  return <SmartFieldsScreen initialEditor={initialEditor} state={state} />
}

const SCREENS: Partial<Record<ScreenId, ComponentType>> = {
  "defaults-text": TextDefaultsScreen,
  "defaults-images": ImageDefaultsScreen,
  "defaults-voice": VoiceDefaultsScreen,
  settings: SettingsScreen,
  subscription: SubscriptionScreen,
  support: SupportScreen,
}

const App = () => {
  const [activeScreen, setActiveScreen] = useState<ScreenId>(bootOptions.screen)
  const [editorRequest, setEditorRequest] = useState<EditorRequest>(() => ({
    editor: getInitialEditorRequest(),
    id: 0,
  }))
  const connection = useAppStore((store) => store.connection)
  const state = useAppStore((store) => store.state)
  const ActiveScreen = SCREENS[activeScreen]
  const screenKey = `${activeScreen}-${editorRequest.id}`
  const navigateTo = (screen: ScreenId) => {
    setActiveScreen(screen)
    if (screen !== "fields") {
      setEditorRequest((request) => ({ ...request, editor: undefined }))
    }
  }

  return (
    <>
      <AppShell
        account={state?.account ?? LOADING_ACCOUNT}
        activeScreen={activeScreen}
        appVersion={state?.appVersion ?? null}
        connection={connection}
        onNavigate={navigateTo}
      >
        {activeScreen === "fields" ? (
          <SmartFieldsRoute
            initialEditor={editorRequest.editor}
            key={screenKey}
          />
        ) : ActiveScreen === undefined ? (
          <PlaceholderScreen key={screenKey} screen={activeScreen} />
        ) : (
          <ActiveScreen key={screenKey} />
        )}
      </AppShell>
      {MockPanel !== null && bootOptions.mock && (
        <Suspense fallback={null}>
          <MockPanel
            onOpenEditor={(editor) => {
              setActiveScreen("fields")
              setEditorRequest((request) => ({
                id: request.id + 1,
                editor,
              }))
            }}
          />
        </Suspense>
      )}
    </>
  )
}

export default App
