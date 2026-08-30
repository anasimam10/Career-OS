export interface ChatMessage {
  role: "user" | "assistant"
  content: string
}

export interface CoachChatPayload {
  message: string
  conversation_history: ChatMessage[]
}

export interface CoachResponse {
  message: string
  quick_actions: string[]
  suggested_resource: string | null
}
