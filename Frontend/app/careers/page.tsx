"use client"

import React, { useState, useEffect, useCallback } from "react"
import { Search, RefreshCw } from "lucide-react"
import { getCareers } from "@/lib/api/careers"
import { CareerCard } from "@/components/career/CareerCard"
import { PageTransition } from "@/components/layout/PageTransition"
import type { CareerListItem } from "@/lib/types/career.types"
import { cn } from "@/lib/utils/cn"

export default function CareersPage() {
  const [careers, setCareers] = useState<CareerListItem[]>([])
  const [search, setSearch] = useState("")
  const [selectedField, setSelectedField] = useState<string>("All")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const list = await getCareers()
      setCareers(list)
    } catch {
      setError("Couldn't load careers right now.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const fields = ["All", ...Array.from(new Set(careers.map((c) => c.field)))]

  const filtered = careers.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.field.toLowerCase().includes(search.toLowerCase())
    const matchesField = selectedField === "All" || c.field === selectedField
    return matchesSearch && matchesField
  })

  return (
    <PageTransition>
      <div className="bg-[#0B0F1A] min-h-screen pt-10 pb-24 text-[#F1F5F9]">
        <div className="mx-auto max-w-[1100px] px-4 sm:px-6 space-y-10">
          {/* Header */}
          <div className="space-y-2">
            <span className="text-xs font-medium tracking-wider text-[#94A3B8] uppercase">
              Careers
            </span>
            <h1 className="text-3xl md:text-5xl font-extrabold text-[#F1F5F9] tracking-tight">
              Explore Careers in Pakistan
            </h1>
          </div>

          {/* Search & Field Filters */}
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-[#111827] p-4 rounded-[12px] border border-[#1E2D42]">
            <div className="relative w-full md:max-w-md">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#94A3B8]" />
              <input
                type="text"
                placeholder="Search careers or fields..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-[#0B0F1A] border border-[#1E2D42] text-[#F1F5F9] rounded-[8px] pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-[#2563EB] transition-colors placeholder:text-[#4B5563]"
              />
            </div>

            <div className="flex flex-wrap gap-1.5 w-full md:w-auto justify-start md:justify-end">
              {fields.map((f) => (
                <button
                  key={f}
                  onClick={() => setSelectedField(f)}
                  className={cn(
                    "rounded-[6px] px-3 py-1.5 text-xs font-semibold transition-colors",
                    selectedField === f
                      ? "bg-[#2563EB] text-white"
                      : "bg-[#1C2539] text-[#94A3B8] hover:text-[#F1F5F9]"
                  )}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {/* Data State */}
          {loading ? (
            /* Skeleton Loading State: 6 cards */
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 pt-2" aria-busy="true">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div
                  key={i}
                  className="h-56 rounded-[12px] border border-[#1E2D42] bg-[#111827] p-6 animate-pulse flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="h-3.5 w-24 bg-[#1C2539] rounded" />
                    <div className="h-5 w-4/5 bg-[#1C2539] rounded" />
                    <div className="h-3.5 w-full bg-[#1C2539] rounded" />
                  </div>
                  <div className="h-9 w-full bg-[#1C2539] rounded-[6px]" />
                </div>
              ))}
            </div>
          ) : error ? (
            /* Error State with Retry */
            <div className="text-center py-16 space-y-4 rounded-2xl border border-rose-900/40 bg-rose-950/20 p-8 max-w-md mx-auto">
              <p className="text-sm text-[#F1F5F9] font-medium">{error}</p>
              <div>
                <button
                  type="button"
                  onClick={load}
                  className="inline-flex items-center gap-2 rounded-[8px] border border-[#2A3A54] bg-[#111827] hover:bg-[#1C2539] px-4 py-2 text-xs font-semibold text-[#F1F5F9] transition-colors"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>Retry</span>
                </button>
              </div>
            </div>
          ) : filtered.length === 0 ? (
            /* Empty State */
            <div className="text-center py-16 space-y-2 rounded-2xl border border-[#1E2D42] bg-[#111827] p-8 max-w-md mx-auto">
              <p className="text-base font-semibold text-[#F1F5F9]">No careers found.</p>
              <p className="text-xs text-[#94A3B8]">Try a different filter or search keyword.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {filtered.map((career) => (
                <CareerCard key={career.slug} career={career} />
              ))}
            </div>
          )}
        </div>
      </div>
    </PageTransition>
  )
}
