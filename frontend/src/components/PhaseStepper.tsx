import { Check } from "lucide-react"
import { cn } from "../lib/utils"
import type { Phase } from "../types"

interface PhaseStepperProps {
  phase: Phase
  canNavigate: (phase: Phase) => boolean
  onNavigate: (phase: Phase) => void
}

const steps: Array<{ phase: Phase; label: string; description: string }> = [
  { phase: "INGEST", label: "Ingest", description: "Load documents" },
  { phase: "REVIEW", label: "Review", description: "Verify facts" },
  { phase: "RESULT", label: "Result", description: "Screening outcome" },
]

export function PhaseStepper({ phase, canNavigate, onNavigate }: PhaseStepperProps) {
  const currentIndex = steps.findIndex((step) => step.phase === phase)
  return (
    <nav aria-label="Screening progress" className="mx-auto flex w-full max-w-3xl items-center justify-center">
      {steps.map((step, index) => {
        const completed = index < currentIndex
        const current = step.phase === phase
        const enabled = canNavigate(step.phase)
        const isLast = index === steps.length - 1

        return (
          <div key={step.phase} className="flex flex-1 items-center">
            <button
              type="button"
              disabled={!enabled}
              onClick={() => onNavigate(step.phase)}
              aria-current={current ? "step" : undefined}
              className={cn(
                "group flex flex-col items-center gap-1.5 focus-visible:outline-none",
                !enabled && "cursor-not-allowed",
              )}
            >
              {/* Step bubble */}
              <span
                className={cn(
                  "flex size-8 items-center justify-center rounded-full border-2 text-xs font-semibold transition-all",
                  current && "border-primary bg-primary text-primary-foreground ring-4 ring-primary/20",
                  completed && "border-emerald-500 bg-emerald-500 text-white dark:bg-emerald-500",
                  !current && !completed && "border-border bg-background text-muted-foreground",
                  enabled && !current && "group-hover:border-primary/50",
                  !enabled && "opacity-50",
                )}
              >
                {completed ? <Check className="size-4" aria-hidden="true" /> : index + 1}
              </span>

              {/* Step label */}
              <span
                className={cn(
                  "hidden flex-col items-center sm:flex",
                  current && "text-foreground",
                  completed && "text-foreground",
                  !current && !completed && "text-muted-foreground",
                  !enabled && "opacity-50",
                )}
              >
                <span className={cn("text-xs font-medium", current && "font-semibold")}>{step.label}</span>
                <span className="text-[10px] text-muted-foreground">{step.description}</span>
              </span>
            </button>

            {/* Connector line between steps */}
            {!isLast && (
              <div className="mx-2 flex-1">
                <div
                  className={cn(
                    "h-0.5 w-full rounded-full transition-colors",
                    index < currentIndex ? "bg-emerald-500" : "bg-border",
                  )}
                  aria-hidden="true"
                />
              </div>
            )}
          </div>
        )
      })}
    </nav>
  )
}
