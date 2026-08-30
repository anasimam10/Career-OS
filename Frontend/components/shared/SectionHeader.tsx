import { cn } from "@/lib/utils/cn"

interface SectionHeaderProps {
  title: string
  subtitle?: string
  badge?: string
  className?: string
}

export function SectionHeader({
  title,
  subtitle,
  badge,
  className,
}: SectionHeaderProps) {
  return (
    <div className={cn("flex flex-col space-y-2 mb-6", className)}>
      {badge && (
        <span className="inline-flex w-fit items-center rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary uppercase tracking-wider">
          {badge}
        </span>
      )}
      <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
        {title}
      </h2>
      {subtitle && (
        <p className="text-base text-muted-foreground max-w-2xl leading-relaxed">
          {subtitle}
        </p>
      )}
    </div>
  )
}
