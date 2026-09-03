import type { ApiError } from "@/lib/types/shared.types"
import { getStudentId } from "@/lib/session"

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
  return json as T
}

function getRequestHeaders(customHeaders?: HeadersInit): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  const studentId = getStudentId()
  if (studentId) {
    headers["X-Student-Id"] = String(studentId)
  }
  if (customHeaders) {
    if (customHeaders instanceof Headers) {
      customHeaders.forEach((val, key) => {
        headers[key] = val
      })
    } else if (Array.isArray(customHeaders)) {
      customHeaders.forEach(([key, val]) => {
        headers[key] = val
      })
    } else {
      Object.assign(headers, customHeaders)
    }
  }
  return headers
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "GET",
    ...init,
    headers: getRequestHeaders(init?.headers),
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
    ...init,
    headers: getRequestHeaders(init?.headers),
    body: JSON.stringify(body),
  })
  return handleResponse<T>(res)
}

export async function apiPut<T>(
    path: string,
    body: unknown,
    init?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "PUT",
    ...init,
    headers: getRequestHeaders(init?.headers),
    body: JSON.stringify(body),
  })
  return handleResponse<T>(res)
}

