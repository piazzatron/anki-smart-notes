import {
  AlertCircle,
  ChevronDown,
  MessageSquareText,
  Search,
  X,
  Zap,
} from "lucide-react"

import { Button } from "@/components/ui/Button"
import { PromptTester } from "@/features/prompt-tester/PromptTester"
import { modelLabel, providerLabel } from "@/lib/catalog"
import { useAppStore } from "@/store/appStore"
import type { AppState, Catalog } from "@/types/api"

import { getProviderForModel, getTextDefaultUsage } from "./textDefaults"
import { useTextDefaultsState } from "./useTextDefaultsState"

const REASONING_LABELS: Record<string, string> = {
  off: "Off",
  low: "Low",
  high: "High",
}

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
  const controls = useTextDefaultsState({
    serverDefaults: state.defaults.chat,
  })
  const usage = getTextDefaultUsage(state.smartFields)

  return (
    <section
      className="flex min-h-0 flex-1 flex-col"
      data-testid="text-defaults-screen"
    >
      <header className="flex shrink-0 items-center justify-between gap-6 border-b border-white/[0.065] px-6 py-5">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <MessageSquareText
              aria-hidden
              className="size-5 text-indigo-soft"
            />
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
            <div className="relative">
              <select
                className="h-11 w-full cursor-pointer appearance-none rounded-lg border border-white/10 bg-white/[0.035] px-3 pr-9 text-xs font-medium text-zinc-100 transition outline-none hover:border-white/16 focus:border-indigo/50"
                id="default-text-model"
                onChange={(event) =>
                  controls.patchDraft({
                    model: event.target.value,
                    provider: getProviderForModel(catalog, event.target.value),
                  })
                }
                value={controls.form.values.model}
              >
                {catalog.chat.providers.map((provider) => (
                  <optgroup key={provider} label={providerLabel(provider)}>
                    {catalog.chat.models
                      .filter((model) => model.provider === provider)
                      .map((model) => (
                        <option key={model.id} value={model.id}>
                          {modelLabel(model.id)}
                        </option>
                      ))}
                  </optgroup>
                ))}
              </select>
              <ChevronDown
                aria-hidden
                className="pointer-events-none absolute top-3.5 right-3 size-4 text-ink-faint"
              />
            </div>
            {controls.form.values.provider === "auto" && (
              <p className="mt-2 text-[11px] leading-4 text-ink-muted">
                Smart routing chooses the best model for each card.
              </p>
            )}

            {controls.form.values.provider === "auto" && (
              <div className="mt-7">
                <p className="text-[10px] font-semibold tracking-[0.08em] text-ink-faint uppercase">
                  Reasoning
                </p>
                <div className="mt-2 grid grid-cols-3 gap-1 rounded-lg border border-white/[0.08] bg-white/[0.025] p-1">
                  {catalog.chat.reasoningLevels.map((level) => (
                    <button
                      aria-pressed={
                        controls.form.values.reasoningLevel === level
                      }
                      className={`rounded-md px-3 py-2 text-[11px] font-semibold transition ${
                        controls.form.values.reasoningLevel === level
                          ? "bg-indigo/18 text-indigo-soft"
                          : "text-zinc-500 hover:bg-white/[0.045] hover:text-zinc-300"
                      }`}
                      key={level}
                      onClick={() =>
                        controls.patchDraft({ reasoningLevel: level })
                      }
                    >
                      {REASONING_LABELS[level] ?? level}
                    </button>
                  ))}
                </div>
                <p className="mt-2 text-[10.5px] leading-4 text-amber/80">
                  Higher reasoning can improve harder generations but uses more
                  credits.
                </p>
              </div>
            )}

            <div className="mt-7 flex items-start gap-4 border-t border-white/[0.065] pt-6">
              <Search
                aria-hidden
                className="mt-0.5 size-4 shrink-0 text-zinc-500"
              />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-zinc-200">
                  Web Search
                </p>
                <p className="mt-1 text-[11px] leading-4 text-ink-muted">
                  Let text generations pull in fresh information from the web.
                </p>
                <p className="mt-1.5 text-[10.5px] text-amber/80">
                  Search is expensive; monitor your usage.
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
              <Zap aria-hidden className="size-4 shrink-0 text-amber" />
              <p className="min-w-0 flex-1 text-[10.5px] leading-4 text-zinc-300">
                Updates <strong>{usage.following} default-backed fields</strong>
                {usage.pinned > 0 && (
                  <> · {usage.pinned} pinned won&apos;t change</>
                )}
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
