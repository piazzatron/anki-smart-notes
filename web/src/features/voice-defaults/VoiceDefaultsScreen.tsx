import { AlertCircle, LoaderCircle, Play, X } from "lucide-react"
import { useEffect, useRef, useState } from "react"

import { hasGenerationAccess } from "@/components/shared/planPresentation"
import { Button } from "@/components/ui/Button"
import { getDefaultUsage } from "@/features/defaults/defaultUsage"
import { useDefaultsForm } from "@/features/defaults/useDefaultsForm"
import { VoicePromptTester } from "@/features/prompt-tester/VoicePromptTester"
import { providerLabel } from "@/lib/catalog"
import { previewTTSVoice, saveTTSDefaults } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AppState, VoiceCatalog, VoiceCatalogItem } from "@/types/api"

import { VoicePicker } from "./VoicePicker"
import { previewTextForLanguage, voiceMatchesSettings } from "./voiceDefaults"
import { useVoiceCatalog } from "./useVoiceCatalog"

const VOICE_GENDER_SYMBOLS: Record<string, string> = {
  Female: "♀",
  Male: "♂",
}

export const VoiceDefaultsScreen = () => {
  const state = useAppStore((store) => store.state)
  const voiceCatalog = useVoiceCatalog()

  if (state === null || voiceCatalog.catalog === null) {
    return (
      <section className="flex min-h-0 flex-1 items-center justify-center">
        {voiceCatalog.error === null ? (
          <LoaderCircle
            aria-label="Loading voices"
            className="size-5 animate-spin text-indigo-soft"
          />
        ) : (
          <p className="rounded-lg border border-red-300/15 bg-red-300/[0.06] px-4 py-3 text-xs text-danger">
            {voiceCatalog.error}
          </p>
        )}
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
  const [previewState, setPreviewState] = useState<{
    error: string | null
    isLoading: boolean
  }>({ error: null, isLoading: false })
  const previewAudio = useRef<HTMLAudioElement | null>(null)

  useEffect(
    () => () => {
      previewAudio.current?.pause()
    },
    [],
  )
  const previewVoice = async (voice: VoiceCatalogItem) => {
    previewAudio.current?.pause()
    setPreviewState({ error: null, isLoading: true })
    try {
      const result = await previewTTSVoice({
        text: previewTextForLanguage(voice.language),
        settings: {
          provider: voice.provider,
          model: voice.model,
          voiceId: voice.voiceId,
        },
      })
      previewAudio.current = new Audio(result.dataUrl)
      await previewAudio.current.play()
    } catch (error) {
      setPreviewState({
        error:
          error instanceof Error
            ? error.message
            : "Could not preview this voice",
        isLoading: false,
      })
      return
    }
    setPreviewState({ error: null, isLoading: false })
  }

  return (
    <section
      className="flex min-h-0 flex-1 flex-col"
      data-testid="voice-defaults-screen"
    >
      <header className="flex shrink-0 items-center justify-between gap-6 border-b border-white/[0.065] px-6 py-5">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span aria-hidden className="text-lg leading-none">
              🔈
            </span>
            <h1 className="truncate text-[21px] leading-tight font-bold tracking-[-0.025em] text-zinc-100">
              Default Voice
            </h1>
          </div>
          <p className="mt-1.5 truncate text-xs text-ink-muted">
            The voice your TTS Smart Fields use unless a field pins its own.
          </p>
        </div>
        <span className="shrink-0 rounded-full border border-white/[0.08] bg-white/[0.025] px-3 py-1.5 text-[10.5px] text-zinc-400">
          Applies to {usage.following} field{usage.following === 1 ? "" : "s"}
          {usage.pinned > 0 && (
            <span className="text-amber"> · {usage.pinned} pinned</span>
          )}
        </span>
      </header>

      {(controls.form.error !== null || previewState.error !== null) && (
        <div className="mx-6 mt-4 flex items-start gap-2 rounded-lg border border-red-300/15 bg-red-300/[0.06] px-3 py-2.5 text-xs text-danger">
          <AlertCircle aria-hidden className="mt-0.5 size-3.5 shrink-0" />
          <p className="min-w-0 flex-1">
            {controls.form.error ?? previewState.error}
          </p>
          <button
            aria-label="Dismiss error"
            className="cursor-pointer"
            onClick={() => {
              controls.dismissError()
              setPreviewState((current) => ({ ...current, error: null }))
            }}
          >
            <X aria-hidden className="size-3.5" />
          </button>
        </div>
      )}

      <div className="grid min-h-0 flex-1 grid-cols-[minmax(390px,1.1fr)_minmax(330px,0.9fr)] px-6 py-5 max-[900px]:grid-cols-1 max-[900px]:overflow-y-auto">
        <div className="flex min-h-0 flex-col border-r border-white/[0.07] pr-6 max-[900px]:border-r-0 max-[900px]:pr-0">
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
                previewState.isLoading
              }
              onClick={() => {
                if (selectedVoice !== undefined)
                  void previewVoice(selectedVoice)
              }}
            >
              {previewState.isLoading ? (
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
            onSelect={controls.patchDraft}
            value={controls.form.values}
          />

          {controls.hasPendingChanges && (
            <div className="mt-4 flex shrink-0 items-center gap-2.5 rounded-lg border border-amber/20 bg-amber/[0.065] p-3">
              <span aria-hidden className="shrink-0 text-sm">
                ⚡
              </span>
              <p className="min-w-0 flex-1 text-[10.5px] leading-4 text-zinc-300">
                This updates{" "}
                <strong>
                  {usage.following} field{usage.following === 1 ? "" : "s"}
                </strong>{" "}
                following the voice default
                {usage.pinned > 0 && (
                  <>
                    {" "}
                    ·{" "}
                    <strong>
                      {usage.pinned} pinned field
                      {usage.pinned === 1 ? "" : "s"}
                    </strong>{" "}
                    won&apos;t change
                  </>
                )}
                .
              </p>
              <Button
                className="px-2.5 py-1.5"
                disabled={controls.form.isSaving}
                onClick={controls.cancel}
              >
                Cancel
              </Button>
              <Button
                className="px-2.5 py-1.5"
                disabled={controls.form.isSaving}
                onClick={() => void controls.save()}
                variant="primary"
              >
                {controls.form.isSaving ? "Updating…" : "Update default"}
              </Button>
            </div>
          )}
        </div>

        <div className="min-h-0 overflow-y-auto pl-6 max-[900px]:mt-6 max-[900px]:border-t max-[900px]:border-white/[0.07] max-[900px]:pt-6 max-[900px]:pl-0">
          <VoicePromptTester
            settings={controls.form.values}
            voiceName={selectedVoice?.name ?? controls.form.values.voiceId}
          />
        </div>
      </div>
    </section>
  )
}
