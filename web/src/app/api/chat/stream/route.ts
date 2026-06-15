import { NextRequest } from 'next/server'
import { authHeaders, backend } from '@/lib/backend'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const body = await req.text()
  const upstream = await fetch(backend('/chat/stream'), {
    method: 'POST',
    headers: authHeaders(req, { 'Content-Type': 'application/json' }),
    body,
    cache: 'no-store',
    // @ts-expect-error - duplex is required by undici for streaming bodies
    duplex: 'half',
  })

  if (!upstream.ok || !upstream.body) {
    const text = await upstream.text().catch(() => 'stream failed')
    return new Response(text, { status: upstream.status || 502 })
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
    },
  })
}
