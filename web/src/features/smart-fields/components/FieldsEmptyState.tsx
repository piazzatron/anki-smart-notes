import { Layers3, Plus } from "lucide-react"

import { Button } from "@/components/ui/Button"

export const FieldsEmptyState = () => (
  <div className="flex flex-1 items-center justify-center p-8 text-center">
    <div className="max-w-sm">
      <span className="mx-auto inline-flex size-11 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.03] text-indigo-soft">
        <Layers3 aria-hidden className="size-5" />
      </span>
      <h2 className="mt-4 text-base font-semibold text-zinc-100">
        Create your first Smart Field
      </h2>
      <p className="mt-1.5 text-xs leading-5 text-ink-muted">
        Choose a field on your cards and Smart Notes will fill it with text,
        audio, or an image.
      </p>
      <Button className="mt-4" disabled variant="primary">
        <Plus aria-hidden className="size-3.5" />
        New Smart Field
      </Button>
    </div>
  </div>
)
