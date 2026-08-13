import { lazy, Suspense, useState, type ComponentType } from "react"

import { AppShell } from "@/components/shared/AppShell"
import { PlaceholderScreen } from "@/components/shared/PlaceholderScreen"
import { Button } from "@/components/ui/Button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/Dialog"
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
  settings: SettingsScreen,
  subscription: SubscriptionScreen,
  support: SupportScreen,
}

interface DefaultsScreenProps {
  onDirtyChange: (isDirty: boolean) => void
}

const DEFAULT_SCREENS: Partial<
  Record<ScreenId, ComponentType<DefaultsScreenProps>>
> = {
  "defaults-text": TextDefaultsScreen,
  "defaults-images": ImageDefaultsScreen,
  "defaults-voice": VoiceDefaultsScreen,
}

const App = () => {
  const [activeScreen, setActiveScreen] = useState<ScreenId>(bootOptions.screen)
  const [hasUnsavedDefaults, setHasUnsavedDefaults] = useState(false)
  const [pendingScreen, setPendingScreen] = useState<ScreenId | null>(null)
  const [editorRequest, setEditorRequest] = useState<EditorRequest>(() => ({
    editor: getInitialEditorRequest(),
    id: 0,
  }))
  const connection = useAppStore((store) => store.connection)
  const state = useAppStore((store) => store.state)
  const ActiveScreen = SCREENS[activeScreen]
  const ActiveDefaultsScreen = DEFAULT_SCREENS[activeScreen]
  const screenKey = `${activeScreen}-${editorRequest.id}`

  const completeNavigation = (screen: ScreenId) => {
    setActiveScreen(screen)
    if (screen !== "fields") {
      setEditorRequest((request) => ({ ...request, editor: undefined }))
    }
  }

  const navigateTo = (screen: ScreenId) => {
    if (screen === activeScreen) return
    if (hasUnsavedDefaults) {
      setPendingScreen(screen)
      return
    }

    completeNavigation(screen)
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
        ) : ActiveDefaultsScreen !== undefined ? (
          <ActiveDefaultsScreen
            key={screenKey}
            onDirtyChange={setHasUnsavedDefaults}
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
      <Dialog
        onOpenChange={(open) => {
          if (!open) setPendingScreen(null)
        }}
        open={pendingScreen !== null}
      >
        <DialogContent className="w-[min(420px,92vw)]">
          <div className="px-5 pt-5 pr-12 pb-4">
            <DialogTitle className="text-sm font-bold text-zinc-100">
              Discard unsaved changes?
            </DialogTitle>
            <DialogDescription className="mt-1.5 text-xs leading-5 text-ink-muted">
              Your changes to these default settings have not been saved.
            </DialogDescription>
          </div>
          <div className="flex justify-end gap-2 border-t border-white/[0.08] px-5 py-4">
            <Button onClick={() => setPendingScreen(null)}>Cancel</Button>
            <Button
              onClick={() => {
                if (pendingScreen === null) return

                setHasUnsavedDefaults(false)
                completeNavigation(pendingScreen)
                setPendingScreen(null)
              }}
              variant="danger"
            >
              Discard changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}

export default App
