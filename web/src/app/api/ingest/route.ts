import { NextRequest } from 'next/server'
import { proxyJson } from '@/lib/backend'

// Ad-hoc path ingestion (e.g. seeding the bundled examples). File uploads go
// through /api/documents instead. Backend ingests when /query is given ingest_path.
export async function POST(req: NextRequest) {
  const { ingest_path, config } = await req.json().catch(() => ({}))
  return proxyJson(req, '/query', {
    method: 'POST',
    body: { query: 'index', config: config ?? 'configs/pipelines/naive.yaml', ingest_path },
  })
}
