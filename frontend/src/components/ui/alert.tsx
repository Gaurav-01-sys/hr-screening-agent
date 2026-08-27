import { forwardRef, type HTMLAttributes } from "react"
import { cn } from "../../lib/utils"

interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "destructive"
}

const Alert = forwardRef<HTMLDivElement, AlertProps>(({ className, variant = "default", ...props }, ref) => (
  <div ref={ref} role="alert" className={cn("relative w-full rounded-lg border p-4 text-sm", variant === "destructive" ? "border-destructive/40 bg-destructive/10 text-red-200" : "border-border bg-card text-foreground", className)} {...props} />
))
Alert.displayName = "Alert"

const AlertTitle = ({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) => (
  <h5 className={cn("mb-1 font-medium leading-none tracking-tight", className)} {...props} />
)
const AlertDescription = ({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) => (
  <div className={cn("text-sm opacity-90", className)} {...props} />
)

export { Alert, AlertTitle, AlertDescription }
