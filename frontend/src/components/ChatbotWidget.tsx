import { useEffect, useRef, useState, type FormEvent } from "react"
import {
  Bot,
  ChevronLeft,
  ClockArrowUp,
  History,
  Loader2,
  MessageCircle,
  PenSquare,
  Send,
  Sparkles,
  Trash2,
  UserRound,
  X,
} from "lucide-react"
import { getApiErrorMessage, sendChatMessage } from "../lib/api"
import type { CandidateProfile, ChatMessage, JobRequirement, ScreeningResponse } from "../types"
import { Badge } from "./ui/badge"
import { Button } from "./ui/button"

interface ChatbotWidgetProps {
  candidate: CandidateProfile
  job: JobRequirement
  response: ScreeningResponse | null
}

interface ConversationItem {
  message: ChatMessage
  sources?: string[]
}

interface SavedSession {
  id: string
  title: string
  savedAt: string
  items: ConversationItem[]
}

const STORAGE_KEY = "hr-screening-chatbot-history"
const MAX_SESSIONS = 20

const suggestions = [
  "Summarize candidate strengths",
  "What is the candidate's total experience?",
  "Why did the rule fail?",
  "Draft a follow-up question",
]

function loadSessions(): SavedSession[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]") as SavedSession[]
  } catch {
    return []
  }
}

function saveSessions(sessions: SavedSession[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(0, MAX_SESSIONS)))
}

function deriveTitle(items: ConversationItem[]): string {
  const first = items.find((i) => i.message.role === "user")?.message.content
  if (!first) return "Untitled chat"
  return first.length > 50 ? first.slice(0, 47) + "…" : first
}

function formatTime(iso: string): string {
  const date = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return "just now"
  if (diffMin < 60) return `${diffMin}m ago`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH}h ago`
  return date.toLocaleDateString()
}

export function ChatbotWidget({ candidate, job, response }: ChatbotWidgetProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [draft, setDraft] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conversation, setConversation] = useState<ConversationItem[]>([])
  const [sessions, setSessions] = useState<SavedSession[]>(loadSessions)
  const [showHistory, setShowHistory] = useState(false)
  const endOfMessagesRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen) endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [conversation, isLoading, isOpen])

  const flushToHistory = (items: ConversationItem[]) => {
    if (items.length === 0) return
    setSessions((prev) => {
      const session: SavedSession = {
        id: crypto.randomUUID(),
        title: deriveTitle(items),
        savedAt: new Date().toISOString(),
        items,
      }
      const updated = [session, ...prev.filter((s) => s.title !== session.title)]
      saveSessions(updated)
      return updated
    })
  }

  const startNewChat = () => {
    flushToHistory(conversation)
    setConversation([])
    setDraft("")
    setError(null)
    setShowHistory(false)
  }

  const restoreSession = (session: SavedSession) => {
    flushToHistory(conversation)
    setConversation(session.items)
    setShowHistory(false)
    setError(null)
  }

  const deleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setSessions((prev) => {
      const updated = prev.filter((s) => s.id !== id)
      saveSessions(updated)
      return updated
    })
  }

  const submitMessage = async (value: string) => {
    const content = value.trim()
    if (!content || isLoading) return

    const userMessage: ChatMessage = {
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    }
    const nextConversation = [...conversation, { message: userMessage }]
    setConversation(nextConversation)
    setDraft("")
    setError(null)
    setIsLoading(true)

    try {
      const result = await sendChatMessage({
        messages: nextConversation.map((item) => item.message),
        candidate,
        job,
        response,
      })
      setConversation((current) => [...current, { message: result.reply, sources: result.sources }])
    } catch (chatError: unknown) {
      setError(getApiErrorMessage(chatError, "The recruiter copilot is unavailable."))
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void submitMessage(draft)
  }

  if (!isOpen) {
    return (
      <Button
        className="fixed bottom-5 right-5 z-40 h-12 rounded-full px-4 shadow-lg sm:bottom-6 sm:right-6"
        onClick={() => setIsOpen(true)}
        aria-label="Open recruiter copilot"
        aria-expanded={false}
      >
        <MessageCircle className="size-4" aria-hidden="true" />
        <span>Recruiter copilot</span>
        {sessions.length > 0 && (
          <span
            className="flex size-5 items-center justify-center rounded-full bg-primary-foreground text-[10px] font-bold text-primary"
            aria-label={`${sessions.length} past sessions`}
          >
            {sessions.length}
          </span>
        )}
      </Button>
    )
  }

  return (
    <section
      className="fixed bottom-4 right-4 z-40 flex h-[min(680px,calc(100vh-2rem))] w-[min(430px,calc(100vw-2rem))] flex-col overflow-hidden rounded-xl border border-border bg-card shadow-2xl sm:bottom-6 sm:right-6"
      aria-label="Recruiter copilot"
    >
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border bg-muted/25 px-4 py-3">
        <div className="flex min-w-0 items-center gap-3">
          {showHistory ? (
            <button
              type="button"
              onClick={() => setShowHistory(false)}
              className="flex size-9 shrink-0 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground"
              aria-label="Back to chat"
            >
              <ChevronLeft className="size-4" aria-hidden="true" />
            </button>
          ) : (
            <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Sparkles className="size-4" aria-hidden="true" />
            </div>
          )}
          <div className="min-w-0">
            <h2 className="truncate text-sm font-semibold text-foreground">
              {showHistory ? "Chat history" : "Recruiter copilot"}
            </h2>
            {!showHistory && (
              <p className="truncate text-xs text-muted-foreground">
                Grounded in {candidate.full_name || "this screening"}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          {!showHistory && (
            <>
              <Button
                variant="ghost"
                size="icon"
                onClick={startNewChat}
                aria-label="New chat"
                title="New chat"
                disabled={conversation.length === 0}
              >
                <PenSquare className="size-4" aria-hidden="true" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowHistory(true)}
                aria-label="View chat history"
                title="History"
                className="relative"
              >
                <History className="size-4" aria-hidden="true" />
                {sessions.length > 0 && (
                  <span className="absolute right-1.5 top-1.5 size-1.5 rounded-full bg-primary" />
                )}
              </Button>
            </>
          )}
          <Button variant="ghost" size="icon" onClick={() => setIsOpen(false)} aria-label="Close recruiter copilot">
            <X className="size-4" aria-hidden="true" />
          </Button>
        </div>
      </header>

      {/* History panel */}
      {showHistory ? (
        <div className="min-h-0 flex-1 overflow-y-auto">
          {sessions.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center">
              <ClockArrowUp className="size-10 text-muted-foreground/40" aria-hidden="true" />
              <p className="text-sm text-muted-foreground">No saved conversations yet.</p>
              <p className="text-xs text-muted-foreground/70">
                Start a chat and your history will appear here.
              </p>
            </div>
          ) : (
            <ul className="divide-y divide-border" role="list">
              {sessions.map((session) => (
                <li key={session.id}>
                  <button
                    type="button"
                    className="flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-accent"
                    onClick={() => restoreSession(session)}
                    aria-label={`Restore session: ${session.title}`}
                  >
                    <MessageCircle className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-foreground">{session.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {session.items.length} messages · {formatTime(session.savedAt)}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => deleteSession(session.id, e)}
                      className="ml-1 shrink-0 rounded p-1 text-muted-foreground/60 hover:bg-destructive/10 hover:text-destructive"
                      aria-label={`Delete session: ${session.title}`}
                      title="Delete"
                    >
                      <Trash2 className="size-3.5" aria-hidden="true" />
                    </button>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : (
        <>
          {/* Chat thread */}
          <div className="min-h-0 flex-1 overflow-y-auto p-4">
            {conversation.length === 0 ? (
              <div className="flex h-full flex-col justify-center">
                <div className="mb-5 rounded-lg border border-primary/20 bg-primary/5 p-4">
                  <p className="text-sm font-medium text-foreground">Ask about the screening context</p>
                  <p className="mt-1 text-xs leading-5 text-muted-foreground">
                    I can explain recorded evidence, requirements, rule outcomes, and interview strategy. I will
                    call out anything missing from the screening memory.
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      className="rounded-full border border-border bg-background px-3 py-2 text-left text-xs text-foreground transition-colors hover:border-primary/50 hover:bg-accent"
                      onClick={() => void submitMessage(suggestion)}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {conversation.map((item, index) => (
                  <div
                    key={`${item.message.timestamp}-${index}`}
                    className={`flex gap-2.5 ${item.message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {item.message.role !== "user" && (
                      <Bot className="mt-1 size-4 shrink-0 text-primary" aria-hidden="true" />
                    )}
                    <div
                      className={`max-w-[88%] rounded-lg px-3 py-2.5 text-sm leading-6 ${
                        item.message.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "border border-border bg-muted/35 text-foreground"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{item.message.content}</p>
                      {item.sources && item.sources.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-1.5 border-t border-border/70 pt-2">
                          {item.sources.map((source) => (
                            <Badge key={source} variant="outline" className="max-w-full font-mono text-[10px]">
                              {source}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    {item.message.role === "user" && (
                      <UserRound className="mt-1 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                    )}
                  </div>
                ))}
                {isLoading && (
                  <div className="flex items-center gap-2.5 text-xs text-muted-foreground" aria-live="polite">
                    <Bot className="size-4 text-primary" aria-hidden="true" />
                    <div className="flex items-center gap-1 rounded-lg border border-border bg-muted/35 px-3 py-2.5">
                      <span className="size-1.5 animate-pulse rounded-full bg-primary" />
                      <span className="size-1.5 animate-pulse rounded-full bg-primary [animation-delay:150ms]" />
                      <span className="size-1.5 animate-pulse rounded-full bg-primary [animation-delay:300ms]" />
                      <span className="sr-only">Copilot is typing</span>
                    </div>
                  </div>
                )}
                <div ref={endOfMessagesRef} />
              </div>
            )}
          </div>

          {error && (
            <p
              className="border-t border-destructive/20 bg-destructive/5 px-4 py-2 text-xs text-destructive"
              role="alert"
            >
              {error}
            </p>
          )}

          <form onSubmit={handleSubmit} className="flex items-end gap-2 border-t border-border bg-background p-3">
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault()
                  void submitMessage(draft)
                }
              }}
              placeholder="Ask about this screening..."
              rows={2}
              maxLength={4000}
              disabled={isLoading}
              className="min-h-10 flex-1 resize-none rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Recruiter question"
            />
            <Button type="submit" size="icon" disabled={!draft.trim() || isLoading} aria-label="Send question">
              {isLoading ? (
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              ) : (
                <Send className="size-4" aria-hidden="true" />
              )}
            </Button>
          </form>
        </>
      )}
    </section>
  )
}

