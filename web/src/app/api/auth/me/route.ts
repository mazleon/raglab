import { NextRequest } from 'next/server'
import { proxyJson } from '@/lib/backend'

export async function GET(req: NextRequest) {
  return proxyJson(req, '/auth/me')
}
