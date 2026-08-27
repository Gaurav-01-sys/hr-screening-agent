import { Check, Circle } from "lucide-react"
import { cn } from "../lib/utils"
import type { Phase } from "../types"

interface PhaseStepperProps {
  phase: Phase
  canNavigate: (phase: Phase) => boolean
  onNavigate: (phase: Phase) => void
}

const steps: Array<{ phase: Phase; label: string }> = [
  { phase: "INGEST", label: "Ingest" },
  { phase: "REVIEW", label: "Review" },
  { phase: "RESULT", label: "Result" },
]

export function PhaseStepper({ phase, canNavigate, onNavigate }: PhaseStepperProps) {
  const currentIndex = steps.findIndex((step) => step.phase === phase)
  return (
    <nav aria-label="Screening progress" className="mx-auto flex w-full max-w-3xl items-center justify-center gap-2 sm:gap-4">
      {steps.map((step, index) => {
        const completed = index < currentIndex
        const current = step.phase === phase
        const enabled = canNavigate(step.phase)
        return (
          <div key={step.phase} className="flex min-w-0 items-center gap-2 sm:gap-3">
            <button
              type="button"
              disabled={!enabled}
              onClick={() => onNavigate(step.phase)}
              aria-current={current ? "step" : undefined}
              className={cn(
                "flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                current && "bg-accent text-foreground",
                completed && enabled && "text-foreground hover:bg-accent",
                !current && !completed && "text-muted-foreground",
                !enabled && "cursor-not-allowed opacity-60",
              )}
            >
              <span className={cn("flex size-6 items-center justify-center rounded-full border text-xs", current && "border-primary bg-primary text-primary-foreground", completed && "border-emerald-500/50 bg-emerald-500/10 text-emerald-300", !current && !completed && "border-border text-muted-foreground")}>
                {completed ? <Check className="size-3.5" aria-hidden="true" /> : current ? index + 1 : <Circle className="size-3" aria-hidden="true" />}
              </span>
              <span className="hidden font-medium sm:inline">{index + 1}. {step.label}</span>
            </button>
            {index < steps.length - 1 && <span className="h-px w-5 bg-border sm:w-12" aria-hidden="true" />}
          </div>
        )
      })}
    </nav>
  )
}
