"use client"

import React from "react"
import { MapPin, Building, Target } from "lucide-react"

export interface Step2LocationProps {
  city: string
  province: string
  targetField: string
  onCityChange: (city: string) => void
  onProvinceChange: (province: string) => void
  onTargetFieldChange: (field: string) => void
}

export const CITIES = [
  "Karachi",
  "Lahore",
  "Islamabad",
  "Rawalpindi",
  "Faisalabad",
  "Multan",
  "Peshawar",
  "Quetta",
  "Sialkot",
  "Gujranwala",
  "Hyderabad",
  "Abbottabad",
  "Other",
]

export const PROVINCES = [
  "Punjab",
  "Sindh",
  "KPK",
  "Balochistan",
  "AJK",
  "Gilgit-Baltistan",
]

export const TARGET_FIELDS = [
  "Software Engineering",
  "Medicine",
  "Business",
  "Engineering",
  "Design",
  "Data Science",
  "Teaching",
  "Law",
  "Finance",
  "Marketing",
  "I'm not sure yet",
]

export function Step2Location({
  city,
  province,
  targetField,
  onCityChange,
  onProvinceChange,
  onTargetFieldChange,
}: Step2LocationProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#F1F5F9]">
          Where are you based and what interests you?
        </h2>
        <p className="mt-2 text-sm text-[#94A3B8]">
          We use this to surface nearby university campuses, verified internships, and matching career intelligence.
        </p>
      </div>

      <div className="space-y-5 pt-2">
        {/* City Dropdown */}
        <div className="space-y-2">
          <label htmlFor="city-select" className="flex items-center gap-2 text-sm font-semibold text-[#F1F5F9]">
            <MapPin className="h-4 w-4 text-[#3B82F6]" />
            <span>City</span>
          </label>
          <div className="relative">
            <select
              id="city-select"
              value={city || "Karachi"}
              onChange={(e) => onCityChange(e.target.value)}
              className="w-full h-12 px-4 rounded-[8px] border border-[#2A3650] bg-[#111827] text-[#F1F5F9] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6] transition-colors appearance-none cursor-pointer"
            >
              {CITIES.map((c) => (
                <option key={c} value={c} className="bg-[#111827] text-[#F1F5F9]">
                  {c}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-[#94A3B8]">
              ▼
            </div>
          </div>
        </div>

        {/* Province Dropdown */}
        <div className="space-y-2">
          <label htmlFor="province-select" className="flex items-center gap-2 text-sm font-semibold text-[#F1F5F9]">
            <Building className="h-4 w-4 text-[#3B82F6]" />
            <span>Province</span>
          </label>
          <div className="relative">
            <select
              id="province-select"
              value={province || "Sindh"}
              onChange={(e) => onProvinceChange(e.target.value)}
              className="w-full h-12 px-4 rounded-[8px] border border-[#2A3650] bg-[#111827] text-[#F1F5F9] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6] transition-colors appearance-none cursor-pointer"
            >
              {PROVINCES.map((p) => (
                <option key={p} value={p} className="bg-[#111827] text-[#F1F5F9]">
                  {p}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-[#94A3B8]">
              ▼
            </div>
          </div>
        </div>

        {/* Target Field Dropdown */}
        <div className="space-y-2">
          <label htmlFor="field-select" className="flex items-center gap-2 text-sm font-semibold text-[#F1F5F9]">
            <Target className="h-4 w-4 text-[#3B82F6]" />
            <span>Target Field <span className="text-[#64748B] font-normal">(Optional)</span></span>
          </label>
          <div className="relative">
            <select
              id="field-select"
              value={targetField || "I'm not sure yet"}
              onChange={(e) => onTargetFieldChange(e.target.value)}
              className="w-full h-12 px-4 rounded-[8px] border border-[#2A3650] bg-[#111827] text-[#F1F5F9] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6] transition-colors appearance-none cursor-pointer"
            >
              {TARGET_FIELDS.map((f) => (
                <option key={f} value={f} className="bg-[#111827] text-[#F1F5F9]">
                  {f}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-[#94A3B8]">
              ▼
            </div>
          </div>
          <p className="text-xs text-[#64748B]">
            All preset options ensure clean matching against Pakistan labour data.
          </p>
        </div>
      </div>
    </div>
  )
}
