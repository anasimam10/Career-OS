"use client"

import React, { useEffect } from "react"
import { MapPin, Building, Globe } from "lucide-react"

export interface Step2LocationProps {
  province: string
  city: string
  onProvinceChange: (province: string) => void
  onCityChange: (city: string) => void
}

export const PROVINCES_MAP: Record<string, string[]> = {
  "Sindh": [
    "Karachi",
    "Hyderabad",
    "Sukkur",
    "Larkana",
    "Mirpur Khas",
    "Nawabshah",
    "Other (Sindh)",
  ],
  "Punjab": [
    "Lahore",
    "Faisalabad",
    "Rawalpindi",
    "Multan",
    "Gujranwala",
    "Sialkot",
    "Bahawalpur",
    "Sargodha",
    "Gujrat",
    "Sahiwal",
    "Rahim Yar Khan",
    "Other (Punjab)",
  ],
  "Islamabad Capital Territory": [
    "Islamabad",
  ],
  "KPK": [
    "Peshawar",
    "Abbottabad",
    "Mardan",
    "Swat",
    "Kohat",
    "Dera Ismail Khan",
    "Haripur",
    "Other (KPK)",
  ],
  "Balochistan": [
    "Quetta",
    "Gwadar",
    "Turbat",
    "Khuzdar",
    "Sibi",
    "Other (Balochistan)",
  ],
  "Azad Jammu & Kashmir (AJK)": [
    "Muzaffarabad",
    "Mirpur",
    "Rawalakot",
    "Other (AJK)",
  ],
  "Gilgit-Baltistan": [
    "Gilgit",
    "Skardu",
    "Other (Gilgit-Baltistan)",
  ],
}

export const PROVINCE_KEYS = Object.keys(PROVINCES_MAP)

export function Step2Location({
  province,
  city,
  onProvinceChange,
  onCityChange,
}: Step2LocationProps) {
  const currentProvince = province || "Sindh"
  const availableCities = PROVINCES_MAP[currentProvince] || PROVINCES_MAP["Sindh"]

  // Synchronize city if current city is not in the province's list
  useEffect(() => {
    if (!availableCities.includes(city)) {
      onCityChange(availableCities[0])
    }
  }, [currentProvince, availableCities, city, onCityChange])

  const handleProvinceSelect = (newProv: string) => {
    onProvinceChange(newProv)
    const newCities = PROVINCES_MAP[newProv] || []
    if (newCities.length > 0) {
      onCityChange(newCities[0])
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#1E2D42] bg-[#111827] text-xs font-semibold text-[#60A5FA] mb-3">
          <Globe className="h-3.5 w-3.5" />
          <span>Step 2: Location</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F1F5F9]">
          Where are you based?
        </h2>
        <p className="mt-2 text-sm text-[#94A3B8]">
          Opportunities, university admissions, and local industry salaries are localized to your province and city.
        </p>
      </div>

      <div className="space-y-5 pt-2">
        {/* Controlled Province Dropdown */}
        <div className="space-y-2">
          <label htmlFor="province-select" className="flex items-center gap-2 text-sm font-semibold text-[#F1F5F9]">
            <Building className="h-4 w-4 text-[#3B82F6]" />
            <span>Province</span>
          </label>
          <div className="relative">
            <select
              id="province-select"
              value={currentProvince}
              onChange={(e) => handleProvinceSelect(e.target.value)}
              className="w-full h-12 px-4 rounded-[10px] border border-[#2A3650] bg-[#111827] text-[#F1F5F9] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6] transition-colors appearance-none cursor-pointer"
            >
              {PROVINCE_KEYS.map((p) => (
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

        {/* Controlled Dependent City Dropdown */}
        <div className="space-y-2">
          <label htmlFor="city-select" className="flex items-center gap-2 text-sm font-semibold text-[#F1F5F9]">
            <MapPin className="h-4 w-4 text-[#3B82F6]" />
            <span>City</span>
          </label>
          <div className="relative">
            <select
              id="city-select"
              value={city || availableCities[0]}
              onChange={(e) => onCityChange(e.target.value)}
              className="w-full h-12 px-4 rounded-[10px] border border-[#2A3650] bg-[#111827] text-[#F1F5F9] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6] transition-colors appearance-none cursor-pointer"
            >
              {availableCities.map((c) => (
                <option key={c} value={c} className="bg-[#111827] text-[#F1F5F9]">
                  {c}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-[#94A3B8]">
              ▼
            </div>
          </div>
          <p className="text-xs text-[#64748B]">
            Cities dynamically correspond to your selected province for verified Pakistani regional intelligence.
          </p>
        </div>
      </div>
    </div>
  )
}
