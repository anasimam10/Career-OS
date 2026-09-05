/**
 * Session abstraction for Career OS.
 * All student identity access goes through this module.
 * Persists student identity in browser localStorage without hardcoding demo student id=1.
 */

export const STUDENT_ID_KEY = "career_os_student_id"
export const SESSION_KEY = "ah_careers_session"
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
    if (!raw) {
      // Fallback: build minimal session from career_os_student_id if present
      const directId = localStorage.getItem(STUDENT_ID_KEY)
      if (directId && !isNaN(Number(directId)) && Number(directId) > 0) {
        return {
          student_id: Number(directId),
          name: DEMO_STUDENT_NAME,
          onboarding_completed: true,
        }
      }
      return null
    }
    return JSON.parse(raw) as Session
  } catch {
    return null
  }
}

export function getOrCreateSession(): Session {
  const existing = getSession()
  if (existing) return existing
  
  if (process.env.NEXT_PUBLIC_USE_MOCK !== "true") {
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
  try {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session))
    if (session.student_id > 0) {
      localStorage.setItem(STUDENT_ID_KEY, String(session.student_id))
    }
  } catch (e) {
    console.error("Error setting session in localStorage:", e)
  }
}

export function updateSession(updates: Partial<Session>): void {
  const current = getSession()
  if (!current) {
    if (process.env.NEXT_PUBLIC_USE_MOCK !== "true") {
      console.warn("Attempting to update session without an existing student identity in real mode.")
      return
    }
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
  if (typeof window !== "undefined") {
    try {
      localStorage.setItem(STUDENT_ID_KEY, String(studentId))
    } catch (e) {
      console.error("Failed to store career_os_student_id in localStorage", e)
    }
  }
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
  try {
    localStorage.removeItem(STUDENT_ID_KEY)
    localStorage.removeItem(SESSION_KEY)
  } catch (e) {
    console.error("Error clearing session:", e)
  }
}

export function isOnboardingComplete(): boolean {
  if (typeof window === "undefined") return false
  const directId = localStorage.getItem(STUDENT_ID_KEY)
  if (directId && !isNaN(Number(directId)) && Number(directId) > 0) {
    return true
  }
  return getSession()?.onboarding_completed ?? false
}

export function getStudentId(): number | null {
  if (typeof window === "undefined") return null
  try {
    const directId = localStorage.getItem(STUDENT_ID_KEY)
    if (directId && !isNaN(Number(directId)) && Number(directId) > 0) {
      return Number(directId)
    }
    const session = getSession()
    if (session?.student_id && session.student_id > 0) {
      return session.student_id
    }
    return null
  } catch {
    return null
  }
}

export function getEffectiveStudentId(): number {
  const sid = getStudentId()
  if (sid) return sid
  if (process.env.NEXT_PUBLIC_USE_MOCK === "true") {
    return DEMO_STUDENT_ID
  }
  return 0 
}

