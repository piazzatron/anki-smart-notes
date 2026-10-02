import { useState } from "react"
import { useTranslation } from "react-i18next"

import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { ImageModelSelect } from "@/features/image-generation/ImageModelSelect"
import { PromptTesterStrip } from "@/features/prompt-tester/PromptTesterStrip"
import { usePromptTester } from "@/features/prompt-tester/usePromptTester"
import { saveImageDefaults } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AppState, Catalog } from "@/types/api"

import {
  DefaultsScreenLayout,
  DefaultsScreenLoading,
} from "./DefaultsScreenLayout"
import { getDefaultUsage } from "./defaultUsage"
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
  const [prompt, setPrompt] = useState(() => t("defaults.image.samplePrompt"))
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
          <label
            className="mb-2 block text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase"
            htmlFor="default-image-model"
          >
            {t("defaults.image.defaultModel")}
          </label>
          <ImageModelSelect
            catalog={catalog.image}
            id="default-image-model"
            onValueChange={(settings) => void controls.updateDefault(settings)}
            value={controls.form.values.model}
          />

          <div className="mt-3 rounded-lg border border-indigo/15 bg-indigo/[0.055] p-3.5">
            <p className="text-xs font-semibold text-zinc-200">
              {t("defaults.image.pickingModel")}
            </p>
            <ul className="mt-2 list-disc space-y-1 ps-5 text-[11px] leading-4 text-ink-muted">
              <li>
                <strong className="text-zinc-300">
                  {t("defaults.image.models.gptImage25")}
                </strong>{" "}
                — {t("defaults.image.gptImage25")}
              </li>
              <li>
                <strong className="text-zinc-300">
                  {t("defaults.image.models.zImageTurbo")}
                </strong>{" "}
                — {t("defaults.image.zImageTurbo")}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </DefaultsScreenLayout>
  )
}
