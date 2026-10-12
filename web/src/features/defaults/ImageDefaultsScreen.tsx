import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"

import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { InfoTip } from "@/components/ui/InfoTip"
import { ImageModelSelect } from "@/features/image-generation/ImageModelSelect"
import { PromptTesterStrip } from "@/features/prompt-tester/PromptTesterStrip"
import { usePromptTester } from "@/features/prompt-tester/usePromptTester"
import { saveImageDefaults, saveSettings } from "@/services/commands"
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

interface ImageDefaultsScreenProps {
  onDirtyChange?: (isDirty: boolean) => void
}

export const ImageDefaultsScreen = ({
  onDirtyChange,
}: ImageDefaultsScreenProps) => {
  const { t } = useTranslation()
  const state = useAppStore((store) => store.state)
  const catalog = useAppStore((store) => store.catalog)
  if (state === null || catalog === null) {
    return (
      <DefaultsScreenLoading
        icon={
          <span aria-hidden className="text-lg leading-none">
            🎨
          </span>
        }
        label={t("defaults.image.loadingLabel")}
        title={t("defaults.image.loadingTitle")}
      />
    )
  }

  return (
    <LoadedImageDefaultsScreen
      catalog={catalog}
      onDirtyChange={onDirtyChange}
      state={state}
    />
  )
}

interface LoadedImageDefaultsScreenProps {
  catalog: Catalog
  onDirtyChange?: (isDirty: boolean) => void
  state: AppState
}

const LoadedImageDefaultsScreen = ({
  catalog,
  onDirtyChange,
  state,
}: LoadedImageDefaultsScreenProps) => {
  const { t } = useTranslation()
  const controls = useDefaultsForm({
    fallbackError: t("defaults.image.saveError"),
    onDirtyChange,
    save: saveImageDefaults,
    serverDefaults: state.defaults.image,
  })
  const usage = getDefaultUsage(state.smartFields, "image")
  // The tester owns its own scratch prompt here: nothing else on the page writes one.
  const [prompt, setPrompt] = useScratchPrompt(
    "image",
    t("defaults.image.samplePrompt"),
  )
  // The model tips open by themselves the first time someone lands here.
  const [isFirstVisit] = useState(() => !state.settings.didSeeImageModelTips)
  useEffect(() => {
    // Read settings from the store, not props: the save republishes state, and a
    // settings dependency would save again on every republish.
    const settings = useAppStore.getState().state?.settings
    if (!isFirstVisit || settings === undefined) return
    void saveSettings({ ...settings, didSeeImageModelTips: true })
  }, [isFirstVisit])

  const tester = usePromptTester({
    fieldType: "image",
    onPromptChange: setPrompt,
    prompt,
    settings: controls.form.values,
  })

  return (
    <DefaultsScreenLayout
      accessory={<DefaultUsagePill usage={usage} />}
      icon={
        <span aria-hidden className="text-lg leading-none">
          🎨
        </span>
      }
      isDirty={controls.form.isDirty}
      isSaving={controls.form.isSaving}
      onSave={() => void controls.saveChanges()}
      subtitle={t("defaults.image.subtitle")}
      tester={<PromptTesterStrip field={tester} />}
      testId="image-defaults-screen"
      title={t("defaults.image.title")}
    >
      {controls.form.error !== null && (
        <ErrorBanner
          className="mb-4"
          message={controls.form.error}
          onDismiss={controls.dismissError}
        />
      )}

      <div>
        <div className="w-full max-w-[480px]">
          <div className="mb-2 flex items-center gap-1.5">
            <label
              className="text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase"
              htmlFor="default-image-model"
            >
              {t("defaults.image.defaultModel")}
            </label>
            <InfoTip
              defaultOpen={isFirstVisit}
              label={t("defaults.image.modelTipLabel")}
            >
              <ul className="space-y-1">
                {MODEL_TIPS.map((tip) => (
                  <li key={tip.name}>
                    <strong className="font-semibold text-zinc-50">
                      {t(tip.name)}
                    </strong>{" "}
                    — {t(tip.description)}
                  </li>
                ))}
              </ul>
            </InfoTip>
          </div>
          <ImageModelSelect
            catalog={catalog.image}
            id="default-image-model"
            onValueChange={(settings) => void controls.updateDefault(settings)}
            openExtrasTip={isFirstVisit}
            value={controls.form.values.model}
          />
        </div>
      </div>
    </DefaultsScreenLayout>
  )
}

// What each model is good at; the picker already shows what each costs.
const MODEL_TIPS = [
  {
    name: "defaults.image.models.gptImage25",
    description: "defaults.image.gptImage25",
  },
  {
    name: "defaults.image.models.nanoBanana21",
    description: "defaults.image.nanoBanana21",
  },
  {
    name: "defaults.image.models.zImageTurbo",
    description: "defaults.image.zImageTurbo",
  },
] as const
