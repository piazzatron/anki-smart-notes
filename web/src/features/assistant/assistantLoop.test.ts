import { afterEach, describe, expect, mock, test } from "bun:test"

import type {
  AppState,
  AssistantActiveTarget,
  AssistantMessage,
  AssistantTurnUsage,
} from "@/types/api"

// `commands` reads boot options from the URL at import time.
if (!("window" in globalThis)) {
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: { location: { search: "" } },
  })
}

const { setCommandSender } = await import("@/services/commands")
const { runAssistantTurn } = await import("./assistantLoop")

const TARGET: AssistantActiveTarget = {
  handle: { mode: "review", cardId: 42 },
  noteTypeId: 1,
  noteTypeName: "Basic",
  deckId: 2,
  deckName: "Biology",
  fieldNames: ["Front", "Back"],
  firstFieldName: "Front",
  firstFieldValue: "mitochondria",
}

const STATE: Pick<AppState, "noteTypes" | "decks" | "globalDeckId"> = {
  noteTypes: [{ id: 1, name: "Basic", fields: ["Front", "Back"] }],
  decks: [
    { id: 0, name: "All Decks" },
    { id: 2, name: "Biology" },
  ],
  globalDeckId: 0,
}

const sseResponse = (frames: string[]): Response =>
  new Response(
    new ReadableStream({
      start(controller) {
        // Split across chunks so the parser's partial-frame buffering is exercised.
        const body = frames.join("")
        const middle = Math.floor(body.length / 2)
        controller.enqueue(new TextEncoder().encode(body.slice(0, middle)))
        controller.enqueue(new TextEncoder().encode(body.slice(middle)))
        controller.close()
      },
    }),
    { status: 200 },
  )

const frame = (event: string, data: unknown) =>
  `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`

const runTurn = async (
  messages: AssistantMessage[] = [],
  showReasoning = false,
) => {
  const produced: AssistantMessage[] = []
  const deltas: string[] = []
  const reasoning: string[] = []
  const usage: AssistantTurnUsage[] = []

  await runAssistantTurn({
    authToken: "jwt",
    model: "auto",
    reasoningLevel: showReasoning ? "high" : "off",
    responseLanguage: "auto",
    showReasoning,
    messages: [...messages, { role: "user", content: "what is this?" }],
    context: null,
    target: TARGET,
    state: STATE,
    signal: new AbortController().signal,
    onDelta: (text) => deltas.push(text),
    onReasoningDelta: (text) => reasoning.push(text),
    onMessage: (message) => produced.push(message),
    onUsage: (turn) => usage.push(turn),
  })

  return { produced, deltas, reasoning, usage }
}

afterEach(() => {
  setCommandSender(async () => undefined as never)
})

describe("runAssistantTurn", () => {
  test("executes a tool call locally and calls back with the result", async () => {
    const requests: unknown[] = []
    global.fetch = mock(async (_url: string, init: RequestInit) => {
      requests.push(JSON.parse(init.body as string))
      return requests.length === 1
        ? sseResponse([
            frame("tool_call", {
              callId: "call_1",
              name: "get_field",
              arguments: '{"fieldName":"Back"}',
            }),
            frame("done", { inputTokens: 10, outputTokens: 5 }),
          ])
        : sseResponse([
            frame("delta", { text: "The powerhouse " }),
            frame("delta", { text: "of the cell." }),
            frame("done", { inputTokens: 20, outputTokens: 8 }),
          ])
    }) as unknown as typeof fetch

    setCommandSender(async (command, payload) => {
      expect(command).toBe("assistant.getField")
      expect(payload).toEqual({
        target: { mode: "review", cardId: 42 },
        fieldName: "Back",
      })
      return { value: "The powerhouse of the cell" } as never
    })

    const { produced, deltas } = await runTurn()

    expect(produced).toEqual([
      {
        type: "function_call",
        name: "get_field",
        arguments: '{"fieldName":"Back"}',
        call_id: "call_1",
      },
      {
        type: "function_call_output",
        call_id: "call_1",
        output: "The powerhouse of the cell",
      },
      { role: "assistant", content: "The powerhouse of the cell." },
    ])
    expect(deltas.at(-1)).toBe("The powerhouse of the cell.")

    // The second call resends the whole conversation, tool result included.
    expect(requests).toHaveLength(2)
    const second = requests[1] as { messages: AssistantMessage[] }
    expect(second.messages).toHaveLength(3)
  })

  test("feeds a failed tool call back to the model instead of throwing", async () => {
    let calls = 0
    global.fetch = mock(async () => {
      calls++
      return calls === 1
        ? sseResponse([
            frame("tool_call", {
              callId: "call_1",
              name: "get_field",
              arguments: '{"fieldName":"Nope"}',
            }),
            frame("done", { inputTokens: 1, outputTokens: 1 }),
          ])
        : sseResponse([
            frame("delta", { text: "That field does not exist." }),
            frame("done", { inputTokens: 2, outputTokens: 2 }),
          ])
    }) as unknown as typeof fetch

    setCommandSender(async () => {
      throw new Error("Unknown field: Nope. Valid fields: Front, Back")
    })

    const { produced } = await runTurn()

    expect(produced[1]).toEqual({
      type: "function_call_output",
      call_id: "call_1",
      output: "Error: Unknown field: Nope. Valid fields: Front, Back",
    })
    expect(produced.at(-1)).toEqual({
      role: "assistant",
      content: "That field does not exist.",
    })
  })

  test("updates the captured target and returns the previous value to the model", async () => {
    let calls = 0
    global.fetch = mock(async () => {
      calls++
      return calls === 1
        ? sseResponse([
            frame("tool_call", {
              callId: "call_1",
              name: "update_field",
              arguments: '{"fieldName":"Back","newValue":"New answer"}',
            }),
            frame("done", { inputTokens: 1, outputTokens: 1 }),
          ])
        : sseResponse([
            frame("delta", { text: "Updated." }),
            frame("done", { inputTokens: 2, outputTokens: 2 }),
          ])
    }) as unknown as typeof fetch

    setCommandSender(async (command, payload) => {
      expect(command).toBe("assistant.updateField")
      expect(payload).toEqual({
        target: TARGET.handle,
        fieldName: "Back",
        newValue: "New answer",
      })
      return {
        status: "updated",
        fieldName: "Back",
        previousValue: "Old answer",
        value: "New answer",
      } as never
    })

    const { produced } = await runTurn()
    expect(JSON.parse((produced[1] as { output: string }).output)).toEqual({
      status: "updated",
      fieldName: "Back",
      previousValue: "Old answer",
      value: "New answer",
    })
  })

  test("resolves an omitted create-note type from the captured target", async () => {
    let calls = 0
    global.fetch = mock(async () => {
      calls++
      return calls === 1
        ? sseResponse([
            frame("tool_call", {
              callId: "call_1",
              name: "create_note",
              arguments: '{"deck":"Biology","fields":{"Front":"Cell"}}',
            }),
            frame("done", { inputTokens: 1, outputTokens: 1 }),
          ])
        : sseResponse([
            frame("delta", { text: "Created." }),
            frame("done", { inputTokens: 2, outputTokens: 2 }),
          ])
    }) as unknown as typeof fetch

    setCommandSender(async (command, payload) => {
      expect(command).toBe("assistant.addNote")
      expect(payload).toEqual({
        deck: "Biology",
        fields: { Front: "Cell" },
        noteType: "Basic",
      })
      return { noteId: 10, cardIds: [20], cardCount: 1 } as never
    })

    const { produced } = await runTurn()
    expect(JSON.parse((produced[1] as { output: string }).output)).toEqual({
      noteId: 10,
      cardIds: [20],
      cardCount: 1,
    })
  })

  test("stops after twelve tool rounds", async () => {
    let calls = 0
    global.fetch = mock(async () => {
      calls++
      return sseResponse([
        frame("tool_call", {
          callId: `call_${calls}`,
          name: "unknown",
          arguments: "{}",
        }),
        frame("done", { inputTokens: 1, outputTokens: 1 }),
      ])
    }) as unknown as typeof fetch

    await expect(runTurn()).rejects.toThrow("more than 12 rounds")
    expect(calls).toBe(12)
  })

  test("accumulates streamed reasoning and reports usage per model call", async () => {
    const requests: unknown[] = []
    global.fetch = mock(async (_url: string, init: RequestInit) => {
      requests.push(JSON.parse(init.body as string))
      return sseResponse([
        frame("reasoning", { text: "The card asks " }),
        frame("reasoning", { text: "about cells." }),
        frame("delta", { text: "Mitochondria." }),
        frame("done", {
          inputTokens: 30,
          outputTokens: 9,
          reasoningTokens: 4,
          credits: 1.25,
        }),
      ])
    }) as unknown as typeof fetch

    const { reasoning, usage } = await runTurn([], true)

    expect(
      (requests[0] as { stream_reasoning: boolean }).stream_reasoning,
    ).toBe(true)
    expect(reasoning.at(-1)).toBe("The card asks about cells.")
    expect(usage).toEqual([
      { inputTokens: 30, outputTokens: 9, reasoningTokens: 4, credits: 1.25 },
    ])
  })

  test("surfaces a mid-stream error event as a thrown error", async () => {
    global.fetch = mock(async () =>
      sseResponse([frame("error", { error: "Out of tokens" })]),
    ) as unknown as typeof fetch

    await expect(runTurn()).rejects.toThrow("Out of tokens")
  })
})
