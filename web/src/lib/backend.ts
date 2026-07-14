import 'server-only'
import type { NextRequest } from 'next/server'

/** Base URL of the FastAPI backend (server-side only). */
export const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000'

/** Name of the HTTP-only session cookie the BFF owns on the browser. */
export const SESSION_COOKIE = 'raglab_session'

export function backend(path: string): string {
  return `${BACKEND_URL}${path}`
}

/** Read the session token from the incoming request's cookie. */
export function sessionToken(req: NextRequest): string | undefined {
  return req.cookies.get(SESSION_COOKIE)?.value
}

/**
 * Headers to forward to the backend: replays the session cookie as a Bearer
 * token (the backend prefers an explicit Authorization header over a cookie).
 */
export function authHeaders(req: NextRequest, extra: Record<string, string> = {}): Record<string, string> {
  const token = sessionToken(req)
  return token ? { Authorization: `Bearer ${token}`, ...extra } : { ...extra }
}

/** Forward a JSON request to the backend and relay its JSON response + status. */
export async function proxyJson(
  req: NextRequest,
  path: string,
  init: { method?: string; body?: unknown } = {},
): Promise<Response> {
  const res = await fetch(backend(path), {
    method: init.method ?? 'GET',
    headers: authHeaders(req, { 'Content-Type': 'application/json' }),
    body: init.body !== undefined ? JSON.stringify(init.body) : undefined,
    cache: 'no-store',
  })
  const text = await res.text()
  return new Response(text, {
    status: res.status,
    headers: { 'Content-Type': res.headers.get('Content-Type') ?? 'application/json' },
  })
}
