import { NextRequest } from 'next/server'
import { proxyJson } from '@/lib/backend'

type Ctx = { params: Promise<{ id: string }> }

export async function GET(req: NextRequest, { params }: Ctx) {
  const { id } = await params
  return proxyJson(req, `/conversations/${id}`)
}

export async function PATCH(req: NextRequest, { params }: Ctx) {
  const { id } = await params
  const body = await req.json().catch(() => ({}))
  return proxyJson(req, `/conversations/${id}`, { method: 'PATCH', body })
}

export async function DELETE(req: NextRequest, { params }: Ctx) {
  const { id } = await params
  return proxyJson(req, `/conversations/${id}`, { method: 'DELETE' })
}
