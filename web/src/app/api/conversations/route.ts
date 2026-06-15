import { NextRequest } from 'next/server'
import { proxyJson } from '@/lib/backend'

export async function GET(req: NextRequest) {
  return proxyJson(req, '/conversations')
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}))
  return proxyJson(req, '/conversations', { method: 'POST', body })
}
