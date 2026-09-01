import type {
  AssistantActiveTarget,
  AssistantMessage,
  AssistantTurnUsage,
  AppState,
} from "@/types/api"

import {
  addAssistantNote,
  getAssistantField,
  updateAssistantField,
} from "@/services/commands"

/** Model-visible tools. Target routing stays entirely in the plugin. */
export const ASSISTANT_TOOLS = [
  {
    type: "function" as const,
    name: "get_field",
    description:
      "Read a field from the active reviewer note or editor buffer. Use this instead of guessing at field contents.",
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
  {
    type: "function" as const,
    name: "update_field",
    description:
      "Immediately update a field on the active target. Reviewer changes are saved to the collection. Add/edit changes fill the editor buffer and remain unsaved until the user saves or adds the note.",
    parameters: {
      type: "object",
      properties: {
        fieldName: {
          type: "string",
          description: "The exact name of the field to update.",
        },
        newValue: {
          type: "string",
          description: "The complete new HTML value for the field.",
        },
      },
      required: ["fieldName", "newValue"],
      additionalProperties: false,
    },
  },
  {
    type: "function" as const,
    name: "create_note",
    description:
      "Create a new Anki note directly in the collection. Always confirm the destination deck with the user before calling. Omit noteType only when an active target supplies it.",
    parameters: {
      type: "object",
      properties: {
        noteType: {
          type: "string",
          description:
            "Exact note type name. Optional only with an active target.",
        },
        deck: {
          type: "string",
          description: "Exact destination deck name confirmed by the user.",
        },
        fields: {
          type: "object",
          description: "Field names mapped to their complete HTML values.",
          additionalProperties: { type: "string" },
        },
        tags: {
          type: "array",
          items: { type: "string" },
        },
      },
      required: ["deck", "fields"],
      additionalProperties: false,
    },
  },
  {
    type: "function" as const,
    name: "list_note_types",
    description: "List available note types and their field schemas.",
    parameters: {
      type: "object",
      properties: {},
      additionalProperties: false,
    },
  },
  {
    type: "function" as const,
    name: "list_decks",
    description: "List valid destination decks for create_note.",
    parameters: {
      type: "object",
      properties: {},
      additionalProperties: false,
    },
  },
]

export interface AssistantContext {
  mode: "review" | "add" | "edit"
  noteType: string
  deck: string
  fieldNames: string[]
  firstFieldName: string
  firstFieldValue: string
}

type AssistantState = Pick<AppState, "noteTypes" | "decks" | "globalDeckId">

interface RunAssistantTurnArgs {
  authToken: string
  model: string
  reasoningLevel: string
  /** Language code the reply must be in, or "auto" to match the user. */
  responseLanguage: string
  /** Ask the backend to forward the model's reasoning text. */
  showReasoning: boolean
  messages: AssistantMessage[]
  context: AssistantContext | null
  target: AssistantActiveTarget | null
  state: AssistantState | null
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
  responseLanguage,
  showReasoning,
  messages,
  context,
  target,
  state,
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
        response_language: responseLanguage,
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
        output: await executeTool(call, target, state),
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
  target: AssistantActiveTarget | null,
  state: AssistantState | null,
): AssistantContext | null => {
  if (target === null || state === null) return null

  return {
    mode: target.handle.mode,
    noteType: target.noteTypeName,
    deck: target.deckName ?? "Unknown",
    fieldNames: target.fieldNames,
    firstFieldName: target.firstFieldName,
    firstFieldValue: target.firstFieldValue,
  }
}

const SERVER_URL = import.meta.env.DEV
  ? "http://localhost:3003"
  : "https://api.smart-notes.xyz"

const MAX_TOOL_STEPS = 12

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
  target: AssistantActiveTarget | null,
  state: AssistantState | null,
): Promise<string> => {
  // Tool failures are answers, not exceptions: the model should see what went
  // wrong and correct itself rather than the whole turn collapsing.
  try {
    if (call.name === "get_field") {
      const { fieldName } = JSON.parse(call.arguments) as { fieldName: string }
      const { value } = await getAssistantField({
        target: target?.handle ?? null,
        fieldName,
      })
      return value.length > 0 ? value : "(this field is empty)"
    }
    if (call.name === "update_field") {
      const args = JSON.parse(call.arguments) as {
        fieldName: string
        newValue: string
      }
      return JSON.stringify(
        await updateAssistantField({
          target: target?.handle ?? null,
          ...args,
        }),
      )
    }
    if (call.name === "create_note") {
      const args = JSON.parse(call.arguments) as {
        noteType?: string
        deck: string
        fields: Record<string, string>
        tags?: string[]
      }
      const noteType = args.noteType ?? targetNoteType(target)
      if (noteType === null) {
        return "Error: noteType is required when there is no active target."
      }
      return JSON.stringify(await addAssistantNote({ ...args, noteType }))
    }
    if (call.name === "list_note_types") {
      if (state === null) return "Error: Anki state is unavailable."
      return JSON.stringify(
        state.noteTypes.map(({ name, fields }) => ({ name, fields })),
      )
    }
    if (call.name === "list_decks") {
      if (state === null) return "Error: Anki state is unavailable."
      return JSON.stringify(
        state.decks
          .filter((deck) => deck.id !== state.globalDeckId)
          .map((deck) => deck.name),
      )
    }
    return `Error: unknown tool ${call.name}`
  } catch (error) {
    return `Error: ${error instanceof Error ? error.message : String(error)}`
  }
}

const targetNoteType = (
  target: AssistantActiveTarget | null,
): string | null => {
  return target?.noteTypeName ?? null
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
