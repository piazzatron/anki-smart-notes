/*
 * Copyright (C) 2024 Michael Piazza
 *
 * This file is part of Smart Notes.
 *
 * Smart Notes is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Smart Notes is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Smart Notes. If not, see <https://www.gnu.org/licenses/>.
 */

import { Lock } from "lucide-react"
import type { ComponentType } from "react"
import { useTranslation } from "react-i18next"
import { create } from "zustand"

import {
  BoltIcon,
  CardIcon,
  CogIcon,
  GalleryIcon,
  type IconProps,
  SearchIcon,
  SparklesIcon,
  VolumeIcon,
} from "@/components/shared/Icons"
import { dailyResetTime } from "@/components/shared/planPresentation"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { ProgressBar } from "@/components/ui/ProgressBar"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/Dialog"
import { openSiteLink, SITE_LINKS } from "@/lib/siteLinks"
import { useAppStore } from "@/store/appStore"

/** What a free user reached for: each has its own title and line in the sheet. */
export type UpgradeFeature =
  | "intelligence"
  | "models"
  | "webSearch"
  | "voice"
  | "images"
  | "generateOnAdd"
  | "generateAtReview"
  | "dailyLimit"
  | "batch"

const FEATURE_ICONS: Record<UpgradeFeature, ComponentType<IconProps>> = {
  intelligence: BoltIcon,
  models: SparklesIcon,
  webSearch: SearchIcon,
  voice: VolumeIcon,
  images: GalleryIcon,
  generateOnAdd: CogIcon,
  generateAtReview: CogIcon,
  dailyLimit: SparklesIcon,
  batch: CardIcon,
}

// The last feature stays set after closing, so the sheet keeps its content while
// it animates out.
const useUpgradeSheetStore = create<{
  feature: UpgradeFeature | null
  open: boolean
}>(() => ({ feature: null, open: false }))

/** Opens the upgrade sheet for a feature the free plan doesn't include. */
export const openUpgradeSheet = (feature: UpgradeFeature) =>
  useUpgradeSheetStore.setState({ feature, open: true })

/** Whether the signed-in account is on the free plan, where paid features are
 *  shown but open the upgrade sheet instead of working. */
export const useIsFreePlan = () =>
  useAppStore(
    (store) =>
      store.state?.account.status === "AUTHENTICATED" &&
      store.state.account.plan.planType === "free",
  )

/** The lock on anything the free plan doesn't include. Decorative: name the
 *  control it sits on instead. */
export const UpgradeLockIcon = ({ className = "" }: { className?: string }) => (
  <Lock
    aria-hidden
    className={`size-3.5 shrink-0 ${className}`}
    strokeWidth={2.25}
  />
)

/** Stands in for a control the free plan doesn't include: the control's row is
 *  greyed out (`opacity-40`) and this lock opens the upgrade sheet. */
export const UpgradeLock = ({ feature }: { feature: UpgradeFeature }) => {
  const { t } = useTranslation()
  return (
    <button
      aria-label={t(`upgradeSheet.features.${feature}.cta`)}
      className="shrink-0 cursor-pointer text-ink-muted transition hover:text-ink"
      onClick={(event) => {
        event.stopPropagation()
        openUpgradeSheet(feature)
      }}
      type="button"
    >
      <UpgradeLockIcon />
    </button>
  )
}

const FeatureIcon = ({ feature }: { feature: UpgradeFeature }) => {
  const Icon = FEATURE_ICONS[feature]
  return <Icon size={22} />
}

/** The one sheet every gated control opens: what the feature does, and the way to
 *  the plans. Mounted once, in App. */
export const UpgradeSheet = () => {
  const { t } = useTranslation()
  const { feature, open } = useUpgradeSheetStore()
  const close = () => useUpgradeSheetStore.setState({ open: false })
  const plan = useAppStore((store) =>
    store.state?.account.status === "AUTHENTICATED"
      ? store.state.account.plan
      : null,
  )
  const dailyNotes =
    plan?.dailyNotesLimit == null
      ? null
      : { used: plan.dailyNotesUsed ?? 0, limit: plan.dailyNotesLimit }

  return (
    <Dialog onOpenChange={(isOpen) => !isOpen && close()} open={open}>
      <DialogContent className="w-[min(400px,92vw)]">
        {feature !== null && (
          <>
            <div className="px-6 pt-7 pb-5 text-center">
              <span className="mx-auto grid size-11 place-items-center rounded-xl bg-indigo/[0.16] text-indigo-soft">
                <FeatureIcon feature={feature} />
              </span>
              <DialogTitle className="mt-4 text-[17px] font-bold text-ink">
                {t(`upgradeSheet.features.${feature}.title`)}
              </DialogTitle>
              <DialogDescription className="mt-1.5 text-[13px] leading-5 text-ink-muted">
                {t(`upgradeSheet.features.${feature}.description`, {
                  count: dailyNotes?.limit ?? 0,
                })}
              </DialogDescription>
              {feature === "dailyLimit" && dailyNotes !== null && (
                <Card className="mt-5 px-4 py-3.5 text-start">
                  <div className="flex items-center justify-between text-[13px]">
                    <span className="font-semibold text-ink">
                      {t("subscription.free.notesToday", dailyNotes)}
                    </span>
                    <span className="text-ink-muted">
                      {t("upgradeSheet.moreNotesAt", {
                        time: dailyResetTime(),
                      })}
                    </span>
                  </div>
                  <ProgressBar
                    colorClass="bg-danger"
                    heightClass="h-1.5"
                    percent={(dailyNotes.used / dailyNotes.limit) * 100}
                    trackClass="mt-2.5 bg-white/[0.08]"
                  />
                </Card>
              )}
            </div>
            <div className="flex flex-col items-center gap-1.5 px-6 pb-5">
              <Button
                className="h-11 w-full text-[14px] font-bold"
                onClick={() => {
                  openSiteLink(SITE_LINKS.upgrade)
                  close()
                }}
                variant="success"
              >
                {t(`upgradeSheet.features.${feature}.cta`)}
              </Button>
              <button
                className="cursor-pointer px-3 py-1.5 text-[13px] text-ink-muted transition hover:text-ink"
                onClick={close}
                type="button"
              >
                {t("common.notNow")}
              </button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
