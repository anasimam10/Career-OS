import type { OnboardingResponse } from "@/lib/types/student.types"
import { MOCK_NBA } from "./journey.mock"

export const MOCK_ONBOARDING_RESPONSE: OnboardingResponse = {
  profile_updated: true,
  next_best_action: MOCK_NBA,
}

export const INTEREST_OPTIONS = [
  "Technology", "Mathematics", "Biology", "Physics", "Chemistry",
  "Literature", "History", "Art & Design", "Music", "Business",
  "Economics", "Psychology", "Sports", "Cooking", "Environment",
]

export const CAREER_FIELD_OPTIONS = [
  "Software Engineering", "Medicine", "Business", "Engineering",
  "Design", "Data Science", "Teaching", "Law", "Finance", "Marketing",
  "Not sure yet",
]

export const MOTIVATION_OPTIONS = [
  "I genuinely love this subject",
  "High salary potential",
  "Job security",
  "Family expectations",
  "Peer influence",
  "Want to help people",
  "Creative expression",
  "Entrepreneurship",
]

export const SPORTS_OPTIONS = [
  "Cricket", "Football", "Badminton", "Hockey", "Tennis",
  "Squash", "Swimming", "Basketball", "Volleyball", "Athletics",
  "No sport",
]

export const FUTURE_GOAL_OPTIONS = [
  "Work at a top company in Pakistan",
  "Start my own business",
  "Work remotely for international companies",
  "Serve Pakistan through public sector",
  "Get a scholarship and study abroad",
  "Become financially independent quickly",
  "Make a positive social impact",
]

export const EDUCATION_STAGE_OPTIONS = [
  { value: "HIGH_SCHOOL", label: "O-Level / Matric" },
  { value: "HIGH_SCHOOL", label: "A-Level / Intermediate" },
  { value: "UNIVERSITY", label: "First Year University" },
  { value: "UNIVERSITY", label: "Second Year University" },
  { value: "UNIVERSITY", label: "Third Year University" },
  { value: "FINAL_YEAR", label: "Final Year University" },
  { value: "CAREER_DISCOVERY", label: "Just finished studies" },
]
