"use client"

import { useState, useCallback } from "react"
import { sendChatMessage } from "@/lib/api/coach"
import type { ChatMessage, CoachResponse } from "@/lib/types/coach.types"

export function useCoachChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Assalam-o-Alaikum! I'm your career mentor. I'm here to give you clear, actionable guidance on your next step. What are you thinking about right now?",
    },
  ])
  const [quickActions, setQuickActions] = useState<string[]>([
    "What should I do next?",
    "Am I ready for an internship?",
    "Should I explore another field?",
    "How do I prepare for tech jobs in Pakistan?",
  ])
  const [suggestedResource, setSuggestedResource] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return

      const userMsg: ChatMessage = { role: "user", content: text.trim() }
      const newHistory = [...messages, userMsg]
      setMessages(newHistory)
      setLoading(true)
      setError(null)

      try {
        const response: CoachResponse = await sendChatMessage({
          message: text.trim(),
          conversation_history: newHistory,
        })
        const botMsg: ChatMessage = { role: "assistant", content: response.message }
        setMessages((prev) => [...prev, botMsg])
        if (response.quick_actions?.length) {
          setQuickActions(response.quick_actions)
        }
        setSuggestedResource(response.suggested_resource)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to get response")
      } finally {
        setLoading(false)
      }
    },
    [messages, loading]
  )

  return {
    messages,
    quickActions,
    suggestedResource,
    loading,
    error,
    sendMessage,
  }
}
