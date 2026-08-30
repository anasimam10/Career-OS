"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Compass, Map, MessageSquare, Sparkles, Target, Trophy, Briefcase, ClipboardCheck } from "lucide-react"
import { cn } from "@/lib/utils/cn"

const navItems = [
  { href: "/", label: "Home", icon: Sparkles },
  { href: "/careers", label: "Careers", icon: Target },
  { href: "/journey", label: "Journey", icon: Map },
  { href: "/opportunities", label: "Opportunities", icon: Briefcase },
  { href: "/sports", label: "Sports", icon: Trophy },
  { href: "/job-readiness", label: "Job Ready", icon: ClipboardCheck },
]

export function NavBar() {
  const pathname = usePathname()

  return (
    <>
      {/* Top Navbar for Desktop */}
      <header className="sticky top-0 z-50 w-full border-b border-border/60 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-blue-600 text-white font-bold text-sm shadow-sm transition-transform group-hover:scale-105">
              A&H
            </div>
            <div className="flex flex-col">
              <span className="font-bold tracking-tight text-foreground text-base leading-none">
                A&H Careers
              </span>
              <span className="text-[10px] text-muted-foreground font-medium leading-tight mt-0.5">
                AI Student Career Journey
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href)

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 rounded-xl px-3.5 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary/10 text-primary font-semibold"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              )
            })}
          </nav>

          <div className="flex items-center gap-3">
            <Link
              href="/mentor"
              className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 transition-all hover:scale-[1.02]"
            >
              <MessageSquare className="h-3.5 w-3.5" />
              <span>Talk to AI Mentor</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Mobile Bottom Navigation Bar */}
      <div className="fixed bottom-0 left-0 z-50 w-full border-t border-border bg-background/95 backdrop-blur md:hidden">
        <nav className="flex h-16 items-center justify-around px-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href)

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex flex-col items-center justify-center gap-1 rounded-lg px-2.5 py-1 text-[11px] font-medium transition-colors",
                  isActive
                    ? "text-primary font-bold"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Icon className={cn("h-4 w-4", isActive ? "stroke-[2.5]" : "")} />
                <span className="text-[10px] whitespace-nowrap">{item.label}</span>
              </Link>
            )
          })}
        </nav>
      </div>
    </>
  )
}
