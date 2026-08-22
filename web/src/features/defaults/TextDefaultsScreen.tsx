import { useState } from "react"
import { useTranslation } from "react-i18next"

import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { Toggle } from "@/components/ui/Toggle"
import { PromptTesterStrip } from "@/features/prompt-tester/PromptTesterStrip"
import { usePromptTester } from "@/features/prompt-tester/usePromptTester"
import { ChatModelSelect } from "@/features/text-generation/ChatModelSelect"
import { ReasoningLevelSelect } from "@/features/text-generation/ReasoningLevelSelect"
import { TextModelGuidance } from "@/features/text-generation/TextModelGuidance"
import { saveChatDefaults } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AppState, Catalog } from "@/types/api"

import {
  DefaultsScreenLayout,
  DefaultsScreenLoading,
} from "./DefaultsScreenLayout"
import { getDefaultUsage } from "./defaultUsage"
import { DefaultUsagePill } from "./DefaultUsagePill"
import { useDefaultsForm } from "./useDefaultsForm"

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
        icon={
          <span aria-hidden className="text-lg leading-none">
            💬
          </span>
        }
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
  const [prompt, setPrompt] = useState(() => t("defaults.text.samplePrompt"))
  const tester = usePromptTester({
    fieldType: "chat",
    onPromptChange: setPrompt,
    prompt,
    settings: controls.form.values,
  })

  return (
    <DefaultsScreenLayout
      accessory={<DefaultUsagePill usage={usage} />}
      icon={
        <span aria-hidden className="text-lg leading-none">
          💬
        </span>
      }
      isDirty={controls.form.isDirty}
      isSaving={controls.form.isSaving}
      onSave={() => void controls.saveChanges()}
      subtitle={t("defaults.text.subtitle")}
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

      <div>
        <div className="grid w-full gap-6 lg:grid-cols-2">
          <div>
            <label
              className="mb-2 block text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase"
              htmlFor="default-text-model"
            >
              {t("defaults.text.defaultModel")}
            </label>
            <ChatModelSelect
              catalog={catalog.chat}
              id="default-text-model"
              onValueChange={(model) => {
                if (model === null) {
                  throw new Error(t("defaults.text.cannotInheritModel"))
                }
                void controls.updateDefault({
                  model: model.id,
                  provider: model.provider,
                })
              }}
              value={controls.form.values.model}
            />
            <TextModelGuidance />
          </div>

          <div>
            {controls.form.values.provider === "auto" && (
              <label className="block">
                <span className="mb-2 block text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
                  {t("defaults.text.reasoningLevel")}
                </span>
                <ReasoningLevelSelect
                  ariaLabel={t("defaults.text.defaultReasoningLevel")}
                  levels={catalog.chat.reasoningLevels}
                  onValueChange={(reasoningLevel) =>
                    void controls.updateDefault({ reasoningLevel })
                  }
                  value={controls.form.values.reasoningLevel}
                />
                <span className="mt-2 block text-[10.5px] leading-4 text-ink-muted">
                  {t("defaults.text.higherReasoning")}
                </span>
              </label>
            )}

            <div
              className={`flex items-start gap-4 ${controls.form.values.provider === "auto" ? "mt-4 border-t border-white/[0.065] pt-4" : ""}`}
            >
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-zinc-200">
                  {t("defaults.text.webSearch")}
                </p>
                <p className="mt-1 text-[11px] leading-4 text-ink-muted">
                  {t("defaults.text.webSearchDescription")}
                </p>
                <p className="mt-1.5 text-[10.5px] text-amber/80">
                  {t("defaults.text.webSearchWarning")}
                </p>
              </div>
              <div className="mt-0.5">
                <Toggle
                  aria-label={t("defaults.text.enableWebSearch")}
                  checked={controls.form.values.webSearchEnabled}
                  onCheckedChange={(webSearchEnabled) =>
                    void controls.updateDefault({
                      webSearchEnabled,
                    })
                  }
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </DefaultsScreenLayout>
  )
}
