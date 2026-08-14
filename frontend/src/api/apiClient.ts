import type { ApiErrorResponse } from "../types/api"

const DEFAULT_TIMEOUT_MS = 30000

/**
 * Why a hand-rolled client instead of axios: the project has no HTTP
 * dependency and the surface needed here (JSON, bearer token, one error
 * shape) is small enough that adding one would cost more than it saves.
 */

export type ApiErrorKind =
  | "network"
  | "timeout"
  | "unauthorized"
  | "forbidden"
  | "notFound"
  | "validation"
  | "server"
  | "unknown"

export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status: number | null
  readonly validationErrors: Record<string, string>

  constructor(
    kind: ApiErrorKind,
    message: string,
    status: number | null = null,
    validationErrors: Record<string, string> = {},
  ) {
    super(message)
    this.name = "ApiError"
    this.kind = kind
    this.status = status
    this.validationErrors = validationErrors
  }

  /** True when the caller should show a "you cannot do this" state rather than an error. */
  get isPermissionDenied(): boolean {
    return this.kind === "forbidden"
  }
}

type TokenReader = () => string | null
type UnauthorizedHandler = () => void

let readToken: TokenReader = () => null
let onUnauthorized: UnauthorizedHandler = () => {}

/**
 * Wired once by AuthProvider. Keeping the token out of this module's own state
 * avoids a circular import between the auth context and the API modules it uses.
 */
export function configureApiClient(options: {
  getToken: TokenReader
  onUnauthorized: UnauthorizedHandler
}): void {
  readToken = options.getToken
  onUnauthorized = options.onUnauthorized
}

export function apiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_URL
  return (configured && configured.trim() ? configured : "http://localhost:8080").replace(/\/+$/, "")
}

export function orchestratorBaseUrl(): string {
  const configured = import.meta.env.VITE_ORCHESTRATOR_URL
  return (configured && configured.trim() ? configured : "http://localhost:8100").replace(/\/+$/, "")
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"
  body?: unknown
  /** Skip the Authorization header (login, activation, password reset). */
  anonymous?: boolean
  /** Absolute base to use instead of the Spring API, e.g. the orchestrator. */
  baseUrl?: string
  timeoutMs?: number
  signal?: AbortSignal
}

function isApiErrorResponse(value: unknown): value is ApiErrorResponse {
  return typeof value === "object" && value !== null && "status" in value && "message" in value
}

async function readErrorBody(response: Response): Promise<{ message: string; validationErrors: Record<string, string> }> {
  const fallback = `${response.status} ${response.statusText}`.trim()
  try {
    const text = await response.text()
    if (!text) return { message: fallback, validationErrors: {} }
    const parsed: unknown = JSON.parse(text)
    if (isApiErrorResponse(parsed)) {
      return {
        message: parsed.message || fallback,
        validationErrors: parsed.validationErrors ?? {},
      }
    }
    return { message: text.slice(0, 500), validationErrors: {} }
  } catch {
    return { message: fallback, validationErrors: {} }
  }
}

function kindForStatus(status: number): ApiErrorKind {
  if (status === 401) return "unauthorized"
  if (status === 403) return "forbidden"
  if (status === 404) return "notFound"
  if (status === 400 || status === 422) return "validation"
  if (status >= 500) return "server"
  return "unknown"
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, anonymous = false, baseUrl, timeoutMs = DEFAULT_TIMEOUT_MS } = options

  const headers: Record<string, string> = { Accept: "application/json" }
  if (body !== undefined) headers["Content-Type"] = "application/json"

  if (!anonymous) {
    const token = readToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  // AbortSignal.timeout would be terser but leaves no way to merge a
  // caller-supplied signal, which ChatPage needs to cancel in-flight requests.
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  if (options.signal) {
    if (options.signal.aborted) controller.abort()
    else options.signal.addEventListener("abort", () => controller.abort(), { once: true })
  }

  let response: Response
  try {
    response = await fetch(`${baseUrl ?? apiBaseUrl()}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    })
  } catch (cause) {
    if (controller.signal.aborted) {
      throw new ApiError("timeout", "The request timed out. The service may be down or unreachable.")
    }
    throw new ApiError(
      "network",
      "Could not reach the server. Check that the backend is running and reachable.",
    )
  } finally {
    clearTimeout(timer)
  }

  if (response.status === 401 && !anonymous) {
    // Clearing auth state here (rather than in every caller) is what makes a
    // single expired token reliably bounce the user back to /login. Only for
    // authenticated calls: an anonymous 401 (login, refresh, activate,
    // forgot-password) means invalid credentials, not an expired session -
    // there was no session to expire, and this hardcoded message would
    // replace the backend's real "Invalid email or password" reason.
    onUnauthorized()
    throw new ApiError("unauthorized", "Your session has expired. Please sign in again.", 401)
  }

  if (!response.ok) {
    const { message, validationErrors } = await readErrorBody(response)
    throw new ApiError(kindForStatus(response.status), message, response.status, validationErrors)
  }

  if (response.status === 204) return undefined as T

  const text = await response.text()
  if (!text) return undefined as T
  return JSON.parse(text) as T
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) => request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PUT", body }),
  delete: <T>(path: string, options?: RequestOptions) => request<T>(path, { ...options, method: "DELETE" }),
}
