import { AlertCircle, X } from "lucide-react"

import { Button } from "@/components/ui/Button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { getDefaultUsage } from "@/features/defaults/defaultUsage"
import { useDefaultsForm } from "@/features/defaults/useDefaultsForm"
import { ImagePromptTester } from "@/features/prompt-tester/ImagePromptTester"
import { modelLabel } from "@/lib/catalog"
import { saveImageDefaults } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AppState, Catalog } from "@/types/api"

export const ImageDefaultsScreen = () => {
  const state = useAppStore((store) => store.state)
  const catalog = useAppStore((store) => store.catalog)
  if (state === null || catalog === null) {
    return <div className="min-h-0 flex-1 animate-pulse bg-white/[0.015]" />
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
    <section
      className="flex min-h-0 flex-1 flex-col"
      data-testid="image-defaults-screen"
    >
      <header className="flex shrink-0 items-center justify-between gap-6 border-b border-white/[0.065] px-6 py-5">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span aria-hidden className="text-lg leading-none">
              🖼️
            </span>
            <h1 className="truncate text-[21px] leading-tight font-bold tracking-[-0.025em] text-zinc-100">
              Default Image Model
            </h1>
          </div>
          <p className="mt-1.5 truncate text-xs text-ink-muted">
            The model your image Smart Fields use unless a field pins its own.
          </p>
        </div>
        <span className="shrink-0 rounded-full border border-white/[0.08] bg-white/[0.025] px-3 py-1.5 text-[10.5px] text-zinc-400">
          Applies to {usage.following} field{usage.following === 1 ? "" : "s"}
          {usage.pinned > 0 && (
            <span className="text-amber"> · {usage.pinned} pinned</span>
          )}
        </span>
      </header>

      {controls.form.error !== null && (
        <div className="mx-6 mt-4 flex items-start gap-2 rounded-lg border border-red-300/15 bg-red-300/[0.06] px-3 py-2.5 text-xs text-danger">
          <AlertCircle aria-hidden className="mt-0.5 size-3.5 shrink-0" />
          <p className="min-w-0 flex-1">{controls.form.error}</p>
          <button className="cursor-pointer" onClick={controls.dismissError}>
            <X aria-hidden className="size-3.5" />
          </button>
        </div>
      )}

      <div className="grid min-h-0 flex-1 grid-cols-[minmax(290px,0.9fr)_minmax(340px,1.1fr)] px-6 py-5 max-[820px]:grid-cols-1 max-[820px]:overflow-y-auto">
        <div className="flex min-h-0 flex-col border-r border-white/[0.07] pr-6 max-[820px]:border-r-0 max-[820px]:pr-0">
          <div className="min-h-0 flex-1 overflow-y-auto pr-1">
            <label
              className="mb-2 block text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase"
              htmlFor="default-image-model"
            >
              Default model
            </label>
            <Select
              onValueChange={(model) => {
                const selected = catalog.image.models.find(
                  (item) => item.id === model,
                )
                if (selected === undefined)
                  throw new Error(`Image catalog is missing model ${model}`)
                controls.patchDraft({ model, provider: selected.provider })
              }}
              value={controls.form.values.model}
            >
              <SelectTrigger id="default-image-model">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {catalog.image.models.map((model) => (
                  <SelectItem key={model.id} value={model.id}>
                    <span className="min-w-0 flex-1 truncate font-semibold text-zinc-100">
                      {modelLabel(model.id)}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

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
                following the image default
                {usage.pinned > 0 && (
                  <>
                    {" "}
                    ·{" "}
                    <strong>
                      {usage.pinned} pinned field{usage.pinned === 1 ? "" : "s"}
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

        <div className="min-h-0 overflow-y-auto pl-6 max-[820px]:mt-6 max-[820px]:border-t max-[820px]:border-white/[0.07] max-[820px]:pt-6 max-[820px]:pl-0">
          <ImagePromptTester settings={controls.form.values} />
        </div>
      </div>
    </section>
  )
}
