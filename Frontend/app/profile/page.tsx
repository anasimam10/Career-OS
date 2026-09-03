"use client"

import { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import {
  User,
  MapPin,
  GraduationCap,
  Target,
  Trophy,
  Sparkles,
  Edit3,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Compass,
  Briefcase,
  X,
  Save,
  Activity,
} from "lucide-react"
import { PageTransition } from "@/components/layout/PageTransition"
import { LoadingState } from "@/components/shared/LoadingState"
import { ErrorState } from "@/components/shared/ErrorState"
import { getStudentProfile, updateStudentProfile, type StudentProfileData } from "@/lib/api/students"
import { isOnboardingComplete, getSession, clearSession } from "@/lib/session"

const CITIES = ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Peshawar", "Quetta", "Multan", "Faisalabad"]
const STAGES = [
  { value: "HIGH_SCHOOL", label: "High School (Matric / O-Levels)" },
  { value: "CAREER_DISCOVERY", label: "Intermediate / A-Levels" },
  { value: "UNIVERSITY", label: "University (Bachelors)" },
  { value: "SKILL_BUILDING", label: "Skill Building & Projects" },
  { value: "JOB_PREPARATION", label: "Final Year / Job Prep" },
]
const SPORTS = ["No sport", "Cricket", "Football", "Badminton", "Hockey", "Tennis", "Squash", "Swimming", "Basketball"]

export default function ProfilePage() {
  const [profile, setProfile] = useState<StudentProfileData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Edit form state
  const [editName, setEditName] = useState("")
  const [editCity, setEditCity] = useState("")
  const [editStage, setEditStage] = useState("")
  const [editGoal, setEditGoal] = useState("")
  const [editSport, setEditSport] = useState("")
  const [newMotivationTag, setNewMotivationTag] = useState("")
  const [editMotivations, setEditMotivations] = useState<string[]>([])

  const loadProfile = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getStudentProfile()
      setProfile(data)
      setEditName(data.name || "")
      setEditCity(data.city || "")
      setEditStage(data.education_stage || "HIGH_SCHOOL")
      setEditGoal(data.career_goal || "")
      setEditSport(data.sports_interest || "No sport")
      setEditMotivations(data.motivation_tags || [])
    } catch (err: any) {
      // If student not found or session stale, purge session and clear profile
      if (err?.statusCode === 404 || (err?.message && (err.message.includes("404") || err.message.includes("not found")))) {
        clearSession()
      }
      setProfile(null)
      setError(err instanceof Error ? err.message : "Failed to load profile")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSaving(true)
      const updated = await updateStudentProfile({
        name: editName,
        city: editCity,
        education_stage: editStage,
        career_goal: editGoal,
        sports_interest: editSport === "No sport" ? undefined : editSport,
        motivation_tags: editMotivations,
      })
      setProfile(updated)
      setEditing(false)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to update profile")
    } finally {
      setSaving(false)
    }
  }

  const addMotivationTag = () => {
    const trimmed = newMotivationTag.trim()
    if (trimmed && !editMotivations.includes(trimmed)) {
      setEditMotivations([...editMotivations, trimmed])
      setNewMotivationTag("")
    }
  }

  const removeMotivationTag = (tag: string) => {
    setEditMotivations(editMotivations.filter((t) => t !== tag))
  }

  return (
    <PageTransition>
      <div className="bg-[#05080E] min-h-screen pt-12 pb-24 relative overflow-hidden">
        {/* Background ambience */}
        <div className="absolute top-0 right-1/4 w-[600px] h-[600px] bg-indigo-500/5 blur-[160px] rounded-full pointer-events-none" />

        <div className="mx-auto max-w-5xl px-4 sm:px-6 space-y-10 relative z-10">
          
          {loading ? (
            <div className="pt-20">
              <LoadingState message="Loading your student profile..." />
            </div>
          ) : !profile ? (
            /* Un-onboarded Empty State */
            <div className="relative rounded-[2rem] border border-slate-800 bg-slate-900/40 p-8 sm:p-16 text-center shadow-2xl space-y-6 max-w-xl mx-auto mt-12 backdrop-blur-sm">
              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Compass className="h-10 w-10 animate-pulse-slow" />
              </div>
              <div className="space-y-3">
                <h1 className="text-3xl font-extrabold text-white">No Student Profile Found</h1>
                <p className="text-slate-400 text-sm leading-relaxed">
                  You have not enrolled in Career OS yet. Complete the onboarding wizard to receive your personalized roadmap and verified Pakistani career intelligence.
                </p>
              </div>
              <div className="pt-2">
                <Link
                  href="/onboarding"
                  className="inline-flex items-center gap-2 rounded-full bg-white px-8 py-3.5 text-sm font-bold text-slate-950 hover:bg-slate-200 transition-all hover:scale-105"
                >
                  Start Onboarding
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          ) : error && !profile ? (
            <div className="pt-20">
              <ErrorState message={error} onRetry={loadProfile} />
            </div>
          ) : profile ? (
            <>
              {/* Top Banner / Hero Card */}
              <div className="rounded-[2.5rem] border border-slate-800 bg-slate-900/50 p-8 sm:p-10 backdrop-blur-md shadow-2xl relative overflow-hidden">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                  <div className="flex items-center gap-5">
                    <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-indigo-600/20 border border-indigo-500/40 text-indigo-400 shadow-[0_0_25px_rgba(99,102,241,0.25)]">
                      <span className="text-3xl font-black">{profile.name ? profile.name[0].toUpperCase() : "S"}</span>
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-3">
                        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">{profile.name}</h1>
                        <span className="inline-flex items-center gap-1 rounded-full border border-green-500/30 bg-green-500/10 px-2.5 py-0.5 text-[10px] font-bold text-green-400 uppercase tracking-wider">
                          <ShieldCheck className="h-3 w-3" />
                          Enrolled
                        </span>
                      </div>
                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                        <span>{profile.email}</span>
                        <span>•</span>
                        <span className="font-mono text-indigo-400">ID: #{profile.id}</span>
                        {profile.city && (
                          <>
                            <span>•</span>
                            <span className="flex items-center gap-1 text-slate-300">
                              <MapPin className="h-3 w-3 text-indigo-400" />
                              {profile.city}, Pakistan
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setEditing(true)}
                      className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-xs font-bold text-white transition hover:bg-slate-700 hover:border-slate-600"
                    >
                      <Edit3 className="h-3.5 w-3.5 text-indigo-400" />
                      Edit Profile
                    </button>
                    <Link
                      href="/journey"
                      className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-bold text-white transition hover:bg-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.3)]"
                    >
                      View Journey
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                </div>

                {saveSuccess && (
                  <div className="mt-6 flex items-center gap-2 rounded-xl border border-green-500/30 bg-green-500/10 px-4 py-2 text-xs font-medium text-green-300">
                    <CheckCircle2 className="h-4 w-4 text-green-400" />
                    Profile updated successfully!
                  </div>
                )}
              </div>

              {/* Grid of Profile Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* 1. Academic & Geographic Focus */}
                <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-sm space-y-4">
                  <div className="flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-wider">
                    <GraduationCap className="h-4 w-4" />
                    Education & Location
                  </div>
                  <div className="space-y-3 pt-1">
                    <div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider">Current Education Stage</div>
                      <div className="text-base font-semibold text-white mt-0.5">{profile.education_stage.replace(/_/g, " ")}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider">City in Pakistan</div>
                      <div className="text-base font-semibold text-white mt-0.5">{profile.city || "Not specified"}</div>
                    </div>
                  </div>
                </div>

                {/* 2. Target Career & Motivations */}
                <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-sm space-y-4">
                  <div className="flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-wider">
                    <Target className="h-4 w-4" />
                    Career Direction
                  </div>
                  <div className="space-y-3 pt-1">
                    <div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider">Primary Career Goal</div>
                      <div className="text-base font-semibold text-white mt-0.5 capitalize">
                        {profile.career_goal ? profile.career_goal.replace(/-/g, " ") : "Undecided"}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider mb-1.5">Motivations</div>
                      <div className="flex flex-wrap gap-1.5">
                        {profile.motivation_tags && profile.motivation_tags.length > 0 ? (
                          profile.motivation_tags.map((tag, idx) => (
                            <span key={idx} className="rounded-md border border-slate-700 bg-slate-800/60 px-2.5 py-1 text-xs text-slate-300">
                              {tag}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-slate-500 italic">No motivation tags recorded</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 3. Core Competencies & Skills */}
                <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-sm space-y-4">
                  <div className="flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-wider">
                    <Briefcase className="h-4 w-4" />
                    Skills & Competencies
                  </div>
                  <div className="pt-1">
                    {profile.skills && profile.skills.length > 0 ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {profile.skills.map((s, idx) => (
                          <div key={idx} className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-800/40 px-3 py-2 text-xs">
                            <span className="font-medium text-slate-200">{s.name}</span>
                            <span className="text-[10px] font-bold uppercase text-indigo-400">{s.level}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="text-xs text-slate-500 italic">No skills recorded yet.</span>
                    )}
                  </div>
                </div>

                {/* 4. Athletic / Sports Pathway */}
                <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-sm space-y-4">
                  <div className="flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-wider">
                    <Trophy className="h-4 w-4" />
                    Sports Pathway
                  </div>
                  <div className="space-y-3 pt-1">
                    <div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider">Registered Sport</div>
                      <div className="text-base font-semibold text-white mt-0.5">
                        {profile.sports_interest && profile.sports_interest !== "No sport"
                          ? profile.sports_interest
                          : "No sports pathway selected"}
                      </div>
                    </div>
                    {profile.sports_interest && profile.sports_interest !== "No sport" && (
                      <Link
                        href="/sports"
                        className="inline-flex items-center gap-1.5 text-xs font-semibold text-amber-400 hover:text-amber-300 transition"
                      >
                        Explore trials & academy openings in {profile.sports_interest}
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    )}
                  </div>
                </div>

                {/* 5. Readiness & Milestones */}
                <div className="md:col-span-2 rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-sm space-y-4">
                  <div className="flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-wider">
                    <Activity className="h-4 w-4" />
                    Career OS Intelligence Status
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-2">
                    <div className="rounded-xl border border-slate-800 bg-slate-800/40 p-4">
                      <div className="text-xs text-slate-500 uppercase tracking-wider">Job Readiness Indicator</div>
                      <div className="text-2xl font-black text-white mt-1">
                        {Math.round((profile.job_readiness_score || 0) * 100)}%
                      </div>
                      <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden mt-2">
                        <div
                          className="h-full bg-indigo-500"
                          style={{ width: `${Math.round((profile.job_readiness_score || 0) * 100)}%` }}
                        />
                      </div>
                    </div>

                    <div className="rounded-xl border border-slate-800 bg-slate-800/40 p-4">
                      <div className="text-xs text-slate-500 uppercase tracking-wider">Completed Milestones</div>
                      <div className="text-2xl font-black text-white mt-1">
                        {profile.completed_milestone_ids ? profile.completed_milestone_ids.length : 0}
                      </div>
                      <p className="text-[11px] text-slate-500 mt-1">Tracked in your active roadmap</p>
                    </div>

                    <div className="rounded-xl border border-slate-800 bg-slate-800/40 p-4">
                      <div className="text-xs text-slate-500 uppercase tracking-wider">Active Next Best Action</div>
                      <div className="text-sm font-semibold text-white mt-1 line-clamp-1">
                        {profile.next_best_action?.title || "Continue current roadmap milestone"}
                      </div>
                      <Link
                        href="/journey"
                        className="inline-flex items-center gap-1 text-[11px] font-bold text-indigo-400 mt-2 hover:text-indigo-300"
                      >
                        Go to Action Card
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    </div>
                  </div>
                </div>

              </div>
            </>
          ) : null}

          {/* Edit Profile Modal */}
          {editing && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
              <div className="relative w-full max-w-lg rounded-3xl border border-slate-700 bg-slate-900 p-6 sm:p-8 shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <h2 className="text-xl font-bold text-white">Edit Your Profile</h2>
                  <button
                    onClick={() => setEditing(false)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                <form onSubmit={handleSave} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">Name</label>
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-700 bg-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">City in Pakistan</label>
                    <select
                      value={editCity}
                      onChange={(e) => setEditCity(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-700 bg-slate-800 text-sm text-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="">Select your city</option>
                      {CITIES.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">Education Stage</label>
                    <select
                      value={editStage}
                      onChange={(e) => setEditStage(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-700 bg-slate-800 text-sm text-white focus:outline-none focus:border-indigo-500"
                    >
                      {STAGES.map((s) => (
                        <option key={s.value} value={s.value}>{s.label}</option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">Primary Career Goal</label>
                    <input
                      type="text"
                      value={editGoal}
                      onChange={(e) => setEditGoal(e.target.value)}
                      placeholder="e.g. software-engineering, accounting-finance"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-700 bg-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">Sports Pathway</label>
                    <select
                      value={editSport}
                      onChange={(e) => setEditSport(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-700 bg-slate-800 text-sm text-white focus:outline-none focus:border-indigo-500"
                    >
                      {SPORTS.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">Motivations</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={newMotivationTag}
                        onChange={(e) => setNewMotivationTag(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addMotivationTag() } }}
                        placeholder="Add motivation tag..."
                        className="flex-1 px-3.5 py-2 rounded-xl border border-slate-700 bg-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                      <button
                        type="button"
                        onClick={addMotivationTag}
                        className="px-3 py-2 rounded-xl bg-indigo-600 text-xs font-bold text-white hover:bg-indigo-500 transition"
                      >
                        Add
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1.5 pt-1.5">
                      {editMotivations.map((tag) => (
                        <span key={tag} className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-slate-300">
                          {tag}
                          <button
                            type="button"
                            onClick={() => removeMotivationTag(tag)}
                            className="text-slate-500 hover:text-red-400"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                    <button
                      type="button"
                      onClick={() => setEditing(false)}
                      className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={saving}
                      className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-indigo-500 transition shadow-[0_0_15px_rgba(99,102,241,0.3)] disabled:opacity-50"
                    >
                      <Save className="h-3.5 w-3.5" />
                      {saving ? "Saving..." : "Save Changes"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

        </div>
      </div>
    </PageTransition>
  )
}
