import { Compass, ExternalLink, Sparkles, User, BookOpen, ShieldCheck, Terminal } from "lucide-react"
import { cn } from "@/lib/utils/cn"
import type { ChatMessage as ChatMessageType } from "@/lib/types/coach.types"
import { MarkdownText } from "@/components/shared/MarkdownText"

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === "user"

  return (
    <div
      className={cn(
        "flex items-start gap-4 w-full group",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      <div
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-xs font-bold transition-transform group-hover:scale-105",
          isUser
            ? "bg-slate-800 text-slate-300 border border-slate-700 shadow-sm"
            : "bg-indigo-600 text-white shadow-[0_0_15px_rgba(79,70,229,0.3)]"
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Terminal className="h-5 w-5" />}
      </div>

      <div
        className={cn(
          "rounded-2xl px-5 py-4 text-sm leading-relaxed max-w-[90%] sm:max-w-[85%] space-y-4 shadow-sm",
          isUser
            ? "bg-slate-800 text-slate-200 font-medium rounded-tr-sm border border-slate-700/50"
            : "bg-slate-900/80 border border-indigo-500/20 text-slate-300 rounded-tl-sm backdrop-blur-md"
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-slate-950 prose-pre:border prose-pre:border-slate-800 text-slate-300">
            <MarkdownText content={message.content} />
          </div>
        )}

        {/* Suggested Resource Card */}
        {!isUser && message.suggested_resource && (
          <div className="flex items-start gap-3 rounded-xl border border-indigo-500/20 bg-indigo-500/10 p-4 text-slate-300">
            <BookOpen className="h-4 w-4 text-indigo-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-400">
                Data Archive
              </span>
              <p className="text-xs font-medium text-indigo-100">
                {message.suggested_resource}
              </p>
            </div>
          </div>
        )}

        {/* ONE Next Best Action Callout (Strictly warm amber accent) */}
        {!isUser && message.next_best_action && (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 overflow-hidden relative">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(245,158,11,0.1),transparent)] pointer-events-none" />
            
            <div className="relative z-10 flex items-center gap-2 text-xs font-bold text-amber-500 uppercase tracking-widest mb-2">
              <Compass className="h-4 w-4" />
              <span>Priority Action</span>
              {message.next_best_action_type && (
                <span className="text-[9px] font-bold bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full border border-amber-500/30">
                  {message.next_best_action_type}
                </span>
              )}
            </div>
            
            <p className="relative z-10 text-sm font-bold text-white mb-1.5">
              {message.next_best_action}
            </p>
            
            {message.reasoning_summary && (
              <p className="relative z-10 text-xs text-amber-200/70 leading-relaxed border-t border-amber-500/20 pt-2 mt-2">
                {message.reasoning_summary}
              </p>
            )}
          </div>
        )}

        {/* Verified Provenance Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="pt-3 mt-2 border-t border-slate-800 flex flex-wrap gap-2 items-center">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" /> Verified Sources:
            </span>
            {message.sources.map((src, idx) =>
              src.source_url ? (
                <a
                  key={idx}
                  href={src.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[10px] text-slate-300 hover:text-indigo-300 hover:bg-slate-800 bg-slate-900 px-2 py-1 rounded-md border border-slate-700 inline-flex items-center gap-1 transition-colors font-medium"
                >
                  <span>{src.title}</span>
                  <ExternalLink className="h-2.5 w-2.5 opacity-60" />
                </a>
              ) : (
                <span
                  key={idx}
                  className="text-[10px] text-slate-400 bg-slate-900 px-2 py-1 rounded-md border border-slate-800 font-medium"
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
