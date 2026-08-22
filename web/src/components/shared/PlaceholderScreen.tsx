import { PageLayout } from "./PageLayout"
import { useTranslation } from "react-i18next"

import type { ScreenId } from "@/lib/boot"

const SCREEN_LABELS: Record<ScreenId, string> = {
  fields: "smartFields",
  "defaults-text": "defaultsText",
  "defaults-images": "defaultsImages",
  "defaults-voice": "defaultsVoice",
  settings: "settings",
  subscription: "subscription",
  support: "support",
}

interface PlaceholderScreenProps {
  screen: ScreenId
}

export const PlaceholderScreen = ({ screen }: PlaceholderScreenProps) => {
  const { t } = useTranslation()

  return (
    <PageLayout
      testId="placeholder-screen"
      title={t(`sidebar.nav.${SCREEN_LABELS[screen]}`)}
    >
      <div className="flex flex-1 items-center justify-center text-center">
        <p className="mt-1 text-xs text-ink-faint">
          {t("common.placeholderScreen")}
        </p>
      </div>
    </PageLayout>
  )
}
