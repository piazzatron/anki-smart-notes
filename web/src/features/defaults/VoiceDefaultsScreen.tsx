import { type ReactNode, useState } from "react"
import { useTranslation } from "react-i18next"

import { useIsFreePlan } from "@/components/shared/UpgradeSheet"

import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { Card } from "@/components/ui/Card"
import { SectionHeading } from "@/components/ui/SectionHeading"
import { PromptTesterStrip } from "@/features/prompt-tester/PromptTesterStrip"
import { usePromptTester } from "@/features/prompt-tester/usePromptTester"
import { providerLabel } from "@/lib/catalog"
import { PageLayout } from "@/components/shared/PageLayout"
import { LoudspeakerEmoji } from "@/components/shared/Emoji"
import { FemaleIcon, MaleIcon } from "@/components/shared/Icons"
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

const GENDER_ICON_CLASS = "inline-block align-[-2px]"
const VOICE_GENDER_ICONS: Record<string, ReactNode> = {
  Female: <FemaleIcon className={GENDER_ICON_CLASS} size={13} />,
  Male: <MaleIcon className={GENDER_ICON_CLASS} size={13} />,
}

interface VoiceDefaultsScreenProps {
  onDirtyChange?: (isDirty: boolean) => void
}

export const VoiceDefaultsScreen = ({
  onDirtyChange,
}: VoiceDefaultsScreenProps) => {
  const { t } = useTranslation()
  const state = useAppStore((store) => store.state)
  const voiceCatalog = useVoiceCatalog()

  if (state === null || voiceCatalog.catalog === null) {
    if (voiceCatalog.error === null) {
      return (
        <DefaultsScreenLoading
          icon={<LoudspeakerEmoji size={28} />}
          label={t("defaults.voice.loadingLabel")}
          title={t("defaults.voice.loadingTitle")}
        />
      )
    }

    return (
      <PageLayout
        icon={<LoudspeakerEmoji size={28} />}
        testId="voice-defaults-screen"
        title={t("defaults.voice.title")}
      >
        <p className="rounded-lg bg-red-300/[0.06] px-4 py-3 text-[13px] text-danger">
          {voiceCatalog.error}
        </p>
      </PageLayout>
    )
  }

  return (
    <LoadedVoiceDefaultsScreen
      catalog={voiceCatalog.catalog}
      onDirtyChange={onDirtyChange}
      state={state}
    />
  )
}

interface LoadedVoiceDefaultsScreenProps {
  catalog: VoiceCatalog
  onDirtyChange?: (isDirty: boolean) => void
  state: AppState
}

const LoadedVoiceDefaultsScreen = ({
  catalog,
  onDirtyChange,
  state,
}: LoadedVoiceDefaultsScreenProps) => {
  const { t } = useTranslation()
  const isFree = useIsFreePlan()
  const controls = useDefaultsForm({
    fallbackError: t("defaults.voice.saveError"),
    onDirtyChange,
    save: saveTTSDefaults,
    serverDefaults: state.defaults.tts,
  })
  const usage = getDefaultUsage(state.smartFields, "tts")
  const selectedVoice = catalog.voices.find((voice) =>
    voiceMatchesSettings(voice, controls.form.values),
  )
  const genderIcon = selectedVoice && VOICE_GENDER_ICONS[selectedVoice.gender]
  const genderLabel =
    selectedVoice &&
    t(`defaults.voice.filters.${selectedVoice.gender.toLowerCase()}`)

  // The tester reads whichever card field the user picks below.
  const [prompt, setPrompt] = useState("")
  const tester = usePromptTester({
    fieldType: "tts",
    onPromptChange: setPrompt,
    prompt,
    settings: controls.form.values,
    voiceName: selectedVoice?.name ?? controls.form.values.voiceId,
  })

  return (
    <DefaultsScreenLayout
      upgradeFeature={isFree ? "voice" : undefined}
      accessory={<DefaultUsagePill usage={usage} />}
      contentFillsHeight
      icon={<LoudspeakerEmoji size={28} />}
      isDirty={controls.form.isDirty}
      isSaving={controls.form.isSaving}
      onSave={() => void controls.saveChanges()}
      tester={<PromptTesterStrip field={tester} />}
      testId="voice-defaults-screen"
      title={t("defaults.voice.title")}
    >
      {controls.form.error !== null && (
        <ErrorBanner
          className="mb-4"
          message={controls.form.error}
          onDismiss={controls.dismissError}
        />
      )}

      <div className="flex min-h-0 flex-1 flex-col">
        <SectionHeading
          tip={{
            content: t("defaults.voice.defaultVoiceTip"),
            label: t("defaults.voice.defaultVoiceTipLabel"),
          }}
        >
          {t("defaults.voice.defaultVoice")}
        </SectionHeading>
        <div className="flex min-h-0 w-full flex-1 flex-col">
          <VoicePicker
            catalog={catalog}
            layout="columns"
            onSelect={controls.updateDefault}
            value={controls.form.values}
          >
            <p className="mb-2 px-hang text-xs font-medium text-ink-muted">
              {t("defaults.voice.currentDefault")}
            </p>
            <Card className="px-hang py-2.5">
              <p className="truncate text-sm font-medium text-ink">
                {selectedVoice?.name ?? controls.form.values.voiceId}
              </p>
              <p className="mt-0.5 truncate text-xs text-ink-muted">
                {providerLabel(controls.form.values.provider)}
                {selectedVoice !== undefined && (
                  <>
                    {" "}
                    · {selectedVoice.language} ·{" "}
                    {genderIcon === undefined ? (
                      genderLabel
                    ) : (
                      <>
                        {genderIcon}
                        <span className="sr-only">{genderLabel}</span>
                      </>
                    )}
                  </>
                )}
              </p>
            </Card>
          </VoicePicker>
        </div>
      </div>
    </DefaultsScreenLayout>
  )
}
