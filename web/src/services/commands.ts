import type {
  ChatDefaultsSavePayload,
  CommandName,
  CommandResponse,
  SmartField,
  SmartFieldDeletePayload,
  TextPromptTestArgs,
  TextPromptTestResult,
} from "@/types/api"

const sessionToken =
  new URLSearchParams(window.location.search).get("token") ?? ""
const isMockMode =
  import.meta.env.DEV &&
  new URLSearchParams(window.location.search).get("mock") === "1"

export const setSmartFieldEnabled = async (
  field: SmartField,
  enabled: boolean,
): Promise<void> => {
  await sendCommand("smartFields.save", {
    noteTypeId: field.noteTypeId,
    deckId: field.deckId,
    targetFieldName: field.targetFieldName,
    fieldType: field.fieldType,
    enabled,
    settings: field.settings,
  })
}

export const deleteSmartField = async (field: SmartField): Promise<void> => {
  await sendCommand("smartFields.delete", {
    noteTypeId: field.noteTypeId,
    deckId: field.deckId,
    targetFieldName: field.targetFieldName,
  } satisfies SmartFieldDeletePayload)
}

export const saveChatDefaults = async (
  defaults: ChatDefaultsSavePayload,
): Promise<void> => {
  await sendCommand("defaults.chat.save", defaults)
}

export const testTextPrompt = async (
  args: TextPromptTestArgs,
): Promise<TextPromptTestResult> =>
  sendCommand<TextPromptTestResult>("prompts.test", args)

const sendCommand = async <Result = void>(
  command: CommandName,
  payload: object,
): Promise<Result> => {
  if (isMockMode) {
    const { handleMockCommand } = await import("@/dev/mockData")
    return handleMockCommand(command, payload) as Result
  }

  const response = await fetch("/api/command", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Session-Token": sessionToken,
    },
    body: JSON.stringify({ command, payload }),
  })
  const result = (await response.json()) as CommandResponse

  if (!response.ok || !result.ok) {
    throw new Error(
      result.error ?? `Command failed with status ${response.status}`,
    )
  }

  return result.result as Result
}
