import { ErrorBanner } from "@/components/ui/ErrorBanner"
import { ImageModelSelect } from "@/features/image-generation/ImageModelSelect"
import { ImagePromptTester } from "@/features/prompt-tester/ImagePromptTester"
import { saveImageDefaults } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AppState, Catalog } from "@/types/api"

import {
  DefaultsScreenLayout,
  DefaultsScreenLoading,
} from "./DefaultsScreenLayout"
import { DefaultUsagePill } from "./DefaultUsagePill"
import { getDefaultUsage } from "./defaultUsage"
import { useDefaultsForm } from "./useDefaultsForm"

export const ImageDefaultsScreen = () => {
  const state = useAppStore((store) => store.state)
  const catalog = useAppStore((store) => store.catalog)
  if (state === null || catalog === null) {
    return <DefaultsScreenLoading label="Loading Image Defaults" />
  }

  return <LoadedImageDefaultsScreen catalog={catalog} state={state} />
}

interface LoadedImageDefaultsScreenProps {
  catalog: Catalog
  state: AppState
}

const LoadedImageDefaultsScreen = ({
  catalog,
  state,
}: LoadedImageDefaultsScreenProps) => {
  const controls = useDefaultsForm({
    fallbackError: "Could not save image defaults",
    save: saveImageDefaults,
    serverDefaults: state.defaults.image,
  })
  const usage = getDefaultUsage(state.smartFields, "image")

  return (
    <DefaultsScreenLayout
      accessory={<DefaultUsagePill usage={usage} />}
      icon={
        <span aria-hidden className="text-lg leading-none">
          🖼️
        </span>
      }
      subtitle="The model your image Smart Fields use unless a field pins its own."
      tester={
        <ImagePromptTester settings={controls.form.values} title="Try it" />
      }
      testId="image-defaults-screen"
      title="Default Image Model"
    >
      {controls.form.error !== null && (
        <ErrorBanner
          className="mx-6 mt-4"
          message={controls.form.error}
          onDismiss={controls.dismissError}
        />
      )}

      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
        <div className="mx-auto w-full max-w-[640px]">
          <label
            className="mb-2 block text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase"
            htmlFor="default-image-model"
          >
            Default model
          </label>
          <ImageModelSelect
            catalog={catalog.image}
            id="default-image-model"
            onValueChange={(settings) => void controls.updateDefault(settings)}
            value={controls.form.values.model}
          />

          <div className="mt-3 rounded-lg border border-indigo/15 bg-indigo/[0.055] p-3.5">
            <p className="text-xs font-semibold text-zinc-200">
              💡 Picking an image model
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-[11px] leading-4 text-ink-muted">
              <li>
                <strong className="text-zinc-300">GPT Image 1.5 Low</strong> —
                best quality / speed tradeoff.
              </li>
              <li>
                <strong className="text-zinc-300">
                  GPT Image 2 (Low / Medium)
                </strong>{" "}
                — same cost, slower, higher quality.
              </li>
              <li>
                <strong className="text-zinc-300">Z-Image Turbo</strong> —
                fastest and cheapest.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </DefaultsScreenLayout>
  )
}
