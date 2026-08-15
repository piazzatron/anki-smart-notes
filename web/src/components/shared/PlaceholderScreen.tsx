import { PageLayout } from "./PageLayout"

import type { ScreenId } from "@/lib/boot"

const SCREEN_LABELS: Record<ScreenId, string> = {
  fields: "Smart Fields",
  "defaults-text": "Default Text Settings",
  "defaults-images": "Default Image Settings",
  "defaults-voice": "Default Voice Settings",
  settings: "Settings",
  subscription: "Subscription",
  support: "Support",
}

interface PlaceholderScreenProps {
  screen: ScreenId
}

export const PlaceholderScreen = ({ screen }: PlaceholderScreenProps) => (
  <PageLayout testId="placeholder-screen" title={SCREEN_LABELS[screen]}>
    <div className="flex flex-1 items-center justify-center text-center">
      <p className="mt-1 text-xs text-ink-faint">
        This screen is next in the rebuild.
      </p>
    </div>
  </PageLayout>
)
