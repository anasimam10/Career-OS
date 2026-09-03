/**
 * Session abstraction for Career OS.
 * All student identity access goes through this module.
 * Persists student identity in browser localStorage without hardcoding demo student id=1.
 */

const SESSION_KEY = "ah_careers_session"
export const DEMO_STUDENT_ID = 1
const DEMO_STUDENT_NAME = "Student"

export interface Session {
  student_id: number
  name: string
  onboarding_completed: boolean
  city?: string
}

export function getSession(): Session | null {
  if (typeof window === "undefined") return null
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) return null
    return JSON.parse(raw) as Session
  } catch {
    return null
  }
}

export function getOrCreateSession(): Session {
  const existing = getSession()
  if (existing) return existing
  
  if (process.env.NEXT_PUBLIC_USE_MOCK !== "true") {
    // In real mode, we don't return Demo Student 1 automatically.
    // Instead return a null-equivalent stub session so app redirects to onboarding
    return {
      student_id: 0,
      name: "",
      onboarding_completed: false,
    }
  }

  const session: Session = {
    student_id: DEMO_STUDENT_ID,
    name: DEMO_STUDENT_NAME,
    onboarding_completed: false,
  }
  setSession(session)
  return session
}

export function setSession(session: Session): void {
  if (typeof window === "undefined") return
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

export function updateSession(updates: Partial<Session>): void {
  const current = getSession()
  if (!current) {
    if (process.env.NEXT_PUBLIC_USE_MOCK !== "true") {
      console.warn("Attempting to update session without an existing student identity in real mode.")
      return
    }
    // Explicit mock-only fallback
    setSession({
      student_id: DEMO_STUDENT_ID,
      name: DEMO_STUDENT_NAME,
      onboarding_completed: false,
      ...updates,
    })
    return
  }
  setSession({ ...current, ...updates })
}

export function saveNewStudentSession(studentId: number, name: string = "Student", city?: string): Session {
  const session: Session = {
    student_id: studentId,
    name: name,
    onboarding_completed: true,
    city: city,
  }
  setSession(session)
  return session
}

export function clearSession(): void {
  if (typeof window === "undefined") return
  localStorage.removeItem(SESSION_KEY)
}

export function isOnboardingComplete(): boolean {
  return getSession()?.onboarding_completed ?? false
}

export function getStudentId(): number | null {
  return getSession()?.student_id ?? null
}

export function getEffectiveStudentId(): number {
  const sid = getSession()?.student_id
  if (sid) return sid
  if (process.env.NEXT_PUBLIC_USE_MOCK === "true") {
    return DEMO_STUDENT_ID
  }
  // In real mode, a missing session means the user needs to onboard.
  // Returning 0 or throwing could break SSR, but returning a non-existent ID 
  // explicitly prevents mixing up with Demo Student 1.
  return 0 
}

