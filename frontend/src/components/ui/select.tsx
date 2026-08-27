import { forwardRef, type SelectHTMLAttributes } from "react"
import { cn } from "../../lib/utils"

const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(({ className, ...props }, ref) => (
  <select ref={ref} className={cn("flex h-9 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring", className)} {...props} />
))
Select.displayName = "Select"

export { Select }
