"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Map,
  MessageSquare,
  Sparkles,
  Target,
  Trophy,
  Briefcase,
  ClipboardCheck,
  ArrowRight,
  User,
  Users
} from "lucide-react"
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
  { href: "/alumni", label: "Talk to Alumni", icon: Users },
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
        <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between px-4 sm:px-6 lg:px-8 gap-4">
          
          {/* Logo Branding */}
          <Link href="/" className="flex items-center gap-2.5 shrink-0 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600 text-white font-bold text-xs shadow-[0_0_15px_rgba(79,70,229,0.35)] transition-transform group-hover:scale-105">
              OS
            </div>
            <div className="flex flex-col hidden sm:flex">
              <span className="font-bold tracking-tight text-white text-sm leading-none">
                Career OS
              </span>
              <span className="text-[9px] text-indigo-300/80 font-medium leading-tight mt-0.5 tracking-wider uppercase">
                Premium Engine
              </span>
            </div>
          </Link>

          {/* Center Navigation Pill Container */}
          <nav className="hidden lg:flex items-center gap-0.5 xl:gap-1 bg-slate-900/60 rounded-full p-1 border border-slate-800/80 shadow-inner">
            {navItems.map((item) => {
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-1.5 rounded-full px-2.5 xl:px-3 py-1.5 text-xs font-medium whitespace-nowrap transition-all duration-150",
                    isActive
                      ? "bg-slate-800 text-white font-semibold shadow-sm border border-slate-700/60 shadow-black/40"
                      : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                  )}
                >
                  <Icon className={cn("h-3.5 w-3.5 shrink-0", isActive ? "text-indigo-400" : "text-slate-500")} />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>

          {/* Right Action Group */}
          <div className="flex items-center gap-3 shrink-0">
            {onboarded ? (
              <div className="flex items-center gap-2.5">
                <Link
                  href="/mentor"
                  className="flex items-center gap-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1.5 text-xs font-semibold text-indigo-300 transition hover:bg-indigo-500/20 whitespace-nowrap"
                >
                  <MessageSquare className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                  <span>Qwen Mentor</span>
                </Link>
                <Link
                  href="/profile"
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700 hover:text-white transition shrink-0"
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
                className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-1.5 text-xs font-bold text-slate-950 transition-all hover:bg-slate-100 hover:scale-105 whitespace-nowrap shadow-sm"
              >
                <span>Start Profile</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Mobile Bottom Navigation Bar */}
      <nav className="lg:hidden fixed bottom-0 left-0 z-50 w-full border-t border-slate-800 bg-[#05080E]/90 backdrop-blur-lg supports-[backdrop-filter]:bg-[#05080E]/70 pb-safe">
        <div className="flex h-16 items-center justify-around px-2">
          {(onboarded
            ? [
                { href: "/careers", label: "Careers", icon: Target },
                { href: "/journey", label: "Journey", icon: Map },
                { href: "/opportunities", label: "Opps", icon: Briefcase },
                { href: "/alumni", label: "Alumni", icon: Users },
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
