"use client"

import { useState, useEffect } from "react"
import { Search } from "lucide-react"
import { getCareers } from "@/lib/api/careers"
import { CareerCard } from "@/components/career/CareerCard"
import { SectionHeader } from "@/components/shared/SectionHeader"
import { LoadingState } from "@/components/shared/LoadingState"
import { ErrorState } from "@/components/shared/ErrorState"
import { EmptyState } from "@/components/shared/EmptyState"
import { Input } from "@/components/ui/input"
import { PageTransition } from "@/components/layout/PageTransition"
import type { CareerListItem } from "@/lib/types/career.types"

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
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10 space-y-8">
        <SectionHeader
          badge="Discovery"
          title="Explore Careers in Pakistan"
          subtitle="Explore demand, real market competition, and academic routes for careers in Pakistan."
        />

        {/* Search & Field Filters */}
        <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="relative w-full sm:max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search careers or fields (e.g. Software, Healthcare)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="flex flex-wrap gap-2 w-full sm:w-auto">
            {fields.map((f) => (
              <button
                key={f}
                onClick={() => setSelectedField(f)}
                className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition-all ${
                  selectedField === f
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <LoadingState message="Loading careers database..." />
        ) : error ? (
          <ErrorState message={error} />
        ) : filtered.length === 0 ? (
          <EmptyState
            title="No matching careers found"
            description="Try adjusting your search keywords or filter to find what you're looking for."
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((career) => (
              <CareerCard key={career.slug} career={career} />
            ))}
          </div>
        )}
      </div>
    </PageTransition>
  )
}
