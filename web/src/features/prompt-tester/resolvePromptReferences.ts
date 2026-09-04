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

/** Resolve prompt references once for validation and previews, matching generation's casing rules. */
export const resolvePromptReferences = (
  prompt: string,
  fields: Record<string, string>,
) => {
  const fieldsByLowerName = new Map(
    Object.entries(fields).map(([name, value]) => [
      name.toLowerCase(),
      { name, value },
    ]),
  )
  const parts: PromptPart[] = []
  const referencedFieldNames = new Set<string>()
  const missingFieldNames = new Set<string>()
  let previousEnd = 0
  let hasFieldReferences = false

  for (const match of prompt.matchAll(/\{\{([^{}]+)\}\}/g)) {
    hasFieldReferences = true
    if (match.index > previousEnd) {
      parts.push({
        text: prompt.slice(previousEnd, match.index),
        isReference: false,
      })
    }

    const field = fieldsByLowerName.get(match[1]!.toLowerCase())
    if (field === undefined) {
      missingFieldNames.add(match[1]!)
    } else {
      referencedFieldNames.add(field.name)
    }
    parts.push({ text: field?.value ?? match[0], isReference: true })
    previousEnd = match.index + match[0].length
  }
  if (previousEnd < prompt.length) {
    parts.push({ text: prompt.slice(previousEnd), isReference: false })
  }

  return {
    hasFieldReferences,
    missingFieldNames: [...missingFieldNames],
    parts,
    referencedFields: Object.entries(fields).filter(([name]) =>
      referencedFieldNames.has(name),
    ),
  }
}

interface PromptPart {
  text: string
  isReference: boolean
}
