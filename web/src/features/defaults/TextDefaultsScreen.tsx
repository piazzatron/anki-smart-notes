import { useTranslation } from "react-i18next"

import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { SectionHeading } from "@/components/ui/SectionHeading"
import { PromptTesterStrip } from "@/features/prompt-tester/PromptTesterStrip"
import { usePromptTester } from "@/features/prompt-tester/usePromptTester"
import { TextModelPicker } from "@/features/text-generation/TextModelPicker"
import { saveChatDefaults } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AppState, Catalog } from "@/types/api"

import {
  DefaultsScreenLayout,
  DefaultsScreenLoading,
} from "./DefaultsScreenLayout"
import { getDefaultUsage } from "./defaultUsage"
import { useScratchPrompt } from "./scratchPrompts"
import { DefaultUsagePill } from "./DefaultUsagePill"
import { useDefaultsForm } from "./useDefaultsForm"
import { SpeechBalloonEmoji } from "@/components/shared/Emoji"

interface TextDefaultsScreenProps {
  onDirtyChange?: (isDirty: boolean) => void
}

export const TextDefaultsScreen = ({
  onDirtyChange,
}: TextDefaultsScreenProps) => {
  const { t } = useTranslation()
  const state = useAppStore((store) => store.state)
  const catalog = useAppStore((store) => store.catalog)

  if (state === null || catalog === null) {
    return (
      <DefaultsScreenLoading
        icon={<SpeechBalloonEmoji size={28} />}
        label={t("defaults.text.loadingLabel")}
        title={t("defaults.text.loadingTitle")}
      />
    )
  }

  return (
    <LoadedTextDefaultsScreen
      catalog={catalog}
      onDirtyChange={onDirtyChange}
      state={state}
    />
  )
}

interface LoadedTextDefaultsScreenProps {
  catalog: Catalog
  onDirtyChange?: (isDirty: boolean) => void
  state: AppState
}

export const LoadedTextDefaultsScreen = ({
  catalog,
  onDirtyChange,
  state,
}: LoadedTextDefaultsScreenProps) => {
  const { t } = useTranslation()
  const controls = useDefaultsForm({
    fallbackError: t("defaults.text.saveError"),
    onDirtyChange,
    save: saveChatDefaults,
    serverDefaults: state.defaults.chat,
  })
  const usage = getDefaultUsage(state.smartFields, "chat")
  // The tester owns its own scratch prompt here: nothing else on the page writes one.
  const [prompt, setPrompt] = useScratchPrompt(
    "text",
    t("defaults.text.samplePrompt"),
  )
  const tester = usePromptTester({
    fieldType: "chat",
    onPromptChange: setPrompt,
    prompt,
    settings: controls.form.values,
  })

  return (
    <DefaultsScreenLayout
      accessory={<DefaultUsagePill usage={usage} />}
      icon={<SpeechBalloonEmoji size={28} />}
      isDirty={controls.form.isDirty}
      isSaving={controls.form.isSaving}
      onSave={() => void controls.saveChanges()}
      tester={<PromptTesterStrip field={tester} />}
      testId="text-defaults-screen"
      title={t("defaults.text.title")}
    >
      {controls.form.error !== null && (
        <ErrorBanner
          className="mb-4"
          message={controls.form.error}
          onDismiss={controls.dismissError}
        />
      )}

      <div className="max-w-[520px]">
        <SectionHeading
          tip={{
            content: t("defaults.text.defaultModelTip"),
            label: t("defaults.text.defaultModelTipLabel"),
          }}
        >
          {t("defaults.text.defaultModel")}
        </SectionHeading>
        <TextModelPicker
          catalog={catalog.chat}
          hanging
          onChange={controls.updateDefault}
          value={controls.form.values}
        />
      </div>
    </DefaultsScreenLayout>
  )
}
