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

import { useState, type ReactNode } from "react"
import { useTranslation } from "react-i18next"

import { useFeedbackForm } from "./useFeedbackForm"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/Dialog"
import { ErrorBanner } from "@/components/ui/ErrorBanner"

interface FeedbackDialogProps {
  children: ReactNode
}

export const FeedbackDialog = ({ children }: FeedbackDialogProps) => {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const form = useFeedbackForm()

  return (
    <Dialog
      onOpenChange={(nextOpen) => {
        if (nextOpen) {
          form.patch({
            error: null,
            isSending: false,
            message: "",
            sent: false,
          })
        }
        setOpen(nextOpen)
      }}
      open={open}
    >
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="w-[min(440px,92vw)]">
        <header className="shrink-0 border-b border-white/[0.07] py-3.5 ps-5 pe-10">
          <DialogTitle className="text-[13px] font-bold text-ink">
            {t("common.feedback.title")}
          </DialogTitle>
          <DialogDescription className="sr-only">
            {t("common.feedback.description")}
          </DialogDescription>
        </header>

        {form.state.sent ? (
          <p className="px-5 py-5 text-xs text-mint">
            {t("common.feedback.sent")}
          </p>
        ) : (
          <>
            <div className="px-5 py-4">
              {form.state.error !== null && (
                <ErrorBanner
                  className="mb-3"
                  message={form.state.error}
                  onDismiss={() => form.patch({ error: null })}
                />
              )}
              <textarea
                aria-label={t("common.feedback.label")}
                className="min-h-[112px] w-full resize-y rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2.5 text-xs leading-[1.5] text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-indigo/45"
                onChange={(event) => form.setMessage(event.target.value)}
                placeholder={t("common.feedback.placeholder")}
                value={form.state.message}
              />
            </div>
            <footer className="flex shrink-0 items-center justify-between gap-3 border-t border-white/[0.07] px-5 py-3.5">
              <button
                className="ms-auto rounded-md bg-mint px-4 py-2 text-xs font-semibold text-emerald-950 transition hover:bg-mint/90 disabled:cursor-not-allowed disabled:opacity-45"
                disabled={form.isSubmitDisabled}
                onClick={() => void form.submit()}
                type="button"
              >
                {form.state.isSending
                  ? t("common.feedback.sending")
                  : t("common.feedback.send")}
              </button>
            </footer>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
