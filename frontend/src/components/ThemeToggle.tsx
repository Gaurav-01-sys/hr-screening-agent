import { Monitor, Moon, Sun } from "lucide-react"
import { useTheme, type Theme } from "./ThemeProvider"
import { Button } from "./ui/button"

const CYCLE: Theme[] = ["system", "light", "dark"]

const LABELS: Record<Theme, string> = {
  system: "System theme",
  light: "Light theme",
  dark: "Dark theme",
}

const ICONS: Record<Theme, typeof Sun> = {
  system: Monitor,
  light: Sun,
  dark: Moon,
}

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const Icon = ICONS[theme]

  const handleClick = () => {
    const currentIndex = CYCLE.indexOf(theme)
    const next = CYCLE[(currentIndex + 1) % CYCLE.length]
    setTheme(next)
  }

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={handleClick}
      aria-label={`Current theme: ${LABELS[theme]}. Click to switch.`}
      title={LABELS[theme]}
      className="shrink-0"
    >
      <Icon className="size-4" aria-hidden="true" />
    </Button>
  )
}
