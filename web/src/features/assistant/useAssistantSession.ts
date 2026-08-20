import { useCallback, useEffect, useRef, useState } from "react"

import {
  appendAssistantRecord,
  loadAssistantHistory,
} from "@/services/commands"
import { useAppStore } from "@/store/appStore"
import type {
  AssistantMessage,
  AssistantRecord,
  AssistantTurnUsage,
} from "@/types/api"

import { buildAssistantContext, runAssistantTurn } from "./assistantLoop"

const HISTORY_PAGE_SIZE = 10

/** Everything the assistant has spent since the window opened. */
export interface AssistantSessionUsage {
  inputTokens: number
  outputTokens: number
  reasoningTokens: number
  credits: number
}

const NO_USAGE: AssistantSessionUsage = {
  inputTokens: 0,
  outputTokens: 0,
  reasoningTokens: 0,
  credits: 0,
}

export interface AssistantSessionState {
  /** Every record in the scroll, oldest first, across all sessions. */
  records: AssistantRecord[]
  /** The reply currently streaming in, if any. */
  streamingText: string | null
  /** The reasoning for the step in progress. Shown, never stored. */
  streamingReasoning: string | null
  usage: AssistantSessionUsage
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
  const reviewerCard = useAppStore((store) => store.reviewerCard)

  const [records, setRecords] = useState<AssistantRecord[]>([])
  const [streamingText, setStreamingText] = useState<string | null>(null)
  const [streamingReasoning, setStreamingReasoning] = useState<string | null>(
    null,
  )
  const [usage, setUsage] = useState<AssistantSessionUsage>(NO_USAGE)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cursor, setCursor] = useState<number | null>(null)
  const [hasMoreHistory, setHasMoreHistory] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)

  // A session is one card encounter. The same card seen again starts a new one,
  // so the id is minted on first send after a card change, not derived from it.
  const sessionRef = useRef<{ id: string; cardId: number | null } | null>(null)
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

      const cardId = reviewerCard?.cardId ?? null
      if (sessionRef.current === null || sessionRef.current.cardId !== cardId) {
        sessionRef.current = { id: crypto.randomUUID(), cardId }
      }
      const session = sessionRef.current

      // Journal write-through: every finalized message is appended as it is
      // produced, so the transcript survives closing the window mid-turn.
      const journal = async (message: AssistantMessage) => {
        const stored = await appendAssistantRecord({
          sessionId: session.id,
          cardId,
          deckId: reviewerCard?.deckId ?? null,
          noteTypeId: reviewerCard?.noteTypeId ?? null,
          message,
        })
        setRecords((current) => [...current, stored])
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
            showReasoning,
            messages: [...sessionMessages, userMessage],
            context: buildAssistantContext(reviewerCard, state),
            card: reviewerCard,
            signal: controller.signal,
            onDelta: setStreamingText,
            onReasoningDelta: setStreamingReasoning,
            onMessage: (message) => {
              setStreamingText(null)
              setStreamingReasoning(null)
              void journal(message)
            },
            onUsage: (turn) => setUsage((total) => addUsage(total, turn)),
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
      reviewerCard,
      showReasoning,
      state,
    ],
  )

  return {
    records,
    streamingText,
    streamingReasoning,
    usage,
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

const addUsage = (
  total: AssistantSessionUsage,
  turn: AssistantTurnUsage,
): AssistantSessionUsage => ({
  inputTokens: total.inputTokens + turn.inputTokens,
  outputTokens: total.outputTokens + turn.outputTokens,
  reasoningTokens: total.reasoningTokens + (turn.reasoningTokens ?? 0),
  credits: total.credits + turn.credits,
})

const errorMessage = (error: unknown): string =>
  error instanceof Error ? error.message : String(error)
