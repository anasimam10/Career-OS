import React from "react"
import Link from "next/link"

export function Footer() {
  return (
    <footer className="border-t border-[#2A3650] bg-[#0B0F1A] py-12 text-[#94A3B8]">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 flex flex-col md:flex-row items-center justify-between gap-6 text-sm">
        {/* Brand & Mission */}
        <div className="space-y-1 text-center md:text-left">
          <p className="font-bold text-[#F1F5F9] text-base">Career OS</p>
          <p className="text-xs text-[#64748B]">Built for Pakistani students.</p>
        </div>

        {/* Minimal Navigation Links */}
        <nav className="flex flex-wrap items-center justify-center gap-6 text-xs font-semibold">
          <Link href="/careers" className="hover:text-[#F1F5F9] transition-colors">
            Explore Careers
          </Link>
          <Link href="/journey" className="hover:text-[#F1F5F9] transition-colors">
            My Journey
          </Link>
          <Link href="/opportunities" className="hover:text-[#F1F5F9] transition-colors">
            Opportunities
          </Link>
          <Link href="/sports" className="hover:text-[#F1F5F9] transition-colors">
            Sports
          </Link>
          <Link href="/alumni" className="hover:text-[#F1F5F9] transition-colors">
            Talk to Alumni
          </Link>
        </nav>

        {/* Copyright & Legal */}
        <div className="text-xs text-[#64748B] text-center md:text-right">
          © 2026 Antigravity · Privacy · Terms
        </div>
      </div>
    </footer>
  )
}
