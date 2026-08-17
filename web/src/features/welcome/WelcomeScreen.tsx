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

import { useState } from "react"

import { ConnectionNotice } from "@/components/shared/ConnectionNotice"
import { errorMessage } from "@/lib/errors"
import { openSiteLink, SITE_LINKS } from "@/lib/siteLinks"
import { exchangeAuthCode } from "@/services/commands"
import type { Connection } from "@/store/appStore"

interface WelcomeScreenProps {
  appVersion: string | null
  connection: Connection
}

// Grouped and organic, not a mirror: a loose crown arcs above the wordmark
// (weighted center-right, toward the ✨), a light pair sits off to the left, a
// denser group gathers up near the title sparkle, and a small pair trails
// lower-right. The weight leans right without any side clumping in a corner.
const WELCOME_SPARKLES = [
  // Crown above the wordmark
  { delay: "-1.7s", duration: "15s", size: "6px", left: "9%", top: "7%" },
  { delay: "-0.6s", duration: "18s", size: "8px", left: "44%", top: "8%" },
  { delay: "-2.9s", duration: "13s", size: "10px", left: "57%", top: "4%" },
  { delay: "-1.3s", duration: "16s", size: "6px", left: "67%", top: "10%" },
  // Left pair
  { delay: "-0.3s", duration: "17s", size: "9px", left: "14%", top: "20%" },
  { delay: "-2.4s", duration: "19s", size: "6px", left: "5%", top: "34%" },
  // Right group, near the title sparkle
  { delay: "-3.2s", duration: "16s", size: "14px", left: "86%", top: "14%" },
  { delay: "-0.8s", duration: "13s", size: "8px", left: "93%", top: "24%" },
  { delay: "-1.9s", duration: "18s", size: "7px", left: "78%", top: "22%" },
  { delay: "-3.6s", duration: "15s", size: "6px", left: "95%", top: "37%" },
  // Lower-right pair
  { delay: "-0.5s", duration: "20s", size: "9px", left: "88%", top: "74%" },
  { delay: "-2.1s", duration: "17s", size: "6px", left: "81%", top: "86%" },
  // Lower-left straggler
  { delay: "-1.5s", duration: "16s", size: "7px", left: "14%", top: "82%" },
] as const

export const WelcomeScreen = ({
  appVersion,
  connection,
}: WelcomeScreenProps) => {
  const [code, setCode] = useState("")
  const [codeError, setCodeError] = useState<string | null>(null)
  const [isSubmittingCode, setIsSubmittingCode] = useState(false)
  const [isWaitingForBrowser, setIsWaitingForBrowser] = useState(false)

  const openOnboarding = (url: string) => {
    setIsWaitingForBrowser(true)
    openSiteLink(url)
  }

  const submitCode = async () => {
    setCodeError(null)
    setIsSubmittingCode(true)
    try {
      await exchangeAuthCode(code)
    } catch (error) {
      setCodeError(errorMessage(error, "Could not connect with that code"))
      setIsSubmittingCode(false)
    }
  }

  return (
    <main className="relative isolate flex h-full min-h-0 flex-col overflow-hidden bg-canvas text-ink">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(640px 440px at 50% 68%, rgba(31,212,125,0.05), transparent 70%), radial-gradient(620px 420px at 50% 30%, rgba(124,141,255,0.04), transparent 70%)",
        }}
      />
      <ConnectionNotice connection={connection} />
      <div className="relative z-10 flex min-h-0 flex-1 items-center justify-center px-6 py-12 text-center">
        {isWaitingForBrowser ? (
          <div className="w-full max-w-[360px]">
            <div className="welcome-enter">
              <div className="mx-auto size-[46px] animate-spin rounded-full border-[2.5px] border-indigo/15 border-t-indigo" />
            </div>
            <h1
              className="welcome-enter mt-[22px] text-lg font-semibold tracking-[-0.2px] text-[#f4f4f6]"
              style={{ animationDelay: "70ms" }}
            >
              Finish up in your browser
            </h1>
            <p
              className="welcome-enter mx-auto mt-2 max-w-[330px] text-[12.5px] leading-[1.6] text-[#8b8b94]"
              style={{ animationDelay: "140ms" }}
            >
              Complete sign-in in the browser we opened. This window will update
              automatically.
            </p>

            <form
              className="welcome-enter mt-7 rounded-[11px] border border-white/[0.07] bg-black/20 p-4 text-left"
              onSubmit={(event) => {
                event.preventDefault()
                void submitCode()
              }}
              style={{ animationDelay: "210ms" }}
            >
              <label
                className="text-[11.5px] font-medium text-[#b4b4be]"
                htmlFor="welcome-auth-code"
              >
                Have a code from the website?
              </label>
              <div className="mt-2 flex gap-2">
                <input
                  autoCapitalize="characters"
                  autoComplete="off"
                  className="min-w-0 flex-1 rounded-lg border border-white/[0.08] bg-white/[0.04] px-3 py-2.5 font-mono text-xs tracking-[0.08em] text-zinc-100 transition outline-none focus:border-indigo/55 focus:ring-2 focus:ring-indigo/15"
                  disabled={isSubmittingCode}
                  id="welcome-auth-code"
                  onChange={(event) =>
                    setCode(event.target.value.toUpperCase())
                  }
                  placeholder="Paste your code"
                  spellCheck={false}
                  value={code}
                />
                <button
                  className="rounded-lg bg-indigo px-4 py-2.5 text-xs font-bold text-white transition hover:bg-[#8a99ff] disabled:opacity-40"
                  disabled={!code.trim() || isSubmittingCode}
                  type="submit"
                >
                  {isSubmittingCode ? "Connecting…" : "Connect"}
                </button>
              </div>
              {codeError !== null && (
                <p className="mt-2 text-[11px] leading-4 text-danger">
                  {codeError}
                </p>
              )}
            </form>
          </div>
        ) : (
          <div className="relative w-full max-w-[380px]">
            <div
              aria-hidden
              className="pointer-events-none absolute top-1/2 left-1/2 -z-10 h-[430px] w-[560px] -translate-x-1/2 -translate-y-1/2"
            >
              {WELCOME_SPARKLES.map((sparkle) => (
                <span
                  className="welcome-sparkle"
                  key={`${sparkle.left}-${sparkle.top}`}
                  style={
                    {
                      "--welcome-sparkle-delay": sparkle.delay,
                      "--welcome-sparkle-duration": sparkle.duration,
                      fontSize: sparkle.size,
                      left: sparkle.left,
                      top: sparkle.top,
                    } as React.CSSProperties
                  }
                >
                  <span className="welcome-sparkle-glyph">✦</span>
                </span>
              ))}
            </div>

            <div className="relative mx-auto w-fit">
              <h1 className="welcome-enter text-[38px] leading-none font-extrabold tracking-[-0.037em] text-[#f6f6f8]">
                Smart Notes
                <span
                  aria-hidden
                  className="ml-1 inline-block translate-y-[-6px] text-[26px] font-normal"
                >
                  ✨
                </span>
              </h1>
            </div>

            <p
              className="welcome-enter mt-[13px] text-[14.5px] leading-[1.55] font-semibold text-[#eaeaef]"
              style={{ animationDelay: "80ms" }}
            >
              Add text, speech, and images to individual cards or your entire
              deck in one click.
            </p>

            <div
              className="welcome-enter mx-auto mt-8 w-full max-w-[356px]"
              style={{ animationDelay: "160ms" }}
            >
              <button
                className="w-full rounded-[14px] border border-[#1fd47d]/60 bg-gradient-to-b from-[#4cf0a8] to-[#1fd47d] px-5 py-[19px] text-[17px] font-extrabold tracking-[0.1px] text-[#06281a] shadow-[inset_0_1px_0_rgba(255,255,255,0.36),0_16px_36px_-10px_rgba(31,212,125,0.66)] transition-[filter,transform] duration-150 hover:scale-[1.01] hover:brightness-105"
                onClick={() => openOnboarding(SITE_LINKS.startTrial)}
                type="button"
              >
                ✨ Start Free Trial ✨
              </button>
              <p className="mt-[15px] text-xs text-[#b6b6bf]">
                Free for 7 days · every feature · no credit card
              </p>
            </div>

            <p
              className="welcome-enter mt-7 text-[12.5px] text-[#8b8b94]"
              style={{ animationDelay: "240ms" }}
            >
              Already have an account?{" "}
              <button
                className="font-medium text-[#a5b4ff] transition-colors hover:text-white"
                onClick={() => openOnboarding(SITE_LINKS.signIn)}
                type="button"
              >
                Sign in
              </button>
            </p>
          </div>
        )}
      </div>

      {appVersion !== null && (
        <p
          className="welcome-enter absolute right-0 bottom-3.5 left-0 z-10 text-center font-mono text-[10px] text-[#5c5c66]"
          style={{ animationDelay: "320ms" }}
        >
          Smart Notes v{appVersion}
        </p>
      )}
    </main>
  )
}
