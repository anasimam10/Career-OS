import type { ApiError } from "@/lib/types/shared.types"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

export class ApiClientError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public raw?: unknown
  ) {
    super(message)
    this.name = "ApiClientError"
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorBody: ApiError = { error: `HTTP ${res.status}` }
    try {
      errorBody = await res.json()
    } catch {
      // ignore parse error
    }
    throw new ApiClientError(errorBody.error, res.status, errorBody)
  }
  const json = await res.json()
  // Backend returns snake_case; frontend types and components also use snake_case.
  // No key conversion needed — camelizeKeys was a design intent that conflicts
  // with the actual snake_case type definitions and component property access.
  return json as T
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  return handleResponse<T>(res)
}

export async function apiPost<T>(
  path: string,
  body: unknown,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    ...init,
  })
  return handleResponse<T>(res)
}
