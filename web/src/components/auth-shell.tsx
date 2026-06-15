"use client"

import { type ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/30 mb-4">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h1 className="text-xl font-semibold text-primary">{title}</h1>
          <p className="text-sm text-muted mt-1">{subtitle}</p>
        </div>
        <div className="glass-panel rounded-2xl p-6 shadow-2xl shadow-violet-500/10">
          {children}
        </div>
        <p className="mt-6 text-center text-[10px] uppercase tracking-[0.15em] text-subtle">
          RAGLab · Agentic Intelligence Workspace
        </p>
      </div>
    </div>
  )
}

interface FieldProps {
  label: string
  value: string
  onChange: (v: string) => void
  type?: string
  placeholder?: string
  autoComplete?: string
  required?: boolean
  minLength?: number
  hint?: string
}

export function Field({ label, value, onChange, type = 'text', placeholder, autoComplete, required, minLength, hint }: FieldProps) {
  return (
    <div className="space-y-1.5">
      <label className="text-[11px] font-semibold uppercase tracking-wider text-muted">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoComplete={autoComplete}
        required={required}
        minLength={minLength}
        className="w-full px-3.5 py-2.5 rounded-xl surface border border-base text-sm text-primary placeholder:text-subtle focus:outline-none focus:border-cyan-500/40 focus:surface-2 transition-all"
      />
      {hint && <p className="text-[10px] text-subtle">{hint}</p>}
    </div>
  )
}

export function SubmitButton({ loading, children }: { loading?: boolean; children: ReactNode }) {
  return (
    <button
      type="submit"
      disabled={loading}
      className={cn(
        'w-full flex items-center justify-center py-2.5 rounded-xl text-sm font-medium transition-all',
        'bg-gradient-to-r from-cyan-500 to-violet-600 text-white shadow-lg shadow-cyan-500/20',
        'hover:shadow-cyan-500/30 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed',
      )}
    >
      {loading ? (
        <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9" />
        </svg>
      ) : children}
    </button>
  )
}
