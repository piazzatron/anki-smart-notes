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

import type { CSSProperties } from "react"
import { useState } from "react"
import { useTranslation } from "react-i18next"

import { Button } from "@/components/ui/Button"
import { errorMessage } from "@/lib/errors"
import { exchangeAuthCode } from "@/services/commands"

interface AuthCodeFormProps {
  className?: string
  style?: CSSProperties
}

/** The box a signed-out user pastes the website's one-time sign-in code into. */
export const AuthCodeForm = ({ className = "", style }: AuthCodeFormProps) => {
  const { t } = useTranslation()
  const [code, setCode] = useState("")
  const [codeError, setCodeError] = useState<string | null>(null)
  const [isSubmittingCode, setIsSubmittingCode] = useState(false)

  const submitCode = async () => {
    setCodeError(null)
    setIsSubmittingCode(true)
    try {
      await exchangeAuthCode(code)
    } catch (error) {
      setCodeError(errorMessage(error, t("welcome.errors.code")))
      setIsSubmittingCode(false)
    }
  }

  return (
    <form
      className={`rounded-[11px] bg-black/20 p-4 text-start ${className}`}
      onSubmit={(event) => {
        event.preventDefault()
        void submitCode()
      }}
      style={style}
    >
      <label
        className="text-[12.5px] font-medium text-ink-muted"
        htmlFor="auth-code"
      >
        {t("welcome.haveCode")}
      </label>
      <div className="mt-2 flex gap-2">
        <input
          autoCapitalize="characters"
          autoComplete="off"
          // A sign-in credential: keep it out of session replays
          data-amp-mask
          className="min-w-0 flex-1 rounded-lg bg-white/[0.04] px-3 py-2.5 font-mono text-[13px] tracking-[0.08em] text-zinc-100 transition outline-none focus:ring-2 focus:ring-indigo/15"
          disabled={isSubmittingCode}
          id="auth-code"
          onChange={(event) => setCode(event.target.value.toUpperCase())}
          placeholder={t("welcome.codePlaceholder")}
          spellCheck={false}
          value={code}
        />
        <Button
          disabled={!code.trim() || isSubmittingCode}
          type="submit"
          variant="primary"
        >
          {isSubmittingCode ? t("welcome.connecting") : t("welcome.connect")}
        </Button>
      </div>
      {codeError !== null && (
        <p className="mt-2 text-xs leading-4 text-danger">{codeError}</p>
      )}
    </form>
  )
}
