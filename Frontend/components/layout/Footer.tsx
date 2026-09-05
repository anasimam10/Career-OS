import React from "react"
import Link from "next/link"

export function Footer() {
  return (
    <footer className="border-t border-[#1E2D42] bg-[#0B0F1A] py-12 text-[#94A3B8]">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 flex flex-col md:flex-row items-center justify-between gap-6 text-sm">
        {/* Brand & Mission */}
        <div className="space-y-1 text-center md:text-left">
          <p className="font-bold text-[#F1F5F9] text-base tracking-tight">Career OS</p>
          <p className="text-xs text-[#94A3B8]">
            Pakistan&apos;s career operating system for students.
          </p>
        </div>

        {/* Navigation Links */}
        <div className="flex flex-col items-center md:items-end gap-2 text-xs">
          <nav className="flex flex-wrap items-center justify-center gap-5 font-semibold text-[#94A3B8]">
            <Link href="/careers" className="hover:text-[#F1F5F9] transition-colors">
              Careers
            </Link>
            <Link href="/journey" className="hover:text-[#F1F5F9] transition-colors">
              My Journey
            </Link>
            <Link href="/opportunities" className="hover:text-[#F1F5F9] transition-colors">
              Opportunities
            </Link>
            <Link href="/job-readiness" className="hover:text-[#F1F5F9] transition-colors">
              Job Readiness
            </Link>
            <Link href="/mock-interview" className="hover:text-[#F1F5F9] transition-colors">
              Mock Interview
            </Link>
            <Link href="/sports" className="hover:text-[#F1F5F9] transition-colors">
              Sports
            </Link>
          </nav>
          <div className="flex items-center gap-4 text-[#64748B]">
            <Link href="/alumni" className="hover:text-[#94A3B8] transition-colors">
              Alumni (Coming Soon)
            </Link>
          </div>
        </div>

        {/* Copyright */}
        <div className="text-xs text-[#64748B] text-center md:text-right">
          © 2026 Career OS
        </div>
      </div>
    </footer>
  )
}
