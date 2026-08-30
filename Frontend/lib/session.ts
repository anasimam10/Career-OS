/**
 * Session abstraction for Phase 1 mock session.
 * All student identity access must go through this module.
 * When real JWT auth is added, only this file needs to change.
 */

const SESSION_KEY = "ah_careers_session"
const DEMO_STUDENT_ID = 1
const DEMO_STUDENT_NAME = "Demo Student"

export interface Session {
  student_id: number
  name: string
  onboarding_completed: boolean
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
  const current = getOrCreateSession()
  setSession({ ...current, ...updates })
}

export function clearSession(): void {
  if (typeof window === "undefined") return
  localStorage.removeItem(SESSION_KEY)
}

export function isOnboardingComplete(): boolean {
  return getSession()?.onboarding_completed ?? false
}

export function getStudentId(): number {
  return getOrCreateSession().student_id
}
