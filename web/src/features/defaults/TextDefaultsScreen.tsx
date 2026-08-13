import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { Toggle } from "@/components/ui/Toggle"
import { PromptTester } from "@/features/prompt-tester/PromptTester"
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
import { DefaultUsagePill } from "./DefaultUsagePill"
import { getDefaultUsage } from "./defaultUsage"
import { useDefaultsForm } from "./useDefaultsForm"

export const TextDefaultsScreen = () => {
  const state = useAppStore((store) => store.state)
  const catalog = useAppStore((store) => store.catalog)

  if (state === null || catalog === null) {
    return <DefaultsScreenLoading label="Loading Default Text Settings" />
  }

  return <LoadedTextDefaultsScreen catalog={catalog} state={state} />
}

interface LoadedTextDefaultsScreenProps {
  catalog: Catalog
  state: AppState
}

export const LoadedTextDefaultsScreen = ({
  catalog,
  state,
}: LoadedTextDefaultsScreenProps) => {
  const controls = useDefaultsForm({
    fallbackError: "Could not save text defaults",
    save: saveChatDefaults,
    serverDefaults: state.defaults.chat,
  })
  const usage = getDefaultUsage(state.smartFields, "chat")

  return (
    <DefaultsScreenLayout
      accessory={<DefaultUsagePill usage={usage} />}
      icon={
        <span aria-hidden className="text-lg leading-none">
          💬
        </span>
      }
      subtitle="The model your text Smart Fields use unless a field pins its own."
      tester={<PromptTester settings={controls.form.values} />}
      testId="text-defaults-screen"
      title="Default Text Settings"
    >
      {controls.form.error !== null && (
        <ErrorBanner
          className="mx-6 mt-4"
          message={controls.form.error}
          onDismiss={controls.dismissError}
        />
      )}

      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
        <div className="grid w-full max-w-[900px] gap-6 lg:grid-cols-2">
          <div>
            <label
              className="mb-2 block text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase"
              htmlFor="default-text-model"
            >
              Default model
            </label>
            <ChatModelSelect
              catalog={catalog.chat}
              id="default-text-model"
              onValueChange={(model) => {
                if (model === null) {
                  throw new Error("Text defaults cannot inherit another model")
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
                  Reasoning level
                </span>
                <ReasoningLevelSelect
                  ariaLabel="Default reasoning level"
                  levels={catalog.chat.reasoningLevels}
                  onValueChange={(reasoningLevel) =>
                    void controls.updateDefault({ reasoningLevel })
                  }
                  value={controls.form.values.reasoningLevel}
                />
                <span className="mt-2 block text-[10.5px] leading-4 text-ink-muted">
                  Higher reasoning can improve harder generations, but uses more
                  credits.
                </span>
              </label>
            )}

            <div
              className={`flex items-start gap-4 ${controls.form.values.provider === "auto" ? "mt-4 border-t border-white/[0.065] pt-4" : ""}`}
            >
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-zinc-200">
                  Web Search
                </p>
                <p className="mt-1 text-[11px] leading-4 text-ink-muted">
                  Let text generations pull in fresh info from the web.
                </p>
                <p className="mt-1.5 text-[10.5px] text-amber/80">
                  ⚠️ Search is expensive; monitor your credits.
                </p>
              </div>
              <div className="mt-0.5">
                <Toggle
                  aria-label="Enable Web Search"
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
