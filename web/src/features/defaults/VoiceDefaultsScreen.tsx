import { LoaderCircle, Play } from "lucide-react"

import { hasGenerationAccess } from "@/components/shared/planPresentation"
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
import { useVoicePreview } from "./useVoicePreview"

const VOICE_GENDER_SYMBOLS: Record<string, string> = {
  Female: "♀",
  Male: "♂",
}

export const VoiceDefaultsScreen = () => {
  const state = useAppStore((store) => store.state)
  const voiceCatalog = useVoiceCatalog()

  if (state === null || voiceCatalog.catalog === null) {
    if (voiceCatalog.error === null) {
      return <DefaultsScreenLoading label="Loading Voice Defaults" />
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
  const accountCanGenerate = hasGenerationAccess(state.account)
  const usage = getDefaultUsage(state.smartFields, "tts")
  const selectedVoice = catalog.voices.find((voice) =>
    voiceMatchesSettings(voice, controls.form.values),
  )
  const voicePreview = useVoicePreview()
  const isPreviewLoading = voicePreview.loadingKey !== null
  const visibleError = controls.form.error ?? voicePreview.error

  return (
    <DefaultsScreenLayout
      accessory={<DefaultUsagePill usage={usage} />}
      icon={
        <span aria-hidden className="text-lg leading-none">
          🔈
        </span>
      }
      subtitle="The voice your TTS Smart Fields use unless a field pins its own."
      tester={
        <VoicePromptTester
          settings={controls.form.values}
          title="Try it"
          voiceName={selectedVoice?.name ?? controls.form.values.voiceId}
        />
      }
      testId="voice-defaults-screen"
      title="Default Voice"
    >
      {visibleError !== null && (
        <ErrorBanner
          className="mx-6 mt-4"
          message={visibleError}
          onDismiss={() => {
            controls.dismissError()
            voicePreview.dismissError()
          }}
        />
      )}

      {/* A flex column rather than a scrolling one: the voice list fills whatever is
          left and scrolls inside its own box. */}
      <div className="flex min-h-0 flex-1 flex-col px-6 py-5">
        <div className="flex min-h-0 w-full max-w-[560px] flex-1 flex-col">
          <p className="mb-2 text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
            Current default
          </p>
          <div className="mb-[18px] flex items-center gap-2.5 rounded-lg border border-white/[0.09] bg-white/[0.03] px-3 py-2.5">
            <button
              aria-label={`Preview ${selectedVoice?.name ?? controls.form.values.voiceId}`}
              className="flex size-6 shrink-0 cursor-pointer items-center justify-center rounded-full border border-indigo/35 bg-indigo/15 text-indigo-soft transition hover:bg-indigo/25 disabled:cursor-not-allowed disabled:opacity-35"
              disabled={
                selectedVoice === undefined ||
                !accountCanGenerate ||
                isPreviewLoading
              }
              onClick={() => {
                if (selectedVoice !== undefined)
                  void voicePreview.preview(selectedVoice)
              }}
            >
              {isPreviewLoading ? (
                <LoaderCircle aria-hidden className="size-3 animate-spin" />
              ) : (
                <Play aria-hidden className="ml-0.5 size-3 fill-current" />
              )}
            </button>
            <p className="min-w-0 flex-1 text-[12.5px] font-medium text-zinc-100">
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

          <p className="mb-2 text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
            Browse voices
          </p>
          <VoicePicker
            canPreview={accountCanGenerate}
            catalog={catalog}
            onSelect={controls.updateDefault}
            value={controls.form.values}
          />
        </div>
      </div>
    </DefaultsScreenLayout>
  )
}
