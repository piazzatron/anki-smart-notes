import type {
  AssistantMessage,
  AssistantTurnUsage,
  ReviewerCard,
  AppState,
  NoteType,
  Deck,
} from "@/types/api"

import { getAssistantField } from "@/services/commands"

/** Tools the assistant can call. v0.1 ships one: reading a field off the card. */
export const ASSISTANT_TOOLS = [
  {
    type: "function" as const,
    name: "get_field",
    description:
      "Read the current value of a field on the card the user is reviewing. Use this instead of guessing at field contents.",
    parameters: {
      type: "object",
      properties: {
        fieldName: {
          type: "string",
          description: "The exact name of the field to read.",
        },
      },
      required: ["fieldName"],
      additionalProperties: false,
    },
  },
]

export interface AssistantContext {
  mode: "review"
  noteType: string
  deck: string
  fieldNames: string[]
  firstFieldName: string
  firstFieldValue: string
}

interface RunAssistantTurnArgs {
  authToken: string
  model: string
  reasoningLevel: string
  /** Ask the backend to forward the model's reasoning text. */
  showReasoning: boolean
  messages: AssistantMessage[]
  context: AssistantContext | null
  card: ReviewerCard | null
  signal: AbortSignal
  /** Streamed text for the reply in progress, re-sent on every token. */
  onDelta: (text: string) => void
  /** Streamed reasoning for the step in progress. Never journaled. */
  onReasoningDelta: (text: string) => void
  /** Every message the turn produced, in order, as each is finalized. */
  onMessage: (message: AssistantMessage) => void
  /** Token spend, once per model call — a turn with tools reports several. */
  onUsage: (usage: AssistantTurnUsage) => void
}

/**
 * Runs one user turn to completion: streams the model's reply, executes any
 * tool calls locally, and calls back until the model answers with text.
 *
 * The loop lives here rather than on the server so streaming is a single hop
 * and tools stay ordinary plugin commands.
 */
export const runAssistantTurn = async ({
  authToken,
  model,
  reasoningLevel,
  showReasoning,
  messages,
  context,
  card,
  signal,
  onDelta,
  onReasoningDelta,
  onMessage,
  onUsage,
}: RunAssistantTurnArgs): Promise<void> => {
  const conversation = [...messages]

  // Bounded so a model that loops on tool calls cannot spin forever.
  for (let step = 0; step < MAX_TOOL_STEPS; step++) {
    const response = await fetch(`${SERVER_URL}/api/assistant`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`,
        "x-sn-source": "anki-plugin",
      },
      body: JSON.stringify({
        model,
        reasoning_level: reasoningLevel,
        stream_reasoning: showReasoning,
        messages: conversation,
        tools: ASSISTANT_TOOLS,
        context,
      }),
      signal,
    })

    if (!response.ok || response.body === null) {
      throw new Error(await readErrorMessage(response))
    }

    let text = ""
    let reasoning = ""
    const toolCalls: ToolCallEvent[] = []

    for await (const event of readSSE(response.body, signal)) {
      if (event.name === "delta") {
        text += (event.data as { text: string }).text
        onDelta(text)
      } else if (event.name === "reasoning") {
        reasoning += (event.data as { text: string }).text
        onReasoningDelta(reasoning)
      } else if (event.name === "tool_call") {
        toolCalls.push(event.data as ToolCallEvent)
      } else if (event.name === "done") {
        onUsage(event.data as AssistantTurnUsage)
      } else if (event.name === "error") {
        throw new Error((event.data as { error: string }).error)
      }
    }

    // Any prose the model produced alongside its tool calls still belongs in
    // the transcript, so it is recorded before the calls it introduces.
    if (text.length > 0) {
      const message: AssistantMessage = { role: "assistant", content: text }
      conversation.push(message)
      onMessage(message)
    }

    if (toolCalls.length === 0) return

    for (const call of toolCalls) {
      const callMessage: AssistantMessage = {
        type: "function_call",
        name: call.name,
        arguments: call.arguments,
        call_id: call.callId,
      }
      conversation.push(callMessage)
      onMessage(callMessage)

      const outputMessage: AssistantMessage = {
        type: "function_call_output",
        call_id: call.callId,
        output: await executeTool(call, card),
      }
      conversation.push(outputMessage)
      onMessage(outputMessage)
    }
  }

  throw new Error(
    `The assistant made more than ${MAX_TOOL_STEPS} rounds of tool calls without answering.`,
  )
}

/** The card context block sent up front. Field values are fetched on demand. */
export const buildAssistantContext = (
  card: ReviewerCard | null,
  state: AppState | null,
): AssistantContext | null => {
  if (card === null || state === null) return null

  const noteType = state.noteTypes.find(
    (item: NoteType) => item.id === card.noteTypeId,
  )
  const deck = state.decks.find((item: Deck) => item.id === card.deckId)

  return {
    mode: "review",
    noteType: noteType?.name ?? "Unknown",
    deck: deck?.name ?? "Unknown",
    fieldNames: card.fieldNames,
    firstFieldName: card.firstFieldName,
    firstFieldValue: card.firstFieldValue,
  }
}

const SERVER_URL = import.meta.env.DEV
  ? "http://localhost:3003"
  : "https://api.smart-notes.xyz"

const MAX_TOOL_STEPS = 6

interface ToolCallEvent {
  callId: string
  name: string
  arguments: string
}

interface SSEEvent {
  name: string
  data: unknown
}

const executeTool = async (
  call: ToolCallEvent,
  card: ReviewerCard | null,
): Promise<string> => {
  // Tool failures are answers, not exceptions: the model should see what went
  // wrong and correct itself rather than the whole turn collapsing.
  try {
    if (call.name !== "get_field") {
      return `Error: unknown tool ${call.name}`
    }
    if (card === null) {
      return "Error: no card is being reviewed right now."
    }

    const { fieldName } = JSON.parse(call.arguments) as { fieldName: string }
    const { value } = await getAssistantField({
      cardId: card.cardId,
      fieldName,
    })
    return value.length > 0 ? value : "(this field is empty)"
  } catch (error) {
    return `Error: ${error instanceof Error ? error.message : String(error)}`
  }
}

/**
 * Parses an SSE body. EventSource cannot be used here because this is a POST
 * with an Authorization header.
 */
async function* readSSE(
  body: ReadableStream<Uint8Array>,
  signal: AbortSignal,
): AsyncGenerator<SSEEvent> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  try {
    while (!signal.aborted) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Frames are separated by a blank line; the last chunk may be partial.
      const frames = buffer.split("\n\n")
      buffer = frames.pop() ?? ""

      for (const frame of frames) {
        const event = parseFrame(frame)
        if (event !== null) yield event
      }
    }
  } finally {
    reader.releaseLock()
  }
}

const parseFrame = (frame: string): SSEEvent | null => {
  let name = "message"
  const dataLines: string[] = []

  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) name = line.slice(6).trim()
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim())
  }

  if (dataLines.length === 0) return null

  try {
    return { name, data: JSON.parse(dataLines.join("\n")) }
  } catch {
    return null
  }
}

const readErrorMessage = async (response: Response): Promise<string> => {
  try {
    const body = (await response.json()) as { error?: string }
    if (body.error !== undefined) return body.error
  } catch {
    // Fall through to the status line.
  }

  return `The assistant is unavailable (${response.status}).`
}
