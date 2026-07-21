import { AlertCircle, X } from "lucide-react"

import { Button } from "@/components/ui/Button"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select"
import { getDefaultUsage } from "@/features/defaults/defaultUsage"
import { useDefaultsForm } from "@/features/defaults/useDefaultsForm"
import { PromptTester } from "@/features/prompt-tester/PromptTester"
import { modelCostLabel, modelLabel, providerLabel } from "@/lib/catalog"
import { saveChatDefaults } from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AppState, Catalog } from "@/types/api"

import { getProviderForModel } from "./textDefaults"

export const TextDefaultsScreen = () => {
  const state = useAppStore((store) => store.state)
  const catalog = useAppStore((store) => store.catalog)

  if (state === null || catalog === null) {
    return (
      <section
        aria-label="Loading Text Defaults"
        className="flex min-h-0 flex-1 animate-pulse flex-col"
      >
        <div className="h-[86px] border-b border-white/[0.065] px-6 py-5">
          <div className="h-5 w-48 rounded bg-white/[0.06]" />
          <div className="mt-3 h-3 w-80 rounded bg-white/[0.035]" />
        </div>
        <div className="grid min-h-0 flex-1 grid-cols-2 gap-8 p-6">
          <div className="h-40 rounded-lg bg-white/[0.025]" />
          <div className="h-56 rounded-lg bg-white/[0.025]" />
        </div>
      </section>
    )
  }

  return <LoadedTextDefaultsScreen catalog={catalog} state={state} />
}

interface LoadedTextDefaultsScreenProps {
  catalog: Catalog
  state: AppState
}

const LoadedTextDefaultsScreen = ({
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
    <section
      className="flex min-h-0 flex-1 flex-col"
      data-testid="text-defaults-screen"
    >
      <header className="flex shrink-0 items-center justify-between gap-6 border-b border-white/[0.065] px-6 py-5">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span aria-hidden className="text-lg leading-none">
              💬
            </span>
            <h1 className="truncate text-[21px] leading-tight font-bold tracking-[-0.025em] text-zinc-100">
              Default Text Model
            </h1>
          </div>
          <p className="mt-1.5 truncate text-xs text-ink-muted">
            The model your text Smart Fields use unless a field pins its own.
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
          <button aria-label="Dismiss error" onClick={controls.dismissError}>
            <X aria-hidden className="size-3.5" />
          </button>
        </div>
      )}

      <div className="grid min-h-0 flex-1 grid-cols-[minmax(290px,0.9fr)_minmax(340px,1.1fr)] px-6 py-5 max-[820px]:grid-cols-1 max-[820px]:overflow-y-auto">
        <div className="flex min-h-0 flex-col border-r border-white/[0.07] pr-6 max-[820px]:border-r-0 max-[820px]:pr-0">
          <div className="min-h-0 flex-1 overflow-y-auto pr-1">
            <label
              className="mb-2 block text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase"
              htmlFor="default-text-model"
            >
              Default model
            </label>
            <Select
              onValueChange={(model) =>
                controls.patchDraft({
                  model,
                  provider: getProviderForModel(catalog, model),
                })
              }
              value={controls.form.values.model}
            >
              <SelectTrigger id="default-text-model">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {catalog.chat.providers.map((provider) => (
                  <SelectGroup key={provider}>
                    <SelectLabel>{providerLabel(provider)}</SelectLabel>
                    {catalog.chat.models
                      .filter((model) => model.provider === provider)
                      .map((model) => {
                        const costLabel = modelCostLabel(model.id)
                        return (
                          <SelectItem key={model.id} value={model.id}>
                            <span className="min-w-0 flex-1 truncate font-semibold text-zinc-100">
                              {modelLabel(model.id)}
                            </span>
                            {costLabel !== undefined && (
                              <span className="shrink-0 rounded bg-white/[0.06] px-2 py-0.5 text-[10px] font-semibold whitespace-nowrap text-zinc-400">
                                {costLabel}
                              </span>
                            )}
                          </SelectItem>
                        )
                      })}
                  </SelectGroup>
                ))}
              </SelectContent>
            </Select>

            <div className="mt-4 flex items-start gap-4 border-t border-white/[0.065] pt-4">
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
              <button
                aria-checked={controls.form.values.webSearchEnabled}
                aria-label="Enable Web Search"
                className={`relative mt-0.5 h-5 w-9 shrink-0 rounded-full transition ${
                  controls.form.values.webSearchEnabled
                    ? "bg-indigo"
                    : "bg-white/10"
                }`}
                onClick={() =>
                  controls.patchDraft({
                    webSearchEnabled: !controls.form.values.webSearchEnabled,
                  })
                }
                role="switch"
              >
                <span
                  className={`absolute top-0.5 size-4 rounded-full bg-white shadow transition ${
                    controls.form.values.webSearchEnabled
                      ? "left-[18px]"
                      : "left-0.5"
                  }`}
                />
              </button>
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
                following the text default
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

        <div className="min-h-0 overflow-y-auto pl-6 max-[820px]:mt-6 max-[820px]:border-t max-[820px]:border-white/[0.07] max-[820px]:pt-6 max-[820px]:pl-0">
          <PromptTester settings={controls.form.values} />
        </div>
      </div>
    </section>
  )
}
