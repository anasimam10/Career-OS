/**
 * Mock data toggle.
 * Set NEXT_PUBLIC_USE_MOCK=true in .env.local to use mock data.
 * All lib/api/*.ts files check this flag before calling the real API.
 */
export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true"
