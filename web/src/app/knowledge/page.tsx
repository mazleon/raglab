"use client"

import { useState, useRef, type DragEvent } from 'react'
import { useDocuments, useUploadDocument, useDeleteDocument } from '@/hooks/use-knowledge'
import { useConfig } from '@/hooks/use-config'
import { cn } from '@/lib/utils'
import type { Document } from '@/types'

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
}

function StatusBadge({ status }: { status: Document['status'] }) {
  const styles: Record<Document['status'], string> = {
    pending: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    indexing: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    indexed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    failed: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  }
  const labels: Record<Document['status'], string> = {
    pending: 'Pending',
    indexing: 'Indexing…',
    indexed: 'Indexed',
    failed: 'Failed',
  }
  return (
    <span className={cn('px-2 py-0.5 rounded-full text-[10px] font-medium border', styles[status])}>
      {status === 'indexing' ? (
        <span className="flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          <span>{labels[status]}</span>
        </span>
      ) : (
        labels[status]
      )}
    </span>
  )
}

export default function KnowledgePage() {
  const { data: documents = [], isLoading } = useDocuments()
  const { data: config } = useConfig()
  const uploadMutation = useUploadDocument()
  const deleteMutation = useDeleteDocument()
  const [isDragOver, setIsDragOver] = useState(false)
  const [embedding, setEmbedding] = useState('hashing')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileDrop = (e: DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const files = Array.from(e.dataTransfer.files)
    files.forEach(file => uploadMutation.mutate({ file, embedding }))
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    files.forEach(file => uploadMutation.mutate({ file, embedding }))
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-center gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-gradient-cyan">Knowledge</h1>
          <p className="text-sm text-white/40 mt-1">Upload and manage documents for RAG ingestion</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-[10px] font-semibold uppercase tracking-wider text-white/40">Embedding</label>
          <select
            value={embedding}
            onChange={(e) => setEmbedding(e.target.value)}
            className="appearance-none border border-white/[0.08] rounded-xl bg-white/[0.04] text-xs text-white/70 px-3 py-2 pr-7 focus:outline-none focus:border-cyan-500/40 cursor-pointer"
          >
            {(config?.embeddings ?? [{ id: 'hashing', name: 'Hashing (Offline)', available: true }]).map((e) => (
              <option key={e.id} value={e.id} disabled={e.available === false} className="bg-slate-900">
                {e.name}{e.available === false ? ' (key required)' : ''}
              </option>
            ))}
          </select>
        </div>
      </div>
      <p className="text-[11px] text-amber-300/60 bg-amber-500/5 border border-amber-500/15 rounded-lg px-3 py-2">
        Documents are indexed with the selected embedding. Chat must use the same embedding to retrieve them.
      </p>

      {/* Upload Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true) }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleFileDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          'relative p-10 rounded-2xl border-2 border-dashed text-center cursor-pointer transition-all duration-300',
          isDragOver
            ? 'border-cyan-400/50 bg-cyan-500/5 shadow-lg shadow-cyan-500/10'
            : 'border-white/[0.08] bg-white/[0.02] hover:border-cyan-500/20 hover:bg-cyan-500/[0.03]',
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.md,.txt,.csv,.docx"
          className="hidden"
          onChange={handleFileSelect}
        />
        <div className={cn(
          'w-16 h-16 mx-auto rounded-2xl flex items-center justify-center mb-4 transition-all duration-300',
          isDragOver ? 'bg-cyan-500/20 scale-110 neon-ring' : 'bg-white/[0.04]',
        )}>
          <svg className={cn('w-8 h-8 transition-colors', isDragOver ? 'text-cyan-400' : 'text-white/30')} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <p className="text-sm font-medium text-white/60 mb-1">
          {isDragOver ? 'Drop files here' : 'Drag & drop files or click to browse'}
        </p>
        <p className="text-[10px] text-white/30">PDF, Markdown, TXT, CSV, DOCX — up to 50MB</p>
        {uploadMutation.isPending && (
          <div className="mt-4 flex items-center justify-center space-x-2 text-xs text-cyan-400">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            <span>Uploading…</span>
          </div>
        )}
      </div>

      {/* Document List */}
      <div className="glass-panel rounded-2xl overflow-hidden">
        <div className="px-5 py-3 border-b border-white/[0.06] flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white/70">
            Indexed Documents
            <span className="ml-2 text-xs text-white/30 font-normal">({documents.length})</span>
          </h2>
        </div>

        {isLoading ? (
          <div className="p-8 space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-14 rounded-xl bg-white/[0.04] animate-pulse" />
            ))}
          </div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center py-12 text-white/30">
            <svg className="w-8 h-8 mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-xs">No documents uploaded yet</p>
          </div>
        ) : (
          <div className="divide-y divide-white/[0.06]">
            {documents.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between px-5 py-3.5 hover:bg-white/[0.02] transition-colors group">
                <div className="flex items-center space-x-3 min-w-0 flex-1">
                  {/* File icon */}
                  <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500/10 to-violet-500/10 flex items-center justify-center">
                    <svg className="w-4 h-4 text-cyan-400/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  {/* Info */}
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-white/70 truncate">{doc.name}</p>
                    <div className="flex items-center space-x-2 text-[10px] text-white/30 mt-0.5">
                      <span>{formatSize(doc.size)}</span>
                      {doc.chunks && <><span>•</span><span>{doc.chunks} chunks</span></>}
                      <span>•</span>
                      <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  {/* Status */}
                  <StatusBadge status={doc.status} />
                </div>
                {/* Delete */}
                <button
                  onClick={() => deleteMutation.mutate(doc.id)}
                  className="flex-shrink-0 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-rose-500/10 transition-all"
                >
                  <svg className="w-4 h-4 text-rose-400/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Stats footer */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Documents', value: documents.length.toString(), icon: 'files', color: 'from-cyan-500 to-blue-600' },
          { label: 'Indexed', value: documents.filter(d => d.status === 'indexed').length.toString(), icon: 'check', color: 'from-emerald-500 to-cyan-500' },
          { label: 'Total Chunks', value: documents.reduce((s, d) => s + (d.chunks || 0), 0).toLocaleString(), icon: 'grid', color: 'from-violet-500 to-rose-500' },
        ].map((stat) => (
          <div key={stat.label} className="glass-card rounded-2xl p-4 text-center">
            <p className="text-2xl font-bold bg-gradient-to-r bg-clip-text text-transparent from-cyan-400 to-violet-400">
              {stat.value}
            </p>
            <p className="text-[10px] text-white/30 mt-1">{stat.label}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
