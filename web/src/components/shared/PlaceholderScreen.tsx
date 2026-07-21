import type { ScreenId } from "@/lib/boot"

const SCREEN_LABELS: Record<ScreenId, string> = {
  fields: "Smart Fields",
  "defaults-text": "Text Defaults",
  "defaults-images": "Image Defaults",
  "defaults-voice": "Voice Defaults",
  settings: "Settings",
  subscription: "Subscription",
  support: "Support & Bugs",
}

interface PlaceholderScreenProps {
  screen: ScreenId
}

export const PlaceholderScreen = ({ screen }: PlaceholderScreenProps) => (
  <section className="flex h-full items-center justify-center p-8 text-center">
    <div>
      <p className="text-sm font-semibold text-zinc-300">
        {SCREEN_LABELS[screen]}
      </p>
      <p className="mt-1 text-xs text-ink-faint">
        This screen is next in the rebuild.
      </p>
    </div>
  </section>
)
