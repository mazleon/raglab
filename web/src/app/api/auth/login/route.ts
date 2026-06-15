import { NextRequest, NextResponse } from 'next/server'
import { backend, SESSION_COOKIE } from '@/lib/backend'

const MAX_AGE = 60 * 60 * 24 * 7

export async function POST(req: NextRequest) {
  const body = await req.json()
  const res = await fetch(backend('/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    cache: 'no-store',
  })
  const data = await res.json().catch(() => ({ detail: 'login failed' }))
  if (!res.ok) {
    return NextResponse.json({ error: data.detail ?? 'login failed' }, { status: res.status })
  }
  const response = NextResponse.json({ user: data.user })
  response.cookies.set(SESSION_COOKIE, data.token, {
    httpOnly: true, sameSite: 'lax', path: '/', maxAge: MAX_AGE,
  })
  return response
}
