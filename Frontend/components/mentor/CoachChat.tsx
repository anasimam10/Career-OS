"use client"

import { useState, useRef, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { Send, Sparkles, User, RefreshCw, Check, Copy } from "lucide-react"
import { useCoachChat } from "@/hooks/useCoachChat"
import { ChatMessage } from "./ChatMessage"
import { TypingIndicator } from "./TypingIndicator"
import { QuickActions } from "./QuickActions"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ErrorState } from "@/components/shared/ErrorState"

function CoachChatContent() {
  const { messages, quickActions, loading, error, sendMessage } = useCoachChat()
  const [input, setInput] = useState("")
  const scrollRef = useRef<HTMLDivElement>(null)
  const searchParams = useSearchParams()
  const promptParam = searchParams.get("prompt")
  const initialPromptSent = useRef(false)

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  // If navigated with a prompt query param, auto-populate or send
  useEffect(() => {
    if (promptParam && !initialPromptSent.current && !loading) {
      initialPromptSent.current = true
      sendMessage(promptParam)
    }
  }, [promptParam, sendMessage, loading])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return
    sendMessage(input)
    setInput("")
  }

  const handleQuickSelect = (action: string) => {
    if (loading) return
    sendMessage(action)
  }

  return (
    <div className="flex flex-col h-[650px] max-w-4xl mx-auto rounded-3xl border border-border bg-card shadow-sm overflow-hidden">
      {/* Mentor Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/30">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-blue-600 text-white font-bold shadow-sm">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-bold text-foreground text-base leading-none">
              A&H Careers AI Mentor
            </h3>
            <span className="text-xs text-muted-foreground mt-0.5 block">
              Context-aware guidance for your career journey in Pakistan
            </span>
          </div>
        </div>

        <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          Active Session
        </span>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        {messages.map((msg, idx) => (
          <ChatMessage key={idx} message={msg} />
        ))}

        {loading && (
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground text-xs font-bold shadow-sm">
              <Sparkles className="h-4 w-4" />
            </div>
            <TypingIndicator />
          </div>
        )}

        {error && <ErrorState message={error} />}

        <div ref={scrollRef} />
      </div>

      {/* Footer / Input Area */}
      <div className="p-4 sm:p-6 border-t border-border bg-muted/10 space-y-4">
        {/* Quick Actions */}
        <QuickActions
          actions={quickActions}
          onSelect={handleQuickSelect}
          disabled={loading}
        />

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your mentor a question (e.g. 'Should I choose Computer Science?')..."
            disabled={loading}
            className="h-12 text-sm rounded-2xl bg-background shadow-sm"
          />
          <Button
            type="submit"
            disabled={loading || !input.trim()}
            className="h-12 px-6 rounded-2xl gap-2 font-semibold shadow-sm"
          >
            <span>Send</span>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  )
}

export function CoachChat() {
  return (
    <Suspense fallback={<div className="h-[650px] rounded-3xl border border-border bg-card animate-pulse" />}>
      <CoachChatContent />
    </Suspense>
  )
}
