import { NextRequest, NextResponse } from 'next/server'
import { authHeaders, backend } from '@/lib/backend'

export async function GET(req: NextRequest) {
  const res = await fetch(backend('/documents'), {
    headers: authHeaders(req),
    cache: 'no-store',
  })
  return new Response(await res.text(), {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  })
}

export async function POST(req: NextRequest) {
  // Pass the multipart form straight through to the backend.
  const form = await req.formData()
  const res = await fetch(backend('/documents'), {
    method: 'POST',
    headers: authHeaders(req), // do NOT set Content-Type — fetch sets the boundary
    body: form,
    cache: 'no-store',
  })
  const data = await res.json().catch(() => ({ detail: 'upload failed' }))
  if (!res.ok) {
    return NextResponse.json({ error: data.detail ?? 'upload failed' }, { status: res.status })
  }
  return NextResponse.json(data, { status: res.status })
}

export async function DELETE(req: NextRequest) {
  const { id } = await req.json().catch(() => ({ id: '' }))
  const res = await fetch(backend(`/documents/${id}`), {
    method: 'DELETE',
    headers: authHeaders(req),
    cache: 'no-store',
  })
  return new Response(await res.text(), {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  })
}
