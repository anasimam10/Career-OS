import { Sparkles, User } from "lucide-react"
import { cn } from "@/lib/utils/cn"
import type { ChatMessage as ChatMessageType } from "@/lib/types/coach.types"

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === "user"

  return (
    <div
      className={cn(
        "flex items-start gap-3 w-full",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-xs font-bold shadow-sm",
          isUser
            ? "bg-secondary text-secondary-foreground"
            : "bg-primary text-primary-foreground"
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
      </div>

      <div
        className={cn(
          "rounded-2xl px-4 py-3 text-sm leading-relaxed max-w-[85%] sm:max-w-[75%]",
          isUser
            ? "bg-primary text-primary-foreground font-medium rounded-tr-sm"
            : "bg-card border border-border text-foreground rounded-tl-sm shadow-card"
        )}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  )
}
