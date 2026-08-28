import { FileText, Loader2, Upload, CheckCircle2 } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "./ui/alert"
import { Badge } from "./ui/badge"
import { Button } from "./ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/card"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import { Skeleton } from "./ui/skeleton"
import { Textarea } from "./ui/textarea"

interface IngestPhaseProps {
  resumeText: string
  jdText: string
  ruleNotes: string
  isLoading: boolean
  error: string | null
  onResumeTextChange: (value: string) => void
  onJdTextChange: (value: string) => void
  onRuleNotesChange: (value: string) => void
  onUpload: (file: File, target: "resume" | "jd") => Promise<void>
  onExtract: () => Promise<void>
}

function UploadControl({ target, disabled, onUpload }: { target: "resume" | "jd"; disabled: boolean; onUpload: (file: File, target: "resume" | "jd") => Promise<void> }) {
  const inputId = `${target}-upload`
  return (
    <>
      <Input
        id={inputId}
        aria-label={`Upload ${target === "resume" ? "resume" : "job description"} document`}
        type="file"
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        disabled={disabled}
        className="sr-only"
        onChange={(event) => {
          const file = event.currentTarget.files?.[0]
          if (file) void onUpload(file, target)
          event.currentTarget.value = ""
        }}
      />
      <Button variant="outline" size="sm" disabled={disabled} onClick={() => document.getElementById(inputId)?.click()}>
        <Upload className="size-3.5" aria-hidden="true" />
        Upload PDF/DOCX
      </Button>
    </>
  )
}

function DocumentCard({ title, value, target, disabled, onChange, onUpload }: { title: string; value: string; target: "resume" | "jd"; disabled: boolean; onChange: (value: string) => void; onUpload: (file: File, target: "resume" | "jd") => Promise<void> }) {
  const fieldId = target === "resume" ? "resume-text" : "jd-text"
  return (
    <div className="relative space-y-3 rounded-lg border border-dashed border-border bg-muted/5 p-4 transition-colors hover:border-primary/50">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Label htmlFor={fieldId} className="text-base font-medium">{title}</Label>
          {value.length > 0 && <Badge variant="success" className="h-5 px-1.5 text-[10px]"><CheckCircle2 className="mr-1 size-3" /> Loaded</Badge>}
        </div>
        <UploadControl target={target} disabled={disabled} onUpload={onUpload} />
      </div>
      <Textarea id={fieldId} value={value} onChange={(event) => onChange(event.target.value)} placeholder={`Paste the ${target === "resume" ? "resume" : "job description"} text here...`} rows={12} disabled={disabled} className="resize-y bg-background" />
    </div>
  )
}

export function IngestPhase({ resumeText, jdText, ruleNotes, isLoading, error, onResumeTextChange, onJdTextChange, onRuleNotesChange, onUpload, onExtract }: IngestPhaseProps) {
  return (
    <section className="space-y-6" aria-labelledby="ingest-title">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">Phase 01</p>
        <h1 id="ingest-title" className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">Ingest candidate materials</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">Load the source documents first. The extraction step proposes structured facts for a human reviewer to verify.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><FileText className="size-4 text-primary" aria-hidden="true" /> Source documents</CardTitle>
          <CardDescription>Upload a PDF or DOCX, or paste text directly. Files use the existing `/parse-document` endpoint.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-8">
          <div className="grid gap-6 lg:grid-cols-2">
            <DocumentCard title="Resume text" value={resumeText} target="resume" disabled={isLoading} onChange={onResumeTextChange} onUpload={onUpload} />
            <DocumentCard title="Job description text" value={jdText} target="jd" disabled={isLoading} onChange={onJdTextChange} onUpload={onUpload} />
          </div>
          <div className="space-y-3 rounded-lg border border-border bg-muted/5 p-4">
            <Label htmlFor="rule-notes" className="text-base font-medium">Mandatory rule notes <span className="font-normal text-muted-foreground text-sm">(optional)</span></Label>
            <Textarea id="rule-notes" value={ruleNotes} onChange={(event) => onRuleNotesChange(event.target.value)} placeholder="Example: Tableau must be at least 24 months. SQL is mandatory. Healthcare domain preferred." rows={3} disabled={isLoading} className="resize-y bg-background" />
            <p className="text-xs text-muted-foreground">Use this free-form input to define absolute requirements. The AI will convert these into strict boolean checks.</p>
          </div>
          {isLoading && (
            <div className="space-y-3 rounded-md border border-border bg-muted/30 p-4" aria-live="polite">
              <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                <Loader2 className="size-4 animate-spin text-primary" />
                Analyzing documents...
              </div>
              <Skeleton className="h-2 w-3/4" />
              <Skeleton className="h-2 w-1/2" />
            </div>
          )}
          {error && <Alert variant="destructive"><AlertTitle>Could not continue</AlertTitle><AlertDescription>{error}</AlertDescription></Alert>}
        </CardContent>
        <CardFooter className="justify-end border-t border-border pt-6">
          <Button type="button" size="lg" disabled={isLoading || !resumeText.trim() || !jdText.trim()} onClick={() => void onExtract()}>
            {isLoading ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : <FileText className="size-4" aria-hidden="true" />}
            Analyze & extract
          </Button>
        </CardFooter>
      </Card>
    </section>
  )
}
