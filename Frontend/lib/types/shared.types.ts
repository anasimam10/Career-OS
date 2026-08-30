export interface ApiError {
  error: string
  fallback_content?: unknown
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
}

export type LoadingState = "idle" | "loading" | "success" | "error"
