import { useEffect, useState } from "react"
import { Activity, CircleDot, RotateCcw } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "./components/ui/alert"
import { Button } from "./components/ui/button"
import { Separator } from "./components/ui/separator"
import { PhaseStepper } from "./components/PhaseStepper"
import { IngestPhase } from "./components/IngestPhase"
import { ReviewPhase } from "./components/ReviewPhase"
import { ResultPhase } from "./components/ResultPhase"
import { API_URL, extractScreening, getApiErrorMessage, getHealth, parseDocument, screenCandidate } from "./lib/api"
import type { ExtractedField, HealthResponse, Phase, ScreeningRequest, ScreeningResponse, SkillExperience } from "./types"

type ApiStatus = "checking" | "online" | "offline"

function App() {
  const [phase, setPhase] = useState<Phase>("INGEST")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking")
  const [resumeText, setResumeText] = useState("")
  const [jdText, setJdText] = useState("")
  const [ruleNotes, setRuleNotes] = useState("")
  const [screeningReq, setScreeningReq] = useState<ScreeningRequest | null>(null)
  const [screeningRes, setScreeningRes] = useState<ScreeningResponse | null>(null)

  useEffect(() => {
    let active = true
    void getHealth()
      .then((health: HealthResponse) => {
        if (active) setApiStatus(health.status === "ok" ? "online" : "offline")
      })
      .catch(() => {
        if (active) setApiStatus("offline")
      })
    return () => {
      active = false
    }
  }, [])

  const reset = () => {
    setPhase("INGEST")
    setIsLoading(false)
    setError(null)
    setResumeText("")
    setJdText("")
    setRuleNotes("")
    setScreeningReq(null)
    setScreeningRes(null)
  }

  const canNavigate = (target: Phase): boolean => {
    if (target === "INGEST") return true
    if (target === "REVIEW") return screeningReq !== null
    return screeningRes !== null
  }

  const navigate = (target: Phase) => {
    if (canNavigate(target)) {
      setError(null)
      setPhase(target)
    }
  }

  const handleUpload = async (file: File, target: "resume" | "jd") => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await parseDocument(file)
      if (result.error) throw new Error(result.error)
      const text = result.text?.trim() ?? ""
      if (!text) throw new Error("The document parser returned no text.")
      if (target === "resume") setResumeText(text)
      else setJdText(text)
    } catch (uploadError: unknown) {
      setError(getApiErrorMessage(uploadError, "Failed to parse document."))
    } finally {
      setIsLoading(false)
    }
  }

  const handleExtract = async () => {
    if (!resumeText.trim() || !jdText.trim()) {
      setError("Provide both a resume and a job description before extracting.")
      return
    }
    setIsLoading(true)
    setError(null)
    try {
      const request = await extractScreening({ resume_text: resumeText, jd_text: jdText, mandatory_rule_notes: ruleNotes })
      setScreeningReq(request)
      setScreeningRes(null)
      setPhase("REVIEW")
    } catch (extractError: unknown) {
      setError(getApiErrorMessage(extractError, "Failed to extract candidate and job facts."))
    } finally {
      setIsLoading(false)
    }
  }

  const handleScreening = async () => {
    if (!screeningReq) return
    setIsLoading(true)
    setError(null)
    try {
      const result = await screenCandidate(screeningReq)
      setScreeningRes(result)
      setPhase("RESULT")
    } catch (screenError: unknown) {
      setError(getApiErrorMessage(screenError, "Failed to run screening rules."))
    } finally {
      setIsLoading(false)
    }
  }

  const updateSkill = (index: number, patch: Partial<SkillExperience>) => {
    setScreeningReq((current) => {
      if (!current) return current
      const skills = current.candidate.skills ?? []
      return {
        ...current,
        candidate: {
          ...current.candidate,
          skills: skills.map((skill, skillIndex) => (skillIndex === index ? { ...skill, ...patch } : skill)),
        },
      }
    })
  }

  const updateField = (index: number, patch: Partial<ExtractedField>) => {
    setScreeningReq((current) => {
      if (!current) return current
      const fields = current.candidate.fields_for_review ?? []
      return {
        ...current,
        candidate: {
          ...current.candidate,
          fields_for_review: fields.map((field, fieldIndex) => (fieldIndex === index ? { ...field, ...patch } : field)),
        },
      }
    })
  }

  return (
    <div className="dark min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-background/95">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-md border border-primary/30 bg-primary/10 text-primary"><Activity className="size-4" aria-hidden="true" /></div>
            <div className="min-w-0"><p className="truncate text-sm font-semibold tracking-tight text-foreground">HR Screening</p><p className="truncate text-xs text-muted-foreground">Evidence-backed candidate workbench</p></div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex" aria-live="polite"><CircleDot className={`size-3 ${apiStatus === "online" ? "text-emerald-400" : apiStatus === "offline" ? "text-red-400" : "text-amber-400"}`} aria-hidden="true" />{apiStatus === "online" ? "API connected" : apiStatus === "offline" ? "API unavailable" : "Checking API"}</div>
            <Button variant="outline" size="sm" onClick={reset}><RotateCcw className="size-3.5" aria-hidden="true" /> New screening</Button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 space-y-5"><PhaseStepper phase={phase} canNavigate={canNavigate} onNavigate={navigate} /><Separator className="h-px w-full" /></div>
        {error && <Alert variant="destructive" className="mb-6"><AlertTitle>Action failed</AlertTitle><AlertDescription>{error}</AlertDescription></Alert>}
        <div className="mx-auto max-w-6xl">
          {phase === "INGEST" && <IngestPhase resumeText={resumeText} jdText={jdText} ruleNotes={ruleNotes} isLoading={isLoading} error={null} onResumeTextChange={setResumeText} onJdTextChange={setJdText} onRuleNotesChange={setRuleNotes} onUpload={handleUpload} onExtract={handleExtract} />}
          {phase === "REVIEW" && screeningReq && <ReviewPhase request={screeningReq} isLoading={isLoading} onSkillChange={updateSkill} onFieldChange={updateField} onBack={() => navigate("INGEST")} onSubmit={handleScreening} />}
          {phase === "RESULT" && screeningRes && <ResultPhase response={screeningRes} onReset={reset} />}
        </div>
      </main>
      <footer className="mx-auto flex max-w-7xl items-center justify-between border-t border-border px-4 py-5 text-xs text-muted-foreground sm:px-6 lg:px-8"><span>Human review stays in the loop.</span><span className="hidden sm:inline">{API_URL}</span></footer>
    </div>
  )
}

export default App
