export interface SourceCitation {
  title: string
  source_url?: string | null
  source_id?: string | null
}

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
  suggested_resource?: string | null
  next_best_action?: string
  next_best_action_type?: string | null
  reasoning_summary?: string | null
  sources?: SourceCitation[]
  confidence?: string | null
}


export interface CoachChatPayload {
  message: string
  conversation_history: ChatMessage[]
}

export interface CoachResponse {
  message: string
  quick_actions: string[]
  suggested_resource: string | null
  next_best_action?: string
  next_best_action_type?: string | null
  reasoning_summary?: string | null
  sources?: SourceCitation[]
  confidence?: string | null
}
