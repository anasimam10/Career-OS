import { Compass, ExternalLink, Sparkles, User } from "lucide-react"
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
          "rounded-2xl px-4 py-3 text-sm leading-relaxed max-w-[85%] sm:max-w-[75%] space-y-3",
          isUser
            ? "bg-primary text-primary-foreground font-medium rounded-tr-sm"
            : "bg-card border border-border text-foreground rounded-tl-sm shadow-card"
        )}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>

        {/* ONE Next Best Action Callout */}
        {!isUser && message.next_best_action && (
          <div className="p-3 rounded-xl bg-primary/10 border border-primary/20 text-foreground">
            <div className="flex items-center gap-1.5 text-xs font-bold text-primary uppercase tracking-wider mb-1">
              <Compass className="h-3.5 w-3.5" />
              <span>Next Best Action</span>
              {message.next_best_action_type && (
                <span className="text-[10px] font-semibold bg-primary/20 px-1.5 py-0.2 rounded text-primary">
                  {message.next_best_action_type}
                </span>
              )}
            </div>
            <p className="text-xs sm:text-sm font-semibold text-foreground">
              {message.next_best_action}
            </p>
            {message.reasoning_summary && (
              <p className="text-[11px] text-muted-foreground mt-1">
                {message.reasoning_summary}
              </p>
            )}
          </div>
        )}

        {/* Verified Provenance Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="pt-2 border-t border-border/50 flex flex-wrap gap-1.5 items-center">
            <span className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
              <ExternalLink className="h-3 w-3" /> Verified Sources:
            </span>
            {message.sources.map((src, idx) =>
              src.source_url ? (
                <a
                  key={idx}
                  href={src.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[11px] text-primary hover:underline bg-primary/5 px-2 py-0.5 rounded-md border border-primary/10 inline-flex items-center gap-1 transition-colors"
                >
                  {src.title}
                </a>
              ) : (
                <span
                  key={idx}
                  className="text-[11px] text-muted-foreground bg-muted px-2 py-0.5 rounded-md border border-border"
                >
                  {src.title}
                </span>
              )
            )}
          </div>
        )}
      </div>
    </div>
  )
}

