import { Sparkles, ArrowRight, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"

interface NBAProps {
  title: string
  description: string
  actionLabel: string
  href?: string
  onComplete?: () => void
  loading?: boolean
}

export function NBA({ title, description, actionLabel, href, onComplete, loading }: NBAProps) {
  return (
    <div className="relative rounded-3xl border border-amber-500/30 bg-slate-900/60 p-6 sm:p-8 shadow-[0_0_40px_rgba(245,158,11,0.1)] overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-amber-500/10 to-transparent pointer-events-none" />
      
      {/* Animated glow */}
      <div className="absolute -top-24 -right-24 w-48 h-48 bg-amber-500/20 blur-[60px] rounded-full pointer-events-none" />
      
      <div className="relative z-10 flex flex-col md:flex-row gap-8 items-start md:items-center justify-between">
        <div className="space-y-4 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-amber-500">
            <Sparkles className="h-3 w-3" />
            <span>Next Best Action</span>
          </div>
          
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white leading-tight">
            {title}
          </h2>
          
          <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
            {description}
          </p>
        </div>

        <div className="w-full md:w-auto shrink-0">
          <Button
            asChild={!!href}
            onClick={!href ? onComplete : undefined}
            disabled={loading}
            size="lg"
            className="w-full sm:w-auto group relative h-14 px-8 rounded-2xl bg-amber-500 hover:bg-amber-400 disabled:opacity-75 disabled:cursor-not-allowed text-slate-950 font-extrabold text-base transition-all hover:scale-105 shadow-[0_0_20px_rgba(245,158,11,0.4)]"
          >
            {href ? (
              <a href={href} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center gap-2">
                {actionLabel}
                <ExternalLink className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </a>
            ) : (
              <span className="flex items-center justify-center gap-2 cursor-pointer">
                {loading ? (
                  <>
                    <div className="h-4 w-4 rounded-full border-2 border-slate-950 border-t-transparent animate-spin" />
                    <span>Updating...</span>
                  </>
                ) : (
                  <>
                    {actionLabel}
                    <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
                  </>
                )}
              </span>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
