import Link from "next/link"
import { ArrowRight, TrendingUp } from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { CareerListItem } from "@/lib/types/career.types"

export function CareerCard({ career }: { career: CareerListItem }) {
  const demandVariant =
    career.demand_level === "HIGH"
      ? "high"
      : career.demand_level === "MEDIUM"
      ? "medium"
      : "low"

  return (
    <Card className="flex flex-col justify-between hover:shadow-card-hover transition-all border-border/80 group">
      <CardHeader>
        <div className="flex items-center justify-between gap-2 mb-2">
          <Badge variant="outline" className="text-[11px]">
            {career.field}
          </Badge>
          <Badge variant={demandVariant} className="text-[11px] font-semibold">
            {career.demand_level} Demand
          </Badge>
        </div>
        <CardTitle className="text-xl group-hover:text-primary transition-colors">
          {career.name}
        </CardTitle>
        <CardDescription>
          Explore verified realities, top Pakistani universities, and day-to-day requirements.
        </CardDescription>
      </CardHeader>
      <CardFooter className="pt-0">
        <Button asChild variant="outline" size="sm" className="w-full justify-between group-hover:border-primary/50">
          <Link href={`/careers/${career.slug}/reality-check`}>
            <span>Run Reality Check</span>
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  )
}
