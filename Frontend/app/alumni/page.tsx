"use client"

import React from "react"
import { TalkToAlumniSection } from "@/components/alumni/TalkToAlumniSection"
import { PageTransition } from "@/components/layout/PageTransition"
import Link from "next/link"
import { ArrowLeft, Users } from "lucide-react"

export default function AlumniPage() {
  return (
    <PageTransition>
      <div className="bg-[#05080E] min-h-screen pt-12 pb-24">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 space-y-8">
          <div className="flex items-center gap-2">
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Home</span>
            </Link>
          </div>

          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-1.5 text-xs font-bold tracking-widest text-indigo-400 uppercase">
              <Users className="h-3.5 w-3.5" />
              <span>Community & Mentorship</span>
            </div>
            <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
              Talk to <span className="text-indigo-400">Alumni</span>
            </h1>
            <p className="text-slate-400 max-w-2xl text-lg">
              Learn directly from graduates who have taken the path you are exploring across Pakistani universities.
            </p>
          </div>

          <div className="pt-4">
            <TalkToAlumniSection />
          </div>
        </div>
      </div>
    </PageTransition>
  )
}
