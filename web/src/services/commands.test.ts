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

import { describe, expect, test } from "bun:test"

import type { CommandName, SmartField } from "@/types/api"

const field: SmartField = {
  id: "existing-smart-field-id",
  noteTypeId: 10,
  deckId: 1,
  targetFieldName: "Meaning",
  fieldType: "chat",
  enabled: true,
  settings: {
    promptText: "Translate {{Front}}",
    provider: "auto",
    model: "auto",
    reasoningLevel: "off",
    webSearchEnabled: false,
    usesDefaultGenerationSettings: true,
  },
}

if (!("window" in globalThis)) {
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: { location: { search: "" } },
  })
}

describe("Smart Field commands", () => {
  test("requests an account refresh", async () => {
    const { refreshAccount, setCommandSender } = await import("./commands")
    const sentCommands: { command: CommandName; payload: object }[] = []
    setCommandSender(
      async <Result = void>(command: CommandName, payload: object) => {
        sentCommands.push({ command, payload })
        return undefined as Result
      },
    )

    await refreshAccount()

    expect(sentCommands).toEqual([{ command: "account.refresh", payload: {} }])
  })

  test("updates enabled state with the existing UUID", async () => {
    const { setCommandSender, setSmartFieldEnabled } =
      await import("./commands")
    const sentCommands: { command: CommandName; payload: object }[] = []
    setCommandSender(
      async <Result = void>(command: CommandName, payload: object) => {
        sentCommands.push({ command, payload })
        return undefined as Result
      },
    )

    await setSmartFieldEnabled(field, false)

    expect(sentCommands).toEqual([
      {
        command: "smartFields.update",
        payload: { ...field, enabled: false },
      },
    ])
  })

  test("deletes the existing UUID without mutable field coordinates", async () => {
    const { deleteSmartField, setCommandSender } = await import("./commands")
    const sentCommands: { command: CommandName; payload: object }[] = []
    setCommandSender(
      async <Result = void>(command: CommandName, payload: object) => {
        sentCommands.push({ command, payload })
        return undefined as Result
      },
    )

    await deleteSmartField(field)

    expect(sentCommands).toEqual([
      {
        command: "smartFields.delete",
        payload: { id: field.id },
      },
    ])
  })
})
