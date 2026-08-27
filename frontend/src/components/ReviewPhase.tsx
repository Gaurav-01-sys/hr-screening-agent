import { ArrowLeft, ArrowRight, ClipboardCheck, Loader2 } from "lucide-react"
import { Badge } from "./ui/badge"
import { Button } from "./ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import { ScrollArea } from "./ui/scroll-area"
import { Select } from "./ui/select"
import { Skeleton } from "./ui/skeleton"
import { cn } from "../lib/utils"
import type { ExtractedField, ScreeningRequest, SkillExperience } from "../types"

interface ReviewPhaseProps {
  request: ScreeningRequest
  isLoading: boolean
  onSkillChange: (index: number, patch: Partial<SkillExperience>) => void
  onFieldChange: (index: number, patch: Partial<ExtractedField>) => void
  onBack: () => void
  onSubmit: () => Promise<void>
}

function statusVariant(status?: string): "secondary" | "success" | "destructive" | "warning" | "outline" {
  if (status === "approved") return "success"
  if (status === "rejected") return "destructive"
  if (status === "corrected") return "warning"
  return "secondary"
}

function evidenceText(field: { evidence?: Array<{ snippet?: string }> }): string {
  return field.evidence?.[0]?.snippet?.trim() || "No evidence captured"
}

export function ReviewPhase({ request, isLoading, onSkillChange, onFieldChange, onBack, onSubmit }: ReviewPhaseProps) {
  const skills = request.candidate.skills ?? []
  const fields = request.candidate.fields_for_review ?? []
  return (
    <section className="space-y-6" aria-labelledby="review-title">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">Phase 02</p>
        <div className="flex flex-wrap items-center gap-3">
          <h1 id="review-title" className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">Verify extracted facts</h1>
          <Badge variant="outline">Human review required</Badge>
        </div>
        <p className="mt-2 max-w-3xl text-sm text-muted-foreground">Correct the fields that affect screening. Evidence snippets stay read-only so every edit remains traceable.</p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><ClipboardCheck className="size-4 text-primary" aria-hidden="true" /> Skill evidence</CardTitle>
            <CardDescription>Skill names and months are editable. Evidence is preserved from extraction.</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? <TableSkeleton columns={3} /> : skills.length === 0 ? <EmptyTableState label="No skills extracted" /> : (
              <ScrollArea className="max-h-[430px] rounded-md border border-border">
                <table className="w-full min-w-[620px] text-left text-sm">
                  <thead className="sticky top-0 z-10 bg-card text-xs uppercase tracking-wide text-muted-foreground">
                    <tr><th className="px-4 py-3 font-medium">Skill</th><th className="w-28 px-4 py-3 font-medium">Months</th><th className="px-4 py-3 font-medium">Evidence snippet</th></tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {skills.map((skill, index) => <tr key={`${skill.skill}-${index}`} className="align-top">
                      <td className="px-4 py-3"><Label htmlFor={`skill-${index}`} className="sr-only">Skill {index + 1}</Label><Input id={`skill-${index}`} value={skill.skill} onChange={(event) => onSkillChange(index, { skill: event.target.value })} /></td>
                      <td className="px-4 py-3"><Label htmlFor={`months-${index}`} className="sr-only">Months for {skill.skill}</Label><Input id={`months-${index}`} type="number" min={0} step={1} value={skill.months} onChange={(event) => onSkillChange(index, { months: Math.max(0, Number.parseInt(event.target.value, 10) || 0) })} /></td>
                      <td className="max-w-md px-4 py-3 text-muted-foreground"><span title={evidenceText(skill)} className="line-clamp-2">{evidenceText(skill)}</span></td>
                    </tr>)}
                  </tbody>
                </table>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Candidate context</CardTitle>
            <CardDescription>Review the identity and role context used for this screening run.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
              <div className="space-y-2"><Label>Candidate</Label><p className="rounded-md border border-border bg-muted/20 px-3 py-2 text-sm text-foreground">{request.candidate.full_name || "Unnamed candidate"}</p></div>
              <div className="space-y-2"><Label>Role</Label><p className="rounded-md border border-border bg-muted/20 px-3 py-2 text-sm text-foreground">{request.job.role_title || "Untitled role"}</p></div>
              <div className="space-y-2"><Label htmlFor="total-experience">Total experience (months)</Label><Input id="total-experience" type="number" value={request.candidate.total_experience_months ?? 0} readOnly /></div>
              <div className="space-y-2"><Label>Mandatory skills</Label><p className="rounded-md border border-border bg-muted/20 px-3 py-2 text-sm text-muted-foreground">{request.job.mandatory_skills?.join(", ") || "None specified"}</p></div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Extracted fields</CardTitle>
          <CardDescription>Unknown fields from the backend are rendered here rather than discarded.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? <TableSkeleton columns={4} /> : fields.length === 0 ? <EmptyTableState label="No review fields" /> : (
            <ScrollArea className="max-h-[430px] rounded-md border border-border">
              <table className="w-full min-w-[700px] text-left text-sm">
                <thead className="sticky top-0 z-10 bg-card text-xs uppercase tracking-wide text-muted-foreground"><tr><th className="px-4 py-3 font-medium">Field</th><th className="px-4 py-3 font-medium">AI value</th><th className="px-4 py-3 font-medium">Human value</th><th className="w-40 px-4 py-3 font-medium">Status</th></tr></thead>
                <tbody className="divide-y divide-border">
                  {fields.map((field, index) => {
                    const status = field.review_status ?? "pending"
                    return <tr key={`${field.name}-${index}`} className="align-middle">
                      <td className="px-4 py-3 font-medium text-foreground">{field.name.replaceAll("_", " ")}</td>
                      <td className="max-w-xs px-4 py-3 text-muted-foreground"><span title={String(field.ai_value ?? "")} className="line-clamp-2">{String(field.ai_value ?? "—")}</span></td>
                      <td className="px-4 py-3"><Label htmlFor={`human-value-${index}`} className="sr-only">Human value for {field.name}</Label><Input id={`human-value-${index}`} value={field.human_value ?? ""} placeholder="Add a correction" onChange={(event) => onFieldChange(index, { human_value: event.target.value, review_status: event.target.value.trim() ? "corrected" : status })} /></td>
                      <td className="px-4 py-3"><div className="flex items-center gap-2"><Select aria-label={`Review status for ${field.name}`} value={status} onChange={(event) => onFieldChange(index, { review_status: event.target.value as ExtractedField["review_status"] })}><option value="pending">Pending</option><option value="approved">Approved</option><option value="rejected">Rejected</option><option value="corrected">Corrected</option></Select><Badge variant={statusVariant(status)}>{status}</Badge></div></td>
                    </tr>
                  })}
                </tbody>
              </table>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      <div className="sticky bottom-4 z-20 flex items-center justify-between rounded-lg border border-border bg-background/95 p-3 shadow-lg backdrop-blur">
        <Button variant="outline" onClick={onBack}><ArrowLeft className="size-4" aria-hidden="true" /> Back to ingest</Button>
        <Button onClick={() => void onSubmit()} disabled={isLoading}>{isLoading ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : <ArrowRight className="size-4" aria-hidden="true" />} Run scoring rules</Button>
      </div>
    </section>
  )
}

function EmptyTableState({ label }: { label: string }) {
  return <div className="flex min-h-28 items-center justify-center rounded-md border border-dashed border-border bg-muted/10 px-4 text-sm text-muted-foreground">{label}</div>
}

function TableSkeleton({ columns }: { columns: number }) {
  const gridClass = columns === 3 ? "grid-cols-3" : "grid-cols-4"
  return (
    <div className="space-y-3 rounded-md border border-border p-4" aria-live="polite" aria-label="Loading table">
      {Array.from({ length: 5 }, (_, row) => (
        <div key={row} className={cn("grid gap-3", gridClass)}>
          {Array.from({ length: columns }, (_, column) => <Skeleton key={column} className="h-9 w-full" />)}
        </div>
      ))}
    </div>
  )
}
