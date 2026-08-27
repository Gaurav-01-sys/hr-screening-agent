import { forwardRef, type HTMLAttributes } from "react"
import { cn } from "../../lib/utils"

const Separator = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} role="separator" className={cn("shrink-0 bg-border", className)} {...props} />
))
Separator.displayName = "Separator"

export { Separator }
