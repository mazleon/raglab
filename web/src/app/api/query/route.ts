import { NextRequest } from 'next/server'
import { proxyJson } from '@/lib/backend'

// Non-streaming query (used for one-off calls / programmatic access).
export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}))
  return proxyJson(req, '/query', { method: 'POST', body })
}
