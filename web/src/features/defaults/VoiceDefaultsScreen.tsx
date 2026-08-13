import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { VoicePromptTester } from "@/features/prompt-tester/VoicePromptTester"
import { providerLabel } from "@/lib/catalog"
import { saveTTSDefaults } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AppState, VoiceCatalog } from "@/types/api"

import {
  DefaultsScreenLayout,
  DefaultsScreenLoading,
} from "./DefaultsScreenLayout"
import { DefaultUsagePill } from "./DefaultUsagePill"
import { VoicePicker } from "./VoicePicker"
import { getDefaultUsage } from "./defaultUsage"
import { voiceMatchesSettings } from "./voiceDefaults"
import { useDefaultsForm } from "./useDefaultsForm"
import { useVoiceCatalog } from "./useVoiceCatalog"

const VOICE_GENDER_SYMBOLS: Record<string, string> = {
  Female: "♀",
  Male: "♂",
}

export const VoiceDefaultsScreen = () => {
  const state = useAppStore((store) => store.state)
  const voiceCatalog = useVoiceCatalog()

  if (state === null || voiceCatalog.catalog === null) {
    if (voiceCatalog.error === null) {
      return <DefaultsScreenLoading label="Loading Default Voice Settings" />
    }

    return (
      <section className="flex min-h-0 flex-1 items-center justify-center">
        <p className="rounded-lg border border-red-300/15 bg-red-300/[0.06] px-4 py-3 text-xs text-danger">
          {voiceCatalog.error}
        </p>
      </section>
    )
  }

  return (
    <LoadedVoiceDefaultsScreen catalog={voiceCatalog.catalog} state={state} />
  )
}

interface LoadedVoiceDefaultsScreenProps {
  catalog: VoiceCatalog
  state: AppState
}

const LoadedVoiceDefaultsScreen = ({
  catalog,
  state,
}: LoadedVoiceDefaultsScreenProps) => {
  const controls = useDefaultsForm({
    fallbackError: "Could not save voice defaults",
    save: saveTTSDefaults,
    serverDefaults: state.defaults.tts,
  })
  const usage = getDefaultUsage(state.smartFields, "tts")
  const selectedVoice = catalog.voices.find((voice) =>
    voiceMatchesSettings(voice, controls.form.values),
  )

  return (
    <DefaultsScreenLayout
      accessory={<DefaultUsagePill usage={usage} />}
      contentFillsHeight
      icon={
        <span aria-hidden className="text-lg leading-none">
          🔈
        </span>
      }
      subtitle="The voice your TTS Smart Fields use unless a field pins its own."
      tester={
        <VoicePromptTester
          settings={controls.form.values}
          voiceName={selectedVoice?.name ?? controls.form.values.voiceId}
        />
      }
      testId="voice-defaults-screen"
      title="Default Voice Settings"
    >
      {controls.form.error !== null && (
        <ErrorBanner
          className="mx-6 mt-4"
          message={controls.form.error}
          onDismiss={controls.dismissError}
        />
      )}

      <div className="flex min-h-0 flex-1 flex-col px-6 py-5">
        <div className="flex min-h-0 w-full max-w-[900px] flex-1 flex-col">
          <VoicePicker
            catalog={catalog}
            layout="columns"
            onSelect={controls.updateDefault}
            value={controls.form.values}
          >
            <p className="mb-2 text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
              Current default
            </p>
            <div className="flex h-9 items-center gap-2.5 rounded-lg border border-white/[0.09] bg-white/[0.03] px-3">
              <p className="min-w-0 flex-1 truncate whitespace-nowrap text-[12.5px] font-medium text-zinc-100">
                {providerLabel(controls.form.values.provider)}
                {selectedVoice === undefined ? (
                  <> · {controls.form.values.voiceId}</>
                ) : (
                  <>
                    {" "}
                    · {selectedVoice.language} ·{" "}
                    {VOICE_GENDER_SYMBOLS[selectedVoice.gender] ??
                      selectedVoice.gender}{" "}
                    · {selectedVoice.name}
                  </>
                )}
              </p>
            </div>
          </VoicePicker>
        </div>
      </div>
    </DefaultsScreenLayout>
  )
}
