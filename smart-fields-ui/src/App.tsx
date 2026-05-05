import { useCallback, useEffect, useMemo, useState } from "react"
import { Sparkles, Trash2, Plus, AlertCircle } from "lucide-react"
import { toast } from "sonner"
import { Toaster } from "@/components/ui/sonner"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { api, type SmartFieldInfo } from "@/lib/api"

function App() {
  const [connected, setConnected] = useState<boolean | null>(null)
  const [noteTypes, setNoteTypes] = useState<string[]>([])
  const [noteType, setNoteType] = useState<string>("")
  const [fields, setFields] = useState<string[]>([])
  const [field, setField] = useState<string>("")
  const [prompt, setPrompt] = useState<string>("")
  const [smartFields, setSmartFields] = useState<Record<string, SmartFieldInfo>>({})
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    api
      .ping()
      .then(() => setConnected(true))
      .catch(() => setConnected(false))
  }, [])

  useEffect(() => {
    if (!connected) return
    api
      .listNoteTypes()
      .then((types) => {
        setNoteTypes(types)
        if (types.length && !noteType) setNoteType(types[0])
      })
      .catch((e: Error) => toast.error(`Failed to load note types: ${e.message}`))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connected])

  const refreshForNoteType = useCallback(async (nt: string) => {
    if (!nt) return
    try {
      const [f, s] = await Promise.all([api.getFields(nt), api.getSmartFields(nt)])
      setFields(f)
      setSmartFields(s)
    } catch (e) {
      toast.error(`Failed to load fields: ${(e as Error).message}`)
    }
  }, [])

  useEffect(() => {
    refreshForNoteType(noteType)
  }, [noteType, refreshForNoteType])

  const availableFields = useMemo(
    () => fields.filter((f) => !(f in smartFields)),
    [fields, smartFields],
  )

  useEffect(() => {
    if (field && !availableFields.includes(field)) setField("")
  }, [availableFields, field])

  const canSubmit = noteType && field && prompt.trim().length > 0 && !submitting

  const onSubmit = async () => {
    if (!canSubmit) return
    setSubmitting(true)
    try {
      await api.addSmartField({ noteType, field, prompt: prompt.trim() })
      toast.success(`Added smart field "${field}" on ${noteType}`)
      setField("")
      setPrompt("")
      await refreshForNoteType(noteType)
    } catch (e) {
      toast.error((e as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  const onDelete = async (f: string) => {
    try {
      await api.removeSmartField({ noteType, field: f })
      toast.success(`Removed "${f}"`)
      await refreshForNoteType(noteType)
    } catch (e) {
      toast.error((e as Error).message)
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="mx-auto max-w-5xl px-6 py-5 flex items-center gap-3">
          <Sparkles className="size-5" />
          <h1 className="text-lg font-semibold tracking-tight">Smart Fields</h1>
          <div className="ml-auto text-xs text-muted-foreground">
            {connected === null && "Connecting…"}
            {connected === true && (
              <span className="inline-flex items-center gap-2">
                <span className="size-2 rounded-full bg-green-500" />
                Connected to Anki
              </span>
            )}
            {connected === false && (
              <span className="inline-flex items-center gap-2 text-destructive">
                <span className="size-2 rounded-full bg-destructive" />
                Not connected
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-10">
        {connected === false && (
          <Card className="mb-6 border-destructive/50">
            <CardContent className="flex items-start gap-3 pt-6">
              <AlertCircle className="size-5 text-destructive shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-foreground">
                  Can't reach the Anki local server.
                </p>
                <p className="text-muted-foreground">
                  Make sure Anki is running with Smart Notes enabled. Expected at{" "}
                  <code className="text-xs">http://127.0.0.1:8766</code>.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid gap-6 md:grid-cols-[1fr_1fr]">
          <Card>
            <CardHeader>
              <CardTitle>Add smart field</CardTitle>
              <CardDescription>
                Create a new AI-generated text field on a note type.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="note-type">Note type</Label>
                <Select
                  value={noteType}
                  onValueChange={setNoteType}
                  disabled={!connected || noteTypes.length === 0}
                >
                  <SelectTrigger id="note-type" className="w-full">
                    <SelectValue placeholder="Select a note type" />
                  </SelectTrigger>
                  <SelectContent>
                    {noteTypes.map((t) => (
                      <SelectItem key={t} value={t}>
                        {t}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="field">Target field</Label>
                <Select
                  value={field}
                  onValueChange={setField}
                  disabled={!noteType || availableFields.length === 0}
                >
                  <SelectTrigger id="field" className="w-full">
                    <SelectValue
                      placeholder={
                        availableFields.length === 0
                          ? "All fields are already smart"
                          : "Select a field"
                      }
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {availableFields.map((f) => (
                      <SelectItem key={f} value={f}>
                        {f}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="prompt">Prompt</Label>
                <Textarea
                  id="prompt"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Write a cloze deletion for {{Front}}"
                  rows={6}
                  className="resize-y"
                />
                <p className="text-xs text-muted-foreground">
                  Reference other fields on the note with <code>{"{{FieldName}}"}</code>.
                </p>
              </div>

              <Button
                onClick={onSubmit}
                disabled={!canSubmit}
                className="w-full"
                size="lg"
              >
                <Plus className="size-4" />
                {submitting ? "Adding…" : "Add smart field"}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Existing on {noteType || "…"}</CardTitle>
              <CardDescription>
                Smart fields already configured for this note type.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {Object.keys(smartFields).length === 0 ? (
                <p className="text-sm text-muted-foreground py-8 text-center">
                  No smart fields yet.
                </p>
              ) : (
                <ul className="divide-y">
                  {Object.entries(smartFields).map(([f, info]) => (
                    <li
                      key={f}
                      className="flex items-start gap-3 py-3 first:pt-0 last:pb-0"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="font-medium text-sm">{f}</div>
                        <div className="text-xs text-muted-foreground truncate">
                          {info.prompt}
                        </div>
                      </div>
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => onDelete(f)}
                        aria-label={`Remove ${f}`}
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      </main>

      <Toaster richColors position="bottom-right" />
    </div>
  )
}

export default App
