"use client"

import React, { useState, useEffect } from "react"
import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Map,
  Target,
  Briefcase,
  ClipboardCheck,
  ArrowRight,
  User,
  Menu,
  X,
  MessageSquare,
  Users,
  Trophy,
} from "lucide-react"
import { cn } from "@/lib/utils/cn"
import { isOnboardingComplete, getSession } from "@/lib/session"

interface NavItem {
  href: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
}

// Primary navigation links: Careers | My Journey | Opportunities | Job Readiness | Mock Interview | Alumni
const primaryNavItems: NavItem[] = [
  { href: "/careers", label: "Careers", icon: Target },
  { href: "/journey", label: "My Journey", icon: Map },
  { href: "/opportunities", label: "Opportunities", icon: Briefcase },
  { href: "/job-readiness", label: "Job Readiness", icon: ClipboardCheck },
  { href: "/mock-interview", label: "Mock Interview", icon: ClipboardCheck },
  { href: "/alumni", label: "Alumni", icon: Users },
]

// Secondary links available in mobile menu & footer
const secondaryNavItems: NavItem[] = [
  { href: "/sports", label: "Sports Pathway", icon: Trophy },
]

export function NavBar() {
  const pathname = usePathname()
  const [onboarded, setOnboarded] = useState(false)
  const [userInitial, setUserInitial] = useState<string | null>(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    setOnboarded(isOnboardingComplete())
    const session = getSession()
    if (session?.student_id) {
      setUserInitial(session.name ? session.name[0].toUpperCase() : "S")
    }
  }, [pathname])

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false)
  }, [pathname])

  return (
    <header className="sticky top-0 z-50 w-full border-b border-[#2A3650] bg-[#0B0F1A]/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1100px] items-center justify-between px-4 sm:px-6">
        {/* Logo Branding (Serves as Home) */}
        <Link href="/" className="flex items-center gap-2.5 shrink-0 group">
          <div className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-full overflow-hidden shadow-sm transition-transform group-hover:scale-105">
            <Image
              src="/images/career-os-logo.png"
              alt="Career OS"
              width={32}
              height={32}
              priority
              className="h-8 w-8 rounded-full object-contain"
            />
          </div>
          <div className="flex flex-col">
            <span className="font-bold tracking-tight text-[#F1F5F9] text-base leading-none">
              Career OS
            </span>
            <span className="text-[10px] text-[#60A5FA] font-medium leading-tight mt-0.5 tracking-wider">
              For Pakistani Students
            </span>
          </div>
        </Link>

        {/* Desktop Primary Navigation (6 Links: Careers, Journey, Opportunities, Job Readiness, Mock Interview, Alumni) */}
        <nav className="hidden md:flex items-center gap-1 bg-[#111827] rounded-full px-2 py-1 border border-[#2A3650]">
          {primaryNavItems.map((item) => {
            const isActive =
              pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-colors",
                  isActive
                    ? "bg-[#1C2539] text-[#F1F5F9] border border-[#2A3650]"
                    : "text-[#94A3B8] hover:bg-[#1C2539]/60 hover:text-[#F1F5F9]"
                )}
              >
                <Icon
                  className={cn(
                    "h-3.5 w-3.5 shrink-0",
                    isActive ? "text-[#3B82F6]" : "text-[#64748B]"
                  )}
                />
                <span>{item.label}</span>
                {item.badge && (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/20">
                    {item.badge}
                  </span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Right Desktop CTA Action */}
        <div className="hidden md:flex items-center gap-3 shrink-0">
          {onboarded ? (
            <div className="flex items-center gap-2.5">
              <Link
                href="/mentor"
                className="flex items-center gap-1.5 rounded-full border border-[#3B82F6]/30 bg-[#3B82F6]/10 px-3 py-1.5 text-xs font-semibold text-[#60A5FA] hover:bg-[#3B82F6]/20 transition"
              >
                <MessageSquare className="h-3.5 w-3.5 text-[#3B82F6] shrink-0" />
                <span>Qwen Mentor</span>
              </Link>
              <Link
                href="/profile"
                className="flex h-8 w-8 items-center justify-center rounded-full bg-[#1C2539] text-[#F1F5F9] border border-[#2A3650] hover:border-[#3B82F6] transition"
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
              className="inline-flex items-center gap-2 rounded-[6px] bg-[#2563EB] hover:bg-[#1D4ED8] px-4 py-2 text-xs font-bold text-white transition-all shadow-sm"
            >
              <span>Create Profile</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          )}
        </div>

        {/* Mobile Hamburger Button (<768px, tap target >= 44x44px) */}
        <div className="flex items-center md:hidden">
          <button
            type="button"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            className="flex h-11 w-11 items-center justify-center rounded-[6px] border border-[#2A3650] bg-[#111827] text-[#F1F5F9] hover:bg-[#1C2539] transition-colors"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu Overlay */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#2A3650] bg-[#0B0F1A] px-4 pt-2 pb-6 space-y-2">
          <div className="space-y-1">
            {primaryNavItems.map((item) => {
              const isActive =
                pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-[8px] px-3.5 min-h-[44px] text-sm font-semibold transition-colors",
                    isActive
                      ? "bg-[#111827] text-[#F1F5F9] border border-[#2A3650]"
                      : "text-[#94A3B8] hover:bg-[#111827] hover:text-[#F1F5F9]"
                  )}
                >
                  <Icon
                    className={cn(
                      "h-4 w-4 shrink-0",
                      isActive ? "text-[#3B82F6]" : "text-[#64748B]"
                    )}
                  />
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="ml-auto inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/20">
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </div>

          {/* Secondary links divider */}
          <div className="pt-2 border-t border-[#2A3650]/80 space-y-1">
            {secondaryNavItems.map((item) => {
              const isActive = pathname.startsWith(item.href)
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-[8px] px-3.5 min-h-[44px] text-sm font-medium transition-colors",
                    isActive
                      ? "bg-[#111827] text-[#F1F5F9] border border-[#2A3650]"
                      : "text-[#94A3B8] hover:bg-[#111827] hover:text-[#F1F5F9]"
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0 text-[#64748B]" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>

          {/* Mobile CTA */}
          <div className="pt-3">
            <Link
              href="/onboarding"
              className="flex items-center justify-center gap-2 rounded-[6px] bg-[#2563EB] hover:bg-[#1D4ED8] min-h-[44px] px-4 text-sm font-bold text-white transition-all shadow-md w-full"
            >
              <span>Create Profile</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      )}
    </header>
  )
}
