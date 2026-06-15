"use client"

import { cn } from '@/lib/utils'
import { useAuth } from '@/hooks/use-auth'

interface TenantSwitcherProps {
  className?: string
}

/**
 * Displays the active workspace (tenant). A user belongs to one tenant in this
 * model, so this is an indicator rather than a switcher — multi-tenant membership
 * is a future extension.
 */
export function TenantSwitcher({ className }: TenantSwitcherProps) {
  const { data: user } = useAuth()
  if (!user) return null

  return (
    <div
      className={cn(
        'flex items-center space-x-2 px-3 py-2 rounded-xl surface border border-base',
        className,
      )}
      title={`Workspace: ${user.tenant_id} · ${user.role}`}
    >
      <div className="w-5 h-5 bg-gradient-to-br from-emerald-400 to-cyan-500 rounded-lg flex items-center justify-center shadow-sm shadow-emerald-400/20">
        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h-8M9 3H5a2 2 0 00-2 2v16a2 2 0 002 2h4M19 21v-6a2 2 0 00-2-2h-6a2 2 0 00-2 2v6" />
        </svg>
      </div>
      <span className="text-sm font-medium text-muted max-w-28 truncate capitalize hidden sm:block">
        {user.tenant_id}
      </span>
    </div>
  )
}
