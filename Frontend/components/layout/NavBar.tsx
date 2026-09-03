"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Map, MessageSquare, Sparkles, Target, Trophy, Briefcase, ClipboardCheck, ArrowRight, User } from "lucide-react"
import { cn } from "@/lib/utils/cn"
import { isOnboardingComplete, getSession } from "@/lib/session"

const navItems = [
  { href: "/", label: "Home", icon: Sparkles },
  { href: "/careers", label: "Careers", icon: Target },
  { href: "/journey", label: "Journey", icon: Map },
  { href: "/opportunities", label: "Opportunities", icon: Briefcase },
  { href: "/sports", label: "Sports", icon: Trophy },
  { href: "/job-readiness", label: "Job Ready", icon: ClipboardCheck },
  { href: "/mock-interview", label: "Mock Interview", icon: ClipboardCheck },
]

export function NavBar() {
  const pathname = usePathname()
  const [onboarded, setOnboarded] = useState(false)
  const [userInitial, setUserInitial] = useState<string | null>(null)

  useEffect(() => {
    setOnboarded(isOnboardingComplete())
    const session = getSession()
    if (session?.student_id) {
      setUserInitial(session.name ? session.name[0].toUpperCase() : "S")
    }
  }, [pathname])

  return (
    <React.Fragment>
      {/* Top Navbar for Desktop */}
      <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-[#05080E]/90 backdrop-blur-md supports-[backdrop-filter]:bg-[#05080E]/70">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white font-bold text-sm shadow-[0_0_15px_rgba(79,70,229,0.3)] transition-transform group-hover:scale-105">
              OS
            </div>
            <div className="flex flex-col hidden sm:flex">
              <span className="font-bold tracking-tight text-white text-base leading-none">
                Career OS
              </span>
              <span className="text-[10px] text-indigo-300 font-medium leading-tight mt-0.5 tracking-wider uppercase">
                Premium Engine
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-1 bg-slate-900/50 rounded-full p-1 border border-slate-800">
            {navItems.map((item) => {
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 rounded-full px-4 py-2 text-xs font-bold transition-all",
                    isActive
                      ? "bg-slate-800 text-white shadow-sm"
                      : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
                  )}
                >
                  <Icon className={cn("h-3.5 w-3.5", isActive ? "text-indigo-400" : "opacity-70")} />
                  {item.label}
                </Link>
              )
            })}
          </nav>

          <div className="flex items-center gap-4">
            {onboarded ? (
              <div className="flex items-center gap-3">
                <Link
                  href="/mentor"
                  className="hidden sm:flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-2 text-xs font-bold text-indigo-300 transition hover:bg-indigo-500/20"
                >
                  <MessageSquare className="h-3.5 w-3.5" />
                  Qwen Mentor
                </Link>
                <Link
                  href="/profile"
                  className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700 transition"
                  title="Your Profile"
                >
                  {userInitial ? (
                    <span className="text-xs font-bold">{userInitial}</span>
                  ) : (
                    <User className="h-4 w-4" />
                  )}
                </Link>
              </div>
            ) : (
              <Link
                href="/onboarding"
                className="hidden sm:inline-flex items-center gap-2 rounded-full bg-white px-5 py-2 text-xs font-bold text-slate-950 transition-all hover:bg-slate-100 hover:scale-105"
              >
                Start Profile
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Mobile Bottom Navigation Bar */}
      <nav className="md:hidden fixed bottom-0 left-0 z-50 w-full border-t border-slate-800 bg-[#05080E]/90 backdrop-blur-lg supports-[backdrop-filter]:bg-[#05080E]/70 pb-safe">
        <div className="flex h-16 items-center justify-around px-2">
          {(onboarded
            ? [
                { href: "/careers", label: "Careers", icon: Target },
                { href: "/journey", label: "Journey", icon: Map },
                { href: "/opportunities", label: "Opps", icon: Briefcase },
                { href: "/mock-interview", label: "Interview", icon: ClipboardCheck },
                { href: "/profile", label: "Profile", icon: User },
              ]
            : navItems.slice(0, 5)
          ).map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors",
                  isActive ? "text-indigo-400" : "text-slate-500 hover:text-slate-300"
                )}
              >
                <div className={cn(
                  "p-1.5 rounded-xl transition-colors",
                  isActive && "bg-indigo-500/10"
                )}>
                  <Icon className={cn("h-5 w-5", isActive && "stroke-[2.5px]")} />
                </div>
                <span className="text-[10px] font-semibold">{item.label}</span>
              </Link>
            )
          })}
        </div>
      </nav>
    </React.Fragment>
  )
}
