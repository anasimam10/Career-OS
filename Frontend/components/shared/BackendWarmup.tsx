"use client"

import { useEffect } from "react"

export function BackendWarmup() {
  useEffect(() => {
    // Silent ping to prevent cold-start delay on Render
    const apiBase =
      process.env.NEXT_PUBLIC_API_BASE_URL || "https://ah-career-backend.onrender.com"
    fetch(`${apiBase}/health`, {
      method: "GET",
      cache: "no-store",
    }).catch(() => {}) // intentionally silent
  }, [])

  return null
}
