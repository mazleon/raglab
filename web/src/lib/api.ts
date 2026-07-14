"use client"

/**
 * Client-side API helpers. Every hook routes its fetch through these so the
 * BFF contract (JSON in, normalized {@link ApiError} out) lives in one place
 * instead of being re-implemented per hook.
 *
 * The browser always calls the Next route handlers under `/api/*` (the BFF);
 * it never reaches FastAPI directly.
 */

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function parseError(res: Response): Promise<string> {
  const data = await res.json().catch(() => null)
  if (data && typeof data.error === 'string' && data.error) return data.error
  if (data && typeof data.detail === 'string' && data.detail) return data.detail
  return `Request failed (${res.status})`
}

async function asJson<T>(res: Response): Promise<T> {
  return (await res.json()) as T
}

/** GET a JSON endpoint. Throws {@link ApiError} on a non-2xx response. */
export async function apiGet<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(path, { cache: 'no-store', ...init })
  if (!res.ok) throw new ApiError(await parseError(res), res.status)
  return asJson<T>(res)
}

/** POST a JSON body. Throws {@link ApiError} on a non-2xx response. */
export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new ApiError(await parseError(res), res.status)
  return asJson<T>(res)
}

/** POST a multipart form (e.g. file upload). Content-Type is set by the browser. */
export async function apiPostForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(path, { method: 'POST', body: form })
  if (!res.ok) throw new ApiError(await parseError(res), res.status)
  return asJson<T>(res)
}

/** DELETE with an optional JSON body. Throws {@link ApiError} on a non-2xx. */
export async function apiDelete(path: string, body?: unknown): Promise<void> {
  const res = await fetch(path, {
    method: 'DELETE',
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new ApiError(await parseError(res), res.status)
}