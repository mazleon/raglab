"use client"

import { useState } from 'react'
import { cn } from '@/lib/utils'

const tenants = [
  { id: 'default', name: 'Default Workspace', role: 'Owner' },
  { id: 'raglab', name: 'RAGLab Team', role: 'Admin' },
  { id: 'research', name: 'Research Lab', role: 'Member' },
]

interface TenantSwitcherProps {
  className?: string
}

export function TenantSwitcher({ className }: TenantSwitcherProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [currentTenant, setCurrentTenant] = useState(tenants[0])

  return (
    <div className={cn('relative', className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      >
        <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
          <svg
            className="w-3 h-3 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h-8M9 3H5a2 2 0 00-2 2v16a2 2 0 002 2h4M19 21v-6a2 2 0 00-2-2h-6a2 2 0 00-2 2v6"
            />
          </svg>
        </div>
        <span className="text-sm font-medium text-gray-700 dark:text-gray-200 max-w-32 truncate">
          {currentTenant.name}
        </span>
        <svg
          className="w-4 h-4 text-gray-500 dark:text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50">
          <div className="px-3 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
            Workspaces
          </div>
          {tenants.map((tenant) => (
            <button
              key={tenant.id}
              onClick={() => {
                setCurrentTenant(tenant)
                setIsOpen(false)
              }}
              className={cn(
                'w-full text-left px-3 py-2 text-sm transition-colors',
                tenant.id === currentTenant.id
                  ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white font-medium'
                  : 'text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50'
              )}
            >
              <div className="font-medium">{tenant.name}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">{tenant.role}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}