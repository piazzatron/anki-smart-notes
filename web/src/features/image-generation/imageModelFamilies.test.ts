import { describe, expect, test } from "bun:test"

import {
  IMAGE_MODEL_FAMILIES,
  familyModel,
  getImageModelFamily,
  imageModelChoices,
  isSwitchOn,
} from "./imageModelFamilies"

describe("image model families", () => {
  test("every variant round-trips through its switch states", () => {
    for (const family of IMAGE_MODEL_FAMILIES) {
      for (const model of Object.keys(family.variants)) {
        const states = Object.fromEntries(
          family.switches.map((key) => [key, isSwitchOn(family, model, key)]),
        )
        expect(familyModel(family, states)).toBe(model)
      }
    }
  })

  test("all switches off picks the family default", () => {
    const nanoBanana = getImageModelFamily("nano-banana-2")!
    expect(familyModel(nanoBanana, {})).toBe("nano-banana-2-lite")
  })

  test("models outside a family have none", () => {
    expect(getImageModelFamily("z-image-turbo")).toBeNull()
  })

  test("collapses each family into one picker choice in catalog order", () => {
    const choices = imageModelChoices([
      { id: "gpt-image-2.5-flare-low", provider: "openai" },
      { id: "gpt-image-2.5-sunburst-medium", provider: "openai" },
      { id: "nano-banana-2-lite", provider: "google" },
      { id: "nano-banana-2", provider: "google" },
      { id: "z-image-turbo", provider: "replicate" },
    ])

    expect(choices.map((choice) => choice.id)).toEqual([
      "gpt-image-2.5",
      "nano-banana",
      "z-image-turbo",
    ])
  })
})
