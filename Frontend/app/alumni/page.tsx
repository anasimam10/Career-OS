"use client"

import React, { useState } from "react"
import { PageTransition } from "@/components/layout/PageTransition"
import Link from "next/link"
import { ArrowLeft, Clock, ShieldCheck, GraduationCap, CheckCircle2 } from "lucide-react"

export default function AlumniPage() {
  const [email, setEmail] = useState("")
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (email.trim()) {
      setSubmitted(true)
    }
  }

  return (
    <PageTransition>
      <div className="bg-[#0B0F1A] min-h-screen pt-12 pb-24 text-[#F1F5F9]">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 space-y-8">
          <div>
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-sm text-[#94A3B8] hover:text-[#F1F5F9] transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Home</span>
            </Link>
          </div>

          <div className="space-y-4">


            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F1F5F9]">
              Talk to Alumni
            </h1>

            <p className="text-[#94A3B8] text-base sm:text-lg max-w-2xl leading-relaxed">
              Connect with graduates from Pakistani universities for advice on admissions, campus culture, and early careers.
            </p>
          </div>

          {/* Status Panel */}
          <div className="rounded-xl border border-[#1E2D42] bg-[#111827] p-6 sm:p-8 space-y-6">


            <p className="text-[#94A3B8] text-sm leading-relaxed">
              We are building a verified alumni network.
            </p>

            <div className="grid sm:grid-cols-2 gap-4 pt-2">
              <div className="rounded-lg border border-[#1E2D42] bg-[#1C2539]/50 p-4 space-y-1.5">
                <div className="flex items-center gap-2 text-[#3B82F6] font-medium text-sm">
                  <ShieldCheck className="h-4 w-4" />
                  <span>Verified Degrees</span>
                </div>
                <p className="text-xs text-[#94A3B8] leading-relaxed">
                  Graduates from recognized Pakistani institutions including NUST, FAST, LUMS, IBA, and GIKI.
                </p>
              </div>

              <div className="rounded-lg border border-[#1E2D42] bg-[#1C2539]/50 p-4 space-y-1.5">
                <div className="flex items-center gap-2 text-[#3B82F6] font-medium text-sm">
                  <GraduationCap className="h-4 w-4" />
                  <span>Candid Advice</span>
                </div>
                <p className="text-xs text-[#94A3B8] leading-relaxed">
                  Direct guidance on entrance test preparation, career realities, and campus transitions.
                </p>
              </div>
            </div>

            {/* Optional Notify Me */}
            <div className="pt-4 border-t border-[#1E2D42]">
              {submitted ? (
                <div className="inline-flex items-center gap-2 text-sm text-[#10B981] font-medium">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Thanks! We&apos;ll notify you when the alumni network is ready.</span>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter email for launch updates"
                    className="flex-1 bg-[#1C2539] border border-[#1E2D42] rounded-lg px-3.5 py-2 text-sm text-[#F1F5F9] placeholder:text-[#4B5563] focus:outline-none focus:border-[#2563EB]"
                    required
                  />
                  <button
                    type="submit"
                    className="px-4 py-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white rounded-lg text-sm font-semibold transition-colors"
                  >
                    Notify me
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  )
}

