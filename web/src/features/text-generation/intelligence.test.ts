import { describe, expect, test } from "bun:test"

import {
  INTELLIGENCE_LEVELS,
  autoSettingsFor,
  intelligenceLevelOf,
} from "./intelligence"

describe("Auto intelligence levels", () => {
  test("every level round-trips through the settings the server reads", () => {
    for (const { id } of INTELLIGENCE_LEVELS) {
      expect(intelligenceLevelOf(autoSettingsFor(id))).toBe(id)
    }
  })

  test("saved settings from before the levels land on the level the server runs", () => {
    expect(intelligenceLevelOf({ model: "auto", reasoningLevel: "low" })).toBe(
      "standard",
    )
    expect(
      intelligenceLevelOf({ model: "auto-max", reasoningLevel: "high" }),
    ).toBe("max")
  })
})
