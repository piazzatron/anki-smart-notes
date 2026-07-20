import type { SmartField } from "@/features/smart-fields/types"

type CommandName = "smartFields.save" | "smartFields.delete" | "defaults.save"

interface CommandResponse {
  ok: boolean
  error?: string
}

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
  })
}

const sendCommand = async (
  command: CommandName,
  payload: Record<string, unknown>,
): Promise<void> => {
  if (isMockMode) {
    const { handleMockCommand } = await import("@/dev/mockData")
    handleMockCommand(command, payload)
    return
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
}
