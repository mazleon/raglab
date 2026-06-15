"use client"

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { Document } from '@/types'

async function fetchDocuments(): Promise<Document[]> {
  const res = await fetch('/api/documents')
  if (!res.ok) throw new Error('Failed to fetch documents')
  const data = await res.json()
  return data.documents ?? []
}

interface UploadArgs {
  file: File
  embedding?: string
}

async function uploadDocument({ file, embedding = 'hashing' }: UploadArgs): Promise<Document> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('embedding', embedding)
  const res = await fetch('/api/documents', {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Upload failed' }))
    throw new Error(err.error)
  }
  const data = await res.json()
  return data.document
}

async function deleteDocument(id: string): Promise<void> {
  const res = await fetch('/api/documents', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id }),
  })
  if (!res.ok) throw new Error('Failed to delete document')
}

async function triggerIngestion(ingestPath: string, config?: string): Promise<void> {
  const res = await fetch('/api/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ingest_path: ingestPath, config }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Ingestion failed' }))
    throw new Error(err.error)
  }
}

export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: fetchDocuments,
    refetchInterval: 5000, // Poll for status changes
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}

export function useIngestion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ ingest_path, config }: { ingest_path: string; config?: string }) =>
      triggerIngestion(ingest_path, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}
