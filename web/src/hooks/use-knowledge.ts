"use client"

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { Document } from '@/types'
import { apiGet, apiPost, apiPostForm, apiDelete } from '@/lib/api'

interface DocumentsResponse { documents: Document[] }
interface DocumentResponse { document: Document }
interface IngestBody { ingest_path: string; config?: string }

async function fetchDocuments(): Promise<Document[]> {
  const data = await apiGet<DocumentsResponse>('/api/documents')
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
  const data = await apiPostForm<DocumentResponse>('/api/documents', formData)
  return data.document
}

async function deleteDocument(id: string): Promise<void> {
  // The /api/documents DELETE handler takes the id in the JSON body.
  await apiDelete('/api/documents', { id })
}

async function triggerIngestion(ingestPath: string, config?: string): Promise<void> {
  await apiPost('/api/ingest', { ingest_path: ingestPath, config } as IngestBody)
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