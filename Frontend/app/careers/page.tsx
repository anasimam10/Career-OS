"use client"

import { useState, useEffect } from "react"
import { Search, Compass } from "lucide-react"
import { getCareers } from "@/lib/api/careers"
import { CareerCard } from "@/components/career/CareerCard"
import { LoadingState } from "@/components/shared/LoadingState"
import { ErrorState } from "@/components/shared/ErrorState"
import { EmptyState } from "@/components/shared/EmptyState"
import { PageTransition } from "@/components/layout/PageTransition"
import type { CareerListItem } from "@/lib/types/career.types"
import { cn } from "@/lib/utils/cn"

export default function CareersPage() {
  const [careers, setCareers] = useState<CareerListItem[]>([])
  const [search, setSearch] = useState("")
  const [selectedField, setSelectedField] = useState<string>("All")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        const list = await getCareers()
        setCareers(list)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load careers")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

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
      <div className="bg-[#05080E] min-h-screen pt-12 pb-24 relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute top-0 right-1/4 w-[500px] h-[500px] bg-indigo-500/10 blur-[150px] rounded-full pointer-events-none" />

        <div className="mx-auto max-w-7xl px-4 sm:px-6 space-y-12 relative z-10">
          
          <div className="text-center space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-1.5 text-xs font-bold tracking-widest text-indigo-400 uppercase">
              <Compass className="h-3.5 w-3.5" />
              <span>Career Database</span>
            </div>
            <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
              Explore Careers in <span className="text-indigo-400">Pakistan</span>
            </h1>
            <p className="text-slate-400 max-w-2xl mx-auto text-lg">
              Explore demand, real market competition, and verified academic routes for careers in Pakistan.
            </p>
          </div>

          {/* Search & Field Filters */}
          <div className="flex flex-col md:flex-row gap-6 items-center justify-between bg-slate-900/60 p-4 sm:p-6 rounded-3xl border border-slate-800 backdrop-blur-md">
            <div className="relative w-full md:max-w-md">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
              <input
                type="text"
                placeholder="Search careers or fields..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-xl pl-12 pr-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all placeholder:text-slate-500"
              />
            </div>

            <div className="flex flex-wrap gap-2 w-full md:w-auto justify-center md:justify-end">
              {fields.map((f) => (
                <button
                  key={f}
                  onClick={() => setSelectedField(f)}
                  className={cn(
                    "rounded-xl px-4 py-2 text-xs font-bold uppercase tracking-wider transition-all",
                    selectedField === f
                      ? "bg-indigo-600 text-white shadow-[0_0_15px_rgba(79,70,229,0.4)]"
                      : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white"
                  )}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="pt-12"><LoadingState message="Loading careers database..." /></div>
          ) : error ? (
            <div className="pt-12"><ErrorState message={error} /></div>
          ) : filtered.length === 0 ? (
            <div className="pt-12">
              <EmptyState
                title="No matching careers found"
                description="Try adjusting your search keywords or filter to find what you're looking for."
              />
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
