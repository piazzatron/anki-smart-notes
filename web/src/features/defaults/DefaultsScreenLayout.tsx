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

import { LoaderCircle } from "lucide-react"
import type { ReactNode } from "react"
import { useTranslation } from "react-i18next"

import { PageLayout } from "@/components/shared/PageLayout"
import {
  openUpgradeSheet,
  type UpgradeFeature,
} from "@/components/shared/UpgradeSheet"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"

interface DefaultsScreenLayoutProps {
  accessory: ReactNode
  children: ReactNode
  contentFillsHeight?: boolean
  icon: ReactNode
  isDirty: boolean
  isSaving: boolean
  onSave: () => void
  tester: ReactNode
  testerAccessory?: ReactNode
  testId: string
  title: string
  /** Set on the free plan when this screen's field type is a paid feature, or
   *  only partly included (voices). */
  upgradeFeature?: Extract<UpgradeFeature, "voice" | "images">
}

export const DefaultsScreenLayout = ({
  accessory,
  children,
  contentFillsHeight = false,
  icon,
  isDirty,
  isSaving,
  onSave,
  tester,
  testerAccessory,
  testId,
  title,
  upgradeFeature,
}: DefaultsScreenLayoutProps) => {
  const { t } = useTranslation()

  return (
    <PageLayout
      actions={
        // A fixed height the save button overhangs (centered), so neither the header
        // nor the title moves when it appears.
        <div className="flex h-8 items-center gap-3">
          {accessory}
          {isDirty && (
            <Button
              className="h-9 px-3.5"
              disabled={isSaving}
              onClick={onSave}
              variant="primary"
            >
              {isSaving
                ? t("defaults.layout.saving")
                : t("defaults.layout.save")}
            </Button>
          )}
        </div>
      }
      className={contentFillsHeight ? "h-full" : undefined}
      icon={icon}
      testId={testId}
      title={title}
    >
      {upgradeFeature !== undefined && (
        <div className="hang mb-8 flex items-center gap-4 rounded-xl bg-indigo/[0.16] py-3.5">
          <p className="min-w-0 flex-1 text-sm font-medium text-indigo-soft">
            {t(`upgradeSheet.notices.${upgradeFeature}`)}
          </p>
          <Button
            onClick={() => openUpgradeSheet(upgradeFeature)}
            variant="primary"
          >
            {t("upgradeSheet.seePlans")}
          </Button>
        </div>
      )}
      {children}
      <div className={contentFillsHeight ? "mt-auto pt-10" : "mt-10"}>
        <div className="mb-[22px] flex min-h-[22px] items-center gap-4">
          <h2 className="text-base font-semibold text-ink">
            {t("defaults.layout.tryIt")}
          </h2>
          {testerAccessory}
        </div>
        <Card className="hang py-5">{tester}</Card>
      </div>
    </PageLayout>
  )
}

export const DefaultsScreenLoading = ({
  icon,
  label,
  title,
}: {
  icon: ReactNode
  label: string
  title: string
}) => (
  <PageLayout icon={icon} testId="defaults-screen-loading" title={title}>
    <div className="flex flex-1 items-center justify-center">
      <LoaderCircle
        aria-label={label}
        className="size-5 animate-spin text-indigo-soft"
      />
    </div>
  </PageLayout>
)
