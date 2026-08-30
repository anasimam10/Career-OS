"use client"

import Link from "next/link"
import {
  MessageSquare,
  Target,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Compass,
  ArrowUpRight,
  TrendingUp,
  MapPin,
} from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ProgressBar } from "@/components/shared/ProgressBar"

export function FeaturesSection() {
  const suggestedQuestions = [
    "What career fits my interests?",
    "Should I choose Computer Science?",
    "What should I do next?",
    "Am I ready for an internship?",
  ]

  const journeyStages = [
    { label: "Discover", active: false },
    { label: "Reality Check", active: false },
    { label: "Decide", active: true, current: true },
    { label: "Build", active: false },
    { label: "Experience", active: false },
    { label: "Get Hired", active: false },
  ]

  return (
    <div className="space-y-24 max-w-6xl mx-auto px-4 sm:px-6 py-12">
      {/* ── 1. AI MENTOR SHOWCASE (TOP PRIORITY) ─────────────────────────── */}
      <section className="rounded-3xl border-2 border-primary/20 bg-gradient-to-b from-primary/5 via-background to-card p-6 sm:p-10 shadow-sm">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8">
          <div className="space-y-4 max-w-xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
              <Sparkles className="h-3.5 w-3.5" />
              <span>CORE FEATURE</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
              YOUR AI CAREER MENTOR
            </h2>
            <p className="text-muted-foreground text-sm sm:text-base leading-relaxed">
              Ask about your career options, your current situation, or what you should focus on next. Your mentor uses your journey context to make guidance actionable and relevant.
            </p>

            <div className="space-y-2 pt-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block">
                Try asking questions like:
              </span>
              <div className="flex flex-wrap gap-2">
                {suggestedQuestions.map((q, idx) => (
                  <Link
                    key={idx}
                    href={`/mentor?prompt=${encodeURIComponent(q)}`}
                    className="inline-flex items-center gap-1 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground hover:border-primary hover:text-primary transition-all active:scale-95 shadow-sm"
                  >
                    <span>{q}</span>
                    <ArrowUpRight className="h-3 w-3 text-muted-foreground" />
                  </Link>
                ))}
              </div>
            </div>

            <div className="pt-4">
              <Button asChild size="lg" className="gap-2 shadow-md">
                <Link href="/mentor">
                  <MessageSquare className="h-4 w-4" />
                  <span>Talk to AI Mentor</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>

          {/* Interactive Chat Preview Card */}
          <div className="w-full lg:w-[420px] rounded-2xl border border-border bg-card shadow-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary text-white font-bold text-xs">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-foreground">AI Career Mentor</h4>
                  <span className="text-[10px] text-emerald-600 font-medium">● Connected to your journey</span>
                </div>
              </div>
              <Badge variant="outline" className="text-[10px]">Real-time</Badge>
            </div>

            <div className="space-y-3 text-xs">
              <div className="rounded-2xl rounded-tr-sm bg-primary text-primary-foreground p-3 ml-auto max-w-[85%] font-medium">
                I&apos;m in 2nd year CS at university. What should my focus be right now?
              </div>
              <div className="rounded-2xl rounded-tl-sm bg-muted/70 text-foreground p-3.5 mr-auto max-w-[90%] space-y-2 leading-relaxed border border-border/50">
                <p>
                  You&apos;re in the <strong>Build</strong> phase. Rather than learning 5 languages, focus on completing <strong>one end-to-end project</strong> using Python or Node.js.
                </p>
                <div className="rounded-xl bg-card p-2.5 border border-border/80 text-[11px] text-foreground font-semibold flex items-center justify-between">
                  <span>Suggested Next Action: Build REST API</span>
                  <ArrowRight className="h-3 w-3 text-primary" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 2. CAREER REALITY CHECK SHOWCASE ─────────────────────────────── */}
      <section className="space-y-8">
        <div className="max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-3 py-1 text-xs font-bold text-amber-700">
            <Target className="h-3.5 w-3.5" />
            <span>REALITY-CHECKED GUIDANCE</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
            BEFORE YOU CHOOSE A CAREER, <br className="hidden sm:inline" />
            <span className="text-primary">REALITY-CHECK IT.</span>
          </h2>
          <p className="text-muted-foreground text-sm sm:text-base leading-relaxed">
            Popularity does not automatically make a career right for you. Understand demand, competition, difficulty, Pakistan-specific opportunities, risks, rewards, and how the field aligns with your profile.
          </p>
        </div>

        {/* Live Reality Check Preview Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Metrics Preview */}
          <div className="lg:col-span-2 grid grid-cols-2 gap-4">
            <div className="rounded-2xl border border-border bg-card p-4 space-y-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Market Demand
              </span>
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold text-foreground">High</span>
                <Badge variant="high">High Demand</Badge>
              </div>
              <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                <div className="h-full bg-rose-500 w-4/5" />
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-card p-4 space-y-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Admission Competition
              </span>
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold text-foreground">Very High</span>
                <Badge variant="high">Top 5%</Badge>
              </div>
              <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                <div className="h-full bg-rose-500 w-full" />
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-card p-4 space-y-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Learning Difficulty
              </span>
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold text-foreground">Medium–High</span>
                <Badge variant="medium">Math & Logic</Badge>
              </div>
              <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                <div className="h-full bg-amber-500 w-2/3" />
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-card p-4 space-y-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Pakistan Opportunity
              </span>
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold text-foreground">Strong</span>
                <Badge variant="success">Local & Remote</Badge>
              </div>
              <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                <div className="h-full bg-emerald-500 w-4/5" />
              </div>
            </div>
          </div>

          {/* AI Verdict Card */}
          <Card className="border-2 border-primary/20 bg-gradient-to-b from-primary/5 to-card flex flex-col justify-between">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  AI Career Verdict
                </span>
                <Badge variant="warning">WORTH EXPLORING</Badge>
              </div>
              <CardTitle className="text-xl font-bold mt-2">
                Software Engineering
              </CardTitle>
              <CardDescription className="text-xs leading-relaxed text-foreground/80 mt-1">
                Your profile shows strong interest in technology, but salary and peer influence are also driving your interest. Test it for 7 days before fully committing.
              </CardDescription>
            </CardHeader>
            <CardFooter className="pt-2">
              <Button asChild className="w-full gap-2" size="sm">
                <Link href="/careers/software-engineering/reality-check">
                  <span>Run Full Reality Check</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </Button>
            </CardFooter>
          </Card>
        </div>
      </section>

      {/* ── 3. MOTIVATION & WHY THIS FIELD ───────────────────────────────── */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center rounded-3xl border border-border bg-muted/20 p-6 sm:p-10">
        <div className="space-y-4">
          <Badge variant="outline" className="text-xs font-bold">
            MOTIVATION REFLECTION
          </Badge>
          <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
            WHY ARE YOU CONSIDERING THIS FIELD?
          </h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Students often pick careers under family or social pressure without testing real interest. Our AI reflects your honest drivers back to you.
          </p>
          <p className="text-xs text-muted-foreground italic border-l-2 border-primary pl-3">
            * AI reflection based on your onboarding answers (not a clinical or psychological diagnosis).
          </p>
        </div>

        <div className="rounded-2xl border border-border bg-card p-5 space-y-3.5 shadow-sm">
          <ProgressBar label="Genuine Interest" value={80} color="emerald" sublabel="Primary Driver" />
          <ProgressBar label="Salary Expectations" value={60} color="primary" />
          <ProgressBar label="Peer Influence" value={40} color="amber" />
          <ProgressBar label="Family Expectations" value={20} color="rose" />
        </div>
      </section>

      {/* ── 4. NEXT BEST ACTION (ONE NEXT STEP) ─────────────────────────── */}
      <section className="space-y-6">
        <div className="max-w-2xl space-y-2">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-700">
            <Clock className="h-3.5 w-3.5" />
            <span>ONE STUDENT. ONE DIRECTION. ONE NEXT STEP.</span>
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight text-foreground">
            YOUR NEXT ACTION
          </h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            You don&apos;t need to figure out your entire 5-year career right now. Just complete your single immediate action.
          </p>
        </div>

        <div className="rounded-3xl border-2 border-primary bg-card p-6 sm:p-8 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-3 max-w-xl">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-primary animate-ping" />
              <Badge variant="default">Immediate Priority</Badge>
              <span className="text-xs text-muted-foreground">3–4 hours this week</span>
            </div>
            <h3 className="text-2xl font-bold text-foreground">
              Build Your Python Fundamentals
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              <strong>Why this matters:</strong> This supports the software engineering path you&apos;re currently exploring and gives you the core foundation needed for subsequent milestones.
            </p>
          </div>

          <Button asChild size="lg" className="w-full md:w-auto gap-2 shrink-0">
            <Link href="/journey">
              <span>Start Step</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>

      {/* ── 5. STUDENT JOURNEY PATHWAY ───────────────────────────────────── */}
      <section className="rounded-3xl border border-border bg-card p-6 sm:p-10 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-foreground">
              Your End-to-End Journey
            </h3>
            <p className="text-xs text-muted-foreground">
              A structured progression from school to your first job in Pakistan
            </p>
          </div>
          <Button asChild variant="outline" size="sm">
            <Link href="/journey">View Full Journey</Link>
          </Button>
        </div>

        {/* Stage Nodes */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          {journeyStages.map((stage, idx) => (
            <div
              key={idx}
              className={`flex flex-col items-center justify-center p-3.5 rounded-2xl border text-center transition-all ${
                stage.current
                  ? "border-primary bg-primary/10 text-primary font-bold shadow-sm ring-2 ring-primary/20"
                  : "border-border bg-muted/30 text-muted-foreground font-medium"
              }`}
            >
              <span className="text-[10px] font-bold text-muted-foreground uppercase">
                Stage {idx + 1}
              </span>
              <span className="text-xs mt-1">{stage.label}</span>
              {stage.current && (
                <span className="mt-1.5 inline-block text-[9px] bg-primary text-white font-semibold px-2 py-0.5 rounded-full">
                  You are here
                </span>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ── 6. CAREER EXPLORATION GRID PREVIEW ───────────────────────────── */}
      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold text-foreground">
              Explore Verified Careers
            </h3>
            <p className="text-xs text-muted-foreground">
              Browse data on engineering, healthcare, technology, and business
            </p>
          </div>
          <Button asChild variant="ghost" size="sm" className="gap-1 text-primary">
            <Link href="/careers">
              <span>View All Careers</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          <Card className="hover:shadow-card-hover transition-all">
            <CardHeader className="p-5">
              <div className="flex justify-between items-center mb-2">
                <Badge variant="outline" className="text-[10px]">Technology</Badge>
                <Badge variant="high" className="text-[10px]">High Demand</Badge>
              </div>
              <CardTitle className="text-base font-bold">Software Engineering</CardTitle>
              <CardDescription className="text-xs mt-1">
                Growing tech sector with high remote and domestic opportunities.
              </CardDescription>
            </CardHeader>
            <CardFooter className="p-5 pt-0">
              <Button asChild variant="outline" size="sm" className="w-full text-xs">
                <Link href="/careers/software-engineering/reality-check">Run Reality Check</Link>
              </Button>
            </CardFooter>
          </Card>

          <Card className="hover:shadow-card-hover transition-all">
            <CardHeader className="p-5">
              <div className="flex justify-between items-center mb-2">
                <Badge variant="outline" className="text-[10px]">Technology</Badge>
                <Badge variant="high" className="text-[10px]">High Demand</Badge>
              </div>
              <CardTitle className="text-base font-bold">Data Science</CardTitle>
              <CardDescription className="text-xs mt-1">
                High demand in Pakistani banking, telecom, and fintech analytics.
              </CardDescription>
            </CardHeader>
            <CardFooter className="p-5 pt-0">
              <Button asChild variant="outline" size="sm" className="w-full text-xs">
                <Link href="/careers/data-science/reality-check">Run Reality Check</Link>
              </Button>
            </CardFooter>
          </Card>

          <Card className="hover:shadow-card-hover transition-all">
            <CardHeader className="p-5">
              <div className="flex justify-between items-center mb-2">
                <Badge variant="outline" className="text-[10px]">Healthcare</Badge>
                <Badge variant="high" className="text-[10px]">High Demand</Badge>
              </div>
              <CardTitle className="text-base font-bold">Medicine (MBBS)</CardTitle>
              <CardDescription className="text-xs mt-1">
                Rigorous path with high demand in public and private health sectors.
              </CardDescription>
            </CardHeader>
            <CardFooter className="p-5 pt-0">
              <Button asChild variant="outline" size="sm" className="w-full text-xs">
                <Link href="/careers/medicine/reality-check">Run Reality Check</Link>
              </Button>
            </CardFooter>
          </Card>
        </div>
      </section>
    </div>
  )
}
