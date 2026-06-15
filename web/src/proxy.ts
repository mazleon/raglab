import { NextRequest, NextResponse } from 'next/server'

const SESSION_COOKIE = 'raglab_session'
const AUTH_PAGES = ['/login', '/register']

/**
 * Server-side route guard. Unauthenticated users hitting an app page are sent to
 * /login; authenticated users hitting /login or /register are sent to /chat.
 * Signature is verified by the backend on every API call — this is the coarse
 * gate that keeps protected pages from rendering at all.
 */
export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl
  const hasSession = Boolean(req.cookies.get(SESSION_COOKIE)?.value)
  const isAuthPage = AUTH_PAGES.some((p) => pathname.startsWith(p))

  if (!hasSession && !isAuthPage) {
    const url = req.nextUrl.clone()
    url.pathname = '/login'
    url.searchParams.set('next', pathname)
    return NextResponse.redirect(url)
  }
  if (hasSession && isAuthPage) {
    const url = req.nextUrl.clone()
    url.pathname = '/chat'
    url.search = ''
    return NextResponse.redirect(url)
  }
  return NextResponse.next()
}

export const config = {
  // Run on everything except API routes, Next internals, and static assets.
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)'],
}
