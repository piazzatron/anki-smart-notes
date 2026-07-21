import { lazy, Suspense, useState, type ComponentType } from "react"

import { AppShell } from "@/components/shared/AppShell"
import { PlaceholderScreen } from "@/components/shared/PlaceholderScreen"
import type { FieldEditorRequest } from "@/features/field-editor/FieldEditorModal"
import { ImageDefaultsScreen } from "@/features/image-defaults/ImageDefaultsScreen"
import { SmartFieldsScreen } from "@/features/smart-fields/SmartFieldsScreen"
import { TextDefaultsScreen } from "@/features/text-defaults/TextDefaultsScreen"
import { VoiceDefaultsScreen } from "@/features/voice-defaults/VoiceDefaultsScreen"
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

interface ScreenProps {
  screen: ScreenId
  initialEditor?: FieldEditorRequest
}

interface EditorRequest {
  id: number
  editor?: FieldEditorRequest
}

const SmartFieldsRoute = ({ initialEditor }: ScreenProps) => {
  const state = useAppStore((store) => store.state)

  return <SmartFieldsScreen initialEditor={initialEditor} state={state} />
}

const SCREENS: Partial<Record<ScreenId, ComponentType<ScreenProps>>> = {
  fields: SmartFieldsRoute,
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
    id: 0,
    editor:
      !bootOptions.mock ||
      bootOptions.screen !== "fields" ||
      bootOptions.editor === null
        ? undefined
        : {
            mode: bootOptions.editor,
            step: bootOptions.editorStep ?? undefined,
          },
  }))
  const connection = useAppStore((store) => store.connection)
  const state = useAppStore((store) => store.state)
  const ActiveScreen = SCREENS[activeScreen] ?? PlaceholderScreen
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
        <ActiveScreen
          initialEditor={editorRequest.editor}
          key={`${activeScreen}-${editorRequest.id}`}
          screen={activeScreen}
        />
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
