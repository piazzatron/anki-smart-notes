import { describe, expect, test } from "bun:test"

import {
  MAX_SIDEBAR_WIDTH,
  MIN_SIDEBAR_WIDTH,
  resizeSidebar,
} from "./sidebarWidth"

describe("resizeSidebar", () => {
  test("follows the pointer toward the content edge in either direction", () => {
    expect(resizeSidebar(236, 40, "ltr")).toBe(276)
    expect(resizeSidebar(236, -40, "rtl")).toBe(276)
    expect(resizeSidebar(236, 40, "rtl")).toBe(196)
  })

  test("clamps to the supported range", () => {
    expect(resizeSidebar(236, 1000, "ltr")).toBe(MAX_SIDEBAR_WIDTH)
    expect(resizeSidebar(236, -1000, "ltr")).toBe(MIN_SIDEBAR_WIDTH)
  })
})
