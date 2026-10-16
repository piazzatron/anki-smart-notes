import { useCallback, useEffect, useRef, useState } from "react"

import {
  appendAssistantRecord,
  loadAssistantHistory,
} from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type { AssistantMessage, AssistantRecord } from "@/types/api"

import { buildAssistantContext, runAssistantTurn } from "./assistantLoop"

const HISTORY_PAGE_SIZE = 10

/** How long a turn spent reasoning, and what it said while doing it. */
export interface TurnReasoning {
  text: string
  seconds: number
}

/** Identifies one journaled record, for the maps keyed on them below. */
export const recordKey = (record: AssistantRecord): string =>
  `${record.sessionId}-${record.seq}`

export interface AssistantSessionState {
  /** Every record in the scroll, oldest first, across all sessions. */
  records: AssistantRecord[]
  /** The reply currently streaming in, if any. */
  streamingText: string | null
  /** The reasoning for the step in progress. Shown, never stored. */
  streamingReasoning: string | null
  /**
   * A finished turn's reasoning and cost, keyed by the reply they belong to.
   * Neither is journaled, so replies loaded from history carry neither.
   */
  reasoningByRecord: Record<string, TurnReasoning>
  creditsByRecord: Record<string, number>
  /** Credits the assistant has spent since the window opened. */
  creditsUsed: number
  isRunning: boolean
  error: string | null
  hasMoreHistory: boolean
  isLoadingHistory: boolean
  canSend: boolean
  send: (text: string) => void
  loadOlder: () => void
  dismissError: () => void
}

/**
 * Owns one assistant conversation: session identity, the transcript, and the
 * running turn. The journal in the plugin is the record — this holds the live
 * view of it.
 */
export const useAssistantSession = (
  model: string,
  reasoningLevel: string,
  showReasoning: boolean,
): AssistantSessionState => {
  const state = useAppStore((store) => store.state)
  const activeTarget = useAppStore((store) => store.activeTarget)

  const [records, setRecords] = useState<AssistantRecord[]>([])
  const [streamingText, setStreamingText] = useState<string | null>(null)
  const [streamingReasoning, setStreamingReasoning] = useState<string | null>(
    null,
  )
  const [reasoningByRecord, setReasoningByRecord] = useState<
    Record<string, TurnReasoning>
  >({})
  const [creditsByRecord, setCreditsByRecord] = useState<
    Record<string, number>
  >({})
  const [creditsUsed, setCreditsUsed] = useState(0)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cursor, setCursor] = useState<number | null>(null)
  const [hasMoreHistory, setHasMoreHistory] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)

  // A session is one target encounter. The plugin-minted handle distinguishes
  // repeat reviews and individual editor buffers without webapp mode routing.
  const sessionRef = useRef<{ id: string; targetKey: string } | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    let cancelled = false

    const hydrate = async () => {
      setIsLoadingHistory(true)
      try {
        const page = await loadAssistantHistory({
          limit: HISTORY_PAGE_SIZE,
          cursor: null,
        })
        if (cancelled) return

        setRecords(page.records)
        setCursor(page.nextCursor)
        setHasMoreHistory(page.nextCursor !== null)
      } catch {
        // An empty journal is the common case on a fresh Anki session; a
        // failure here should not block the user from starting a chat.
      } finally {
        if (!cancelled) setIsLoadingHistory(false)
      }
    }

    void hydrate()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(
    () => () => {
      abortRef.current?.abort()
    },
    [],
  )

  const loadOlder = useCallback(() => {
    if (cursor === null || isLoadingHistory) return

    const load = async () => {
      setIsLoadingHistory(true)
      try {
        const page = await loadAssistantHistory({
          limit: HISTORY_PAGE_SIZE,
          cursor,
        })
        setRecords((current) => [...page.records, ...current])
        setCursor(page.nextCursor)
        setHasMoreHistory(page.nextCursor !== null)
      } catch (e) {
        setError(errorMessage(e))
      } finally {
        setIsLoadingHistory(false)
      }
    }

    void load()
  }, [cursor, isLoadingHistory])

  const authToken = state?.account.authToken ?? null
  const canSend = !isRunning && authToken !== null

  const send = useCallback(
    (text: string) => {
      const trimmed = text.trim()
      if (trimmed.length === 0 || isRunning || authToken === null) return

      const target = activeTarget
      const targetKey = JSON.stringify(target?.handle ?? null)
      if (
        sessionRef.current === null ||
        sessionRef.current.targetKey !== targetKey
      ) {
        sessionRef.current = { id: crypto.randomUUID(), targetKey }
      }
      const session = sessionRef.current
      const cardId =
        target?.handle.mode === "review" ? target.handle.cardId : null

      // Journal write-through: every finalized message is appended as it is
      // produced, so the transcript survives closing the window mid-turn.
      const journal = async (message: AssistantMessage) => {
        const stored = await appendAssistantRecord({
          sessionId: session.id,
          cardId,
          deckId: target?.deckId ?? null,
          noteTypeId: target?.noteTypeId ?? null,
          message,
        })
        setRecords((current) => [...current, stored])
        return stored
      }

      // A turn's reasoning and cost belong to the reply it produced, but the
      // journal stores neither, so they are held here and re-pointed at the
      // turn's latest reply as it lands.
      let reasoningText = ""
      let reasoningStartedAt: number | null = null
      let turnCredits = 0
      let attachedKey: string | null = null

      const attachTo = (key: string) => {
        const seconds =
          reasoningStartedAt === null
            ? 0
            : Math.round((Date.now() - reasoningStartedAt) / 1000)

        setReasoningByRecord((current) =>
          withKeyMoved(
            current,
            attachedKey,
            key,
            reasoningText.length > 0 ? { text: reasoningText, seconds } : null,
          ),
        )
        setCreditsByRecord((current) =>
          withKeyMoved(
            current,
            attachedKey,
            key,
            turnCredits > 0 ? Math.round(turnCredits) : null,
          ),
        )
        attachedKey = key
      }

      const run = async () => {
        setIsRunning(true)
        setError(null)
        const controller = new AbortController()
        abortRef.current = controller

        try {
          const userMessage: AssistantMessage = {
            role: "user",
            content: trimmed,
          }
          await journal(userMessage)

          // Model context is this session only: earlier sessions render in the
          // scroll but are never sent.
          const sessionMessages = records
            .filter((record) => record.sessionId === session.id)
            .map((record) => record.message)

          await runAssistantTurn({
            authToken,
            model,
            reasoningLevel,
            responseLanguage:
              state?.assistantSettings.responseLanguage ?? "auto",
            showReasoning,
            messages: [...sessionMessages, userMessage],
            context: buildAssistantContext(target, state),
            target,
            state,
            signal: controller.signal,
            onDelta: setStreamingText,
            onReasoningDelta: (text) => {
              reasoningStartedAt ??= Date.now()
              reasoningText = text
              setStreamingReasoning(text)
            },
            onMessage: (message) => {
              setStreamingText(null)
              setStreamingReasoning(null)
              void journal(message).then((stored) => {
                if ("role" in message && message.role === "assistant")
                  attachTo(recordKey(stored))
              })
            },
            onUsage: (turn) => {
              turnCredits += turn.credits
              setCreditsUsed((total) => total + turn.credits)
            },
          })
        } catch (e) {
          if (!controller.signal.aborted) setError(errorMessage(e))
        } finally {
          setStreamingText(null)
          setStreamingReasoning(null)
          setIsRunning(false)
          abortRef.current = null
        }
      }

      void run()
    },
    [
      authToken,
      isRunning,
      model,
      reasoningLevel,
      records,
      activeTarget,
      showReasoning,
      state,
    ],
  )

  return {
    records,
    streamingText,
    streamingReasoning,
    reasoningByRecord,
    creditsByRecord,
    creditsUsed,
    isRunning,
    error,
    hasMoreHistory,
    isLoadingHistory,
    canSend,
    send,
    loadOlder,
    dismissError: () => setError(null),
  }
}

/** Re-points a turn's value at its newest reply, dropping the older entry. */
const withKeyMoved = <T>(
  entries: Record<string, T>,
  from: string | null,
  to: string,
  value: T | null,
): Record<string, T> => {
  const next = { ...entries }
  if (from !== null) delete next[from]
  if (value !== null) next[to] = value
  return next
}

const errorMessage = (error: unknown): string =>
  error instanceof Error ? error.message : String(error)
