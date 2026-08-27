import { CheckCircle2, ClipboardList, FileCheck2, Flag, RotateCcw, XCircle } from "lucide-react"
import { Badge } from "./ui/badge"
import { Button } from "./ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Progress } from "./ui/progress"
import { ScrollArea } from "./ui/scroll-area"
import { Separator } from "./ui/separator"
import type { ScreeningResponse } from "../types"

interface ResultPhaseProps {
  response: ScreeningResponse
  onReset: () => void
}

function humanize(value: string): string {
  return value.toLowerCase().replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function scoreAsPercent(value: number): number {
  return value <= 1 ? value * 100 : value
}

function recommendationVariant(value: string): "success" | "warning" | "destructive" | "secondary" {
  if (value === "strong_fit") return "success"
  if (value === "borderline") return "warning"
  if (value === "reject") return "destructive"
  return "secondary"
}

export function ResultPhase({ response, onReset }: ResultPhaseProps) {
  const scoreEntries = Object.entries(response.scores).filter(([key, value]) => key !== "final_score" && typeof value === "number")
  const rules = response.rule_results ?? []
  const questions = response.interview_questions ?? []
  return (
    <section className="space-y-6" aria-labelledby="result-title">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">Phase 03</p>
        <h1 id="result-title" className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">Screening result</h1>
        <p className="mt-2 text-sm text-muted-foreground">A transparent summary for a human decision-maker. Review the evidence before taking action.</p>
      </div>

      <Card className="overflow-hidden border-primary/30">
        <div className="border-b border-border bg-primary/[0.06] p-6 sm:p-8">
          <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
            <div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">Recommendation</p><div className="flex flex-wrap items-center gap-3"><h2 className="text-3xl font-semibold tracking-tight text-foreground">{humanize(response.recommendation)}</h2><Badge variant={recommendationVariant(response.recommendation)}>{response.grade ? `Grade ${response.grade}` : "Reviewed output"}</Badge></div><p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">{response.explanation}</p></div>
            <div className="flex shrink-0 items-center gap-3"><div className="rounded-md border border-border bg-background px-4 py-3 text-center"><p className="text-xs uppercase tracking-wide text-muted-foreground">Final score</p><p className="text-2xl font-semibold text-foreground">{response.scores.final_score.toFixed(1)}</p></div><Badge variant={response.hard_fail ? "destructive" : "success"}>{response.hard_fail ? "Hard fail" : "No hard fail"}</Badge></div>
          </div>
        </div>
        <CardContent className="grid gap-4 p-6 sm:grid-cols-3"><SummaryMetric label="Next action" value={humanize(response.next_action ?? "manual_review")} /><SummaryMetric label="Rule checks" value={`${rules.filter((rule) => rule.passed).length}/${rules.length} passed`} /><SummaryMetric label="Evidence confidence" value={typeof response.scores.evidence_confidence === "number" ? `${Math.round(response.scores.evidence_confidence * 100)}%` : "Not provided"} /></CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><FileCheck2 className="size-4 text-primary" aria-hidden="true" /> Rule evaluations</CardTitle><CardDescription>Each check stays tied to its rule ID, severity, and evidence.</CardDescription></CardHeader>
          <CardContent><ScrollArea className="max-h-[530px] space-y-3 pr-2">{rules.length === 0 ? <EmptyResult label="No mandatory rules were supplied." /> : rules.map((rule) => <div key={rule.rule_id} className={`rounded-md border p-4 ${rule.passed ? "border-emerald-500/20 bg-emerald-500/[0.06]" : "border-destructive/30 bg-destructive/[0.07]"}`}><div className="flex flex-wrap items-center justify-between gap-2"><div className="flex items-center gap-2">{rule.passed ? <CheckCircle2 className="size-4 text-emerald-300" aria-hidden="true" /> : <XCircle className="size-4 text-red-300" aria-hidden="true" />}<span className="font-mono text-xs text-foreground">{rule.rule_id}</span></div><Badge variant={rule.passed ? "success" : "destructive"}>{rule.passed ? "Pass" : "Fail"}</Badge></div><p className="mt-2 text-sm leading-6 text-muted-foreground">{rule.message}</p>{rule.severity && <p className="mt-2 text-xs uppercase tracking-wide text-muted-foreground">Severity: {humanize(rule.severity)}</p>}</div>)}</ScrollArea></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><ClipboardList className="size-4 text-primary" aria-hidden="true" /> Score breakdown</CardTitle><CardDescription>Normalized components used by the deterministic scoring policy.</CardDescription></CardHeader>
          <CardContent className="space-y-5">{scoreEntries.map(([key, value]) => { const numericValue = typeof value === "number" ? value : 0; return <div key={key} className="space-y-2"><div className="flex items-center justify-between gap-3 text-sm"><span className="text-muted-foreground">{humanize(key)}</span><span className="font-mono text-xs text-foreground">{numericValue.toFixed(2)}</span></div><Progress value={scoreAsPercent(numericValue)} /></div> })}</CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><Flag className="size-4 text-primary" aria-hidden="true" /> Reviewer summary</CardTitle><CardDescription>Signals to verify before a final disposition.</CardDescription></CardHeader><CardContent className="grid gap-5 sm:grid-cols-3 xl:grid-cols-1 2xl:grid-cols-3"><SummaryList title="Strengths" items={response.strengths ?? []} empty="No strengths surfaced." /><SummaryList title="Concerns" items={response.concerns ?? []} empty="No unresolved concerns." /><SummaryList title="Resume flags" items={response.red_flags ?? []} empty="None surfaced." /></CardContent></Card>
        <Card><CardHeader><CardTitle>Structured interview guide</CardTitle><CardDescription>Use consistent questions and evaluate observable evidence.</CardDescription></CardHeader><CardContent>{questions.length === 0 ? <EmptyResult label="No interview questions were returned." /> : <ScrollArea className="max-h-[360px] space-y-3 pr-2">{questions.map((question, index) => <div key={`${question.question}-${index}`} className="rounded-md border border-border bg-muted/10 p-4"><div className="flex items-start gap-3"><Badge variant="outline">{humanize(question.type)}</Badge><p className="text-sm font-medium leading-6 text-foreground">{question.question}</p></div><p className="mt-3 text-xs leading-5 text-muted-foreground"><span className="font-medium text-foreground">Purpose:</span> {question.purpose}</p><p className="mt-2 text-xs leading-5 text-muted-foreground"><span className="font-medium text-foreground">Signals:</span> {question.good_answer_signals}</p>{question.evidence_anchor && <p className="mt-2 border-l-2 border-primary/50 pl-3 text-xs italic text-muted-foreground">Resume anchor: {question.evidence_anchor}</p>}</div>)}</ScrollArea>}</CardContent></Card>
      </div>

      {response.communication_draft && <Card><CardHeader><CardTitle>Recruiter communication draft</CardTitle><CardDescription>Warm, plain-language copy generated from the reviewed facts. Verify it before sending.</CardDescription></CardHeader><CardContent><pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-md border border-border bg-muted/10 p-4 font-sans text-sm leading-6 text-muted-foreground">{response.communication_draft}</pre></CardContent></Card>}

      <Separator className="h-px w-full" />
      <div className="flex justify-center pb-4"><Button variant="outline" size="lg" onClick={onReset}><RotateCcw className="size-4" aria-hidden="true" /> Start new screening</Button></div>
    </section>
  )
}

function SummaryMetric({ label, value }: { label: string; value: string }) { return <div className="rounded-md border border-border bg-muted/10 p-4"><p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p><p className="mt-1 text-sm font-medium text-foreground">{value}</p></div> }
function SummaryList({ title, items, empty }: { title: string; items: string[]; empty: string }) { return <div><h3 className="text-sm font-medium text-foreground">{title}</h3>{items.length === 0 ? <p className="mt-2 text-xs text-muted-foreground">{empty}</p> : <ul className="mt-2 space-y-2">{items.map((item, index) => <li key={`${item}-${index}`} className="text-xs leading-5 text-muted-foreground">{item}</li>)}</ul>}</div> }
function EmptyResult({ label }: { label: string }) { return <div className="rounded-md border border-dashed border-border p-5 text-sm text-muted-foreground">{label}</div> }
