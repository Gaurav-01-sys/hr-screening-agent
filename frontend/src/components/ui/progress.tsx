import { forwardRef, type HTMLAttributes } from "react"
import { cn } from "../../lib/utils"

interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
  value?: number
}

const widthClasses = [
  "w-0", "w-[5%]", "w-[10%]", "w-[15%]", "w-[20%]", "w-[25%]",
  "w-[30%]", "w-[35%]", "w-[40%]", "w-[45%]", "w-1/2", "w-[55%]",
  "w-[60%]", "w-[65%]", "w-[70%]", "w-[75%]", "w-4/5", "w-[85%]",
  "w-[90%]", "w-[95%]", "w-full",
] as const

const Progress = forwardRef<HTMLDivElement, ProgressProps>(({ className, value = 0, ...props }, ref) => {
  const clampedValue = Math.max(0, Math.min(100, value))
  const widthClass = widthClasses[Math.round(clampedValue / 5)]
  return (
    <div
      ref={ref}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(clampedValue)}
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-secondary", className)}
      {...props}
    >
      <div className={cn("h-full bg-primary transition-all", widthClass)} />
    </div>
  )
})
Progress.displayName = "Progress"

export { Progress }
