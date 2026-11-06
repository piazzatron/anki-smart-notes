import { lazy, Suspense, useEffect, useState, type ComponentType } from "react"
import { useTranslation } from "react-i18next"

import { AppShell } from "@/components/shared/AppShell"
import { shouldShowTrialEndedTakeover } from "@/components/shared/planPresentation"
import { PlaceholderScreen } from "@/components/shared/PlaceholderScreen"
import { UpgradeSheet } from "@/components/shared/UpgradeSheet"
import { Button } from "@/components/ui/Button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/Dialog"
import { getInitialEditorRequest } from "@/dev/initialEditor"
import { ImageDefaultsScreen } from "@/features/defaults/ImageDefaultsScreen"
import { TextDefaultsScreen } from "@/features/defaults/TextDefaultsScreen"
import { useVoiceCatalog } from "@/features/defaults/useVoiceCatalog"
import { allowedVoicesOf } from "@/features/defaults/voiceDefaults"
import { VoiceDefaultsScreen } from "@/features/defaults/VoiceDefaultsScreen"
import type { FieldEditorRequest } from "@/features/field-editor/FieldEditorScreen"
import { SmartFieldsScreen } from "@/features/smart-fields/SmartFieldsScreen"
import { SettingsScreen } from "@/features/settings/SettingsScreen"
import { SubscriptionScreen } from "@/features/subscription/SubscriptionScreen"
import { SupportScreen } from "@/features/support/SupportScreen"
import { FreePlanStartedScreen } from "@/features/trial-ended/FreePlanStartedScreen"
import { getFreePlanImpact } from "@/features/trial-ended/freePlanImpact"
import { TrialEndedScreen } from "@/features/trial-ended/TrialEndedScreen"
import { WelcomeScreen } from "@/features/welcome/WelcomeScreen"
import { bootOptions, type ScreenId } from "@/lib/boot"
import { syncAmplitudeIdentity } from "@/services/amplitude"
import { saveSettings } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AccountState } from "@/types/api"

const MockPanel = import.meta.env.DEV
  ? lazy(() => import("@/dev/MockPanel"))
  : null
const LOADING_ACCOUNT: AccountState = {
  status: "LOADING",
  plan: null,
  email: null,
  authToken: null,
}

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
  const { t } = useTranslation()
  const [activeScreen, setActiveScreen] = useState<ScreenId>(bootOptions.screen)
  const [hasUnsavedDefaults, setHasUnsavedDefaults] = useState(false)
  const [pendingScreen, setPendingScreen] = useState<ScreenId | null>(null)
  const [editorRequest, setEditorRequest] = useState<EditorRequest>(() => ({
    editor: getInitialEditorRequest(),
    id: 0,
  }))
  const connection = useAppStore((store) => store.connection)
  const state = useAppStore((store) => store.state)
  const voiceCatalog = useVoiceCatalog().catalog
  const ActiveScreen = SCREENS[activeScreen]
  const ActiveDefaultsScreen = DEFAULT_SCREENS[activeScreen]
  const screenKey = `${activeScreen}-${editorRequest.id}`
  const showWelcome =
    state?.account.status === "UNAUTHENTICATED" &&
    state.smartFields.length === 0
  const showTrialEnded =
    state !== null &&
    shouldShowTrialEndedTakeover(state.account, state.settings)
  const freePlanStarted =
    state?.account.status === "AUTHENTICATED" &&
    state.account.plan.planType === "free" &&
    !state.settings.didSeeFreePlanWelcome
      ? state.account.plan
      : null

  const installId = state?.installId
  const email = state?.account.email ?? null
  useEffect(() => {
    if (installId) syncAmplitudeIdentity({ installId, email })
  }, [installId, email])

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
      {showWelcome ? (
        <WelcomeScreen
          appVersion={state?.appVersion ?? null}
          connection={connection}
        />
      ) : showTrialEnded ? (
        <TrialEndedScreen />
      ) : freePlanStarted !== null && state !== null ? (
        <FreePlanStartedScreen
          dailyNotesLimit={freePlanStarted.dailyNotesLimit!}
          impact={getFreePlanImpact({
            smartFields: state.smartFields,
            defaults: state.defaults,
            allowedVoices: allowedVoicesOf(state),
            voices: voiceCatalog?.voices ?? null,
          })}
          onContinue={() =>
            void saveSettings({
              ...state.settings,
              didSeeFreePlanWelcome: true,
            })
          }
          reason={freePlanStarted.freePlanReason!}
        />
      ) : (
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
      )}
      <UpgradeSheet />
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
          <div className="px-5 pe-12 pt-5 pb-4">
            <DialogTitle className="text-sm font-semibold text-ink">
              {t("common.discardUnsavedChanges.title")}
            </DialogTitle>
            <DialogDescription className="mt-1.5 text-[13px] leading-5 text-ink-muted">
              {t("common.discardUnsavedChanges.description")}
            </DialogDescription>
          </div>
          <DialogFooter>
            <Button onClick={() => setPendingScreen(null)}>
              {t("common.cancel")}
            </Button>
            <Button
              onClick={() => {
                if (pendingScreen === null) return

                setHasUnsavedDefaults(false)
                completeNavigation(pendingScreen)
                setPendingScreen(null)
              }}
              variant="danger"
            >
              {t("common.discardChanges")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

export default App
