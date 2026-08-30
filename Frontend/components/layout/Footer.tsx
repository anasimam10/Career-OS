import Link from "next/link"

export function Footer() {
  return (
    <footer className="border-t border-border bg-background py-10 pb-24 md:pb-10">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-foreground">A&H Careers</span>
          <span>•</span>
          <span>AI-Powered Student Career Journey</span>
        </div>
        <p className="text-xs">
          Pakistan-focused career realities & actionable student guidance.
        </p>
      </div>
    </footer>
  )
}
