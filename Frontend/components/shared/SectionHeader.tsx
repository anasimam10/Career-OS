import React from "react"
import { cn } from "@/lib/utils/cn"

interface SectionHeaderProps {
  title: string
  subtitle?: string
  badge?: string
  className?: string
  level?: "h1" | "h2"
}

export function SectionHeader({
  title,
  subtitle,
  badge,
  className,
  level = "h1",
}: SectionHeaderProps) {
  const HeadingTag = level
  return (
    <div className={cn("flex flex-col space-y-2 mb-6", className)}>
      {badge && (
        <span className="inline-flex w-fit items-center rounded-full bg-[#3B82F6]/10 px-3 py-1 text-xs font-semibold text-[#60A5FA] uppercase tracking-wider">
          {badge}
        </span>
      )}
      <HeadingTag className="text-3xl font-extrabold tracking-tight text-[#F1F5F9] sm:text-4xl">
        {title}
      </HeadingTag>
      {subtitle && (
        <p className="text-base text-[#94A3B8] max-w-2xl leading-relaxed">
          {subtitle}
        </p>
      )}
    </div>
  )
}
