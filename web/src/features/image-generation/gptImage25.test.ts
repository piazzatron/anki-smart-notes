import { describe, expect, test } from "bun:test"

import {
  GPT_IMAGE_25,
  gptImage25Model,
  gptImage25Options,
  imageModelChoices,
} from "./gptImage25"

describe("GPT Image 2.5 options", () => {
  test("every switch combination round-trips through its wire model", () => {
    for (const richerDetail of [false, true]) {
      for (const highQuality of [false, true]) {
        const options = { richerDetail, highQuality }
        expect(gptImage25Options(gptImage25Model(options))).toEqual(options)
      }
    }
  })

  test("other image models have no GPT Image 2.5 options", () => {
    expect(gptImage25Options("z-image-turbo")).toBeNull()
  })

  test("collapses GPT Image 2.5 models into one picker choice in catalog order", () => {
    const choices = imageModelChoices([
      { id: "gpt-image-2.5-flare-low", provider: "openai" },
      { id: "gpt-image-2.5-sunburst-medium", provider: "openai" },
      { id: "nano-banana-2", provider: "google" },
      { id: "z-image-turbo", provider: "replicate" },
    ])

    expect(choices.map((choice) => choice.id)).toEqual([
      GPT_IMAGE_25,
      "nano-banana-2",
      "z-image-turbo",
    ])
  })
})
