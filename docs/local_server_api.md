# Dev Server API Reference

Local HTTP server for programmatic Smart Notes operations. Runs automatically in DEV mode.

**Endpoint:** `POST http://127.0.0.1:8766/`

All requests use action-based routing:

```json
{"action": "actionName", "version": 1, "params": {...}}
```

Responses:

```json
{"result": <value>, "error": null}
{"result": null, "error": "description"}
```

## Actions

### ping

Health check.

**Params:** none
**Result:** `"pong"`

```bash
curl -X POST http://localhost:8766 -d '{"action": "ping", "version": 1}'
```

### getSmartFields

List all smart fields configured for a note type.

**Params:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `noteType` | string | yes | | Anki note type name |
| `deckId` | int | no | global (1) | Deck ID to scope fields to |

**Result:** `{ "<fieldName>": { "prompt": string, "extras": FieldExtras } }`

### addSmartField

Create a new smart field. Errors if the field already exists for the given noteType + deckId.

**Params:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `noteType` | string | yes | | Anki note type name |
| `field` | string | yes | | Field name to configure |
| `prompt` | string | yes | | Prompt template. Use `{{FieldName}}` to reference other fields |
| `type` | string | no | `"chat"` | One of: `"chat"`, `"tts"`, `"image"` |
| `deckId` | int | no | global (1) | Deck ID |
| `automatic` | bool | no | `true` | Generate automatically or require manual trigger |
| `useCustomModel` | bool | no | `false` | Override global model settings |
| `chatOptions` | object | no | | Chat-specific overrides (see below) |
| `ttsOptions` | object | no | | TTS-specific overrides (see below) |
| `imageOptions` | object | no | | Image-specific overrides (see below) |

**chatOptions:**
| Field | Type | Description |
|-------|------|-------------|
| `provider` | string | `"openai"`, `"anthropic"`, or `"deepseek"` |
| `model` | string | Model ID (e.g. `"gpt-5"`, `"claude-sonnet-4-6"`) |
| `temperature` | int | Temperature value |
| `markdownToHtml` | bool | Convert markdown response to HTML |
| `webSearch` | bool | Enable web search |

**ttsOptions:**
| Field | Type | Description |
|-------|------|-------------|
| `provider` | string | `"openai"`, `"elevenLabs"`, `"google"`, or `"azure"` |
| `model` | string | TTS model ID |
| `voice` | string | Voice name |
| `stripHtml` | bool | Strip HTML from input before TTS |

**imageOptions:**
| Field | Type | Description |
|-------|------|-------------|
| `provider` | string | `"replicate"`, `"google"`, or `"openai"` |
| `model` | string | Image model ID |

**Result:** `true`

### updateSmartField

Update an existing smart field. Errors if the field doesn't exist. Same params as `addSmartField`.

**Result:** `true`

### removeSmartField

Delete a smart field.

**Params:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `noteType` | string | yes | | Anki note type name |
| `field` | string | yes | | Field name to remove |
| `deckId` | int | no | global (1) | Deck ID |

**Result:** `true`

### generateNote

Generate smart fields for a single note.

**Params:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `noteId` | int | yes | | Anki note ID |
| `deckId` | int | no | inferred from note's cards | Deck ID |
| `overwrite` | bool | no | `false` | Overwrite existing field values |
| `targetField` | string | no | | Generate only this specific field (and its dependencies) |

**Result:**
```json
{
  "updated": true,
  "fields": { "<fieldName>": "<generatedValue>" }
}
```

`fields` contains only the fields that changed.

### generateNotes

Batch-generate smart fields for multiple notes.

**Params:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `noteIds` | int[] | yes | | List of Anki note IDs |
| `deckId` | int | no | inferred per note | Deck ID (applied to all notes) |
| `overwrite` | bool | no | `false` | Overwrite existing field values |

**Result:**
```json
{
  "updated": [noteId, ...],
  "failed": [noteId, ...],
  "skipped": [noteId, ...]
}
```

## UI Actions

These actions open Qt dialogs programmatically. The request blocks until the dialog is closed.

### uiEditSmartField

Open the prompt dialog in edit mode for an existing smart field.

**Params:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `noteType` | string | yes | | Anki note type name |
| `field` | string | yes | | Field name to edit |
| `deckId` | int | no | global (1) | Deck ID |

**Result:** `true` if the user clicked OK, `false` if cancelled.

### uiNewSmartField

Open the prompt dialog in new mode to create a smart field.

**Params:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `fieldType` | string | yes | | One of: `"chat"`, `"tts"`, `"image"` |
| `deckId` | int | no | global (1) | Deck ID |

**Result:** `true` if the user clicked OK, `false` if cancelled.

## Notes

- Use Anki Connect (port 8765) for standard Anki operations like `findNotes`, `notesInfo`, `modelNames`, `deckNames`, etc.
- Smart fields are scoped to noteType + deckId. The global deck (ID 1) serves as a fallback.
- The `{{FieldName}}` syntax in prompts references other fields on the same note. Fields are resolved in dependency order via a DAG.
- Type definitions for params and responses are in `src/local_server.py`.
- The local server is also used for the `/auth/callback` browser-based sign-in handoff. If port 8766 fails to bind (e.g. two Anki profiles running at once), the plugin logs the error and the user falls back to the auth code copy-paste flow.
