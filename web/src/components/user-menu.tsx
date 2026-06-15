"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth, useLogout } from '@/hooks/use-auth'

export function UserMenu() {
  const [isOpen, setIsOpen] = useState(false)
  const { data: user } = useAuth()
  const logout = useLogout()
  const router = useRouter()

  const initial = (user?.name || user?.email || 'U').charAt(0).toUpperCase()
  const label = user?.name || user?.email?.split('@')[0] || 'Account'

  const handleSignOut = async () => {
    await logout.mutateAsync()
    router.push('/login')
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 rounded-xl hover:bg-white/[0.06] transition-all group"
        aria-label="Account menu"
      >
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center text-white text-sm font-medium shadow-lg shadow-cyan-500/20">
          {initial}
        </div>
        <span className="text-sm font-medium text-white/60 group-hover:text-white/80 hidden sm:block max-w-32 truncate">{label}</span>
        <svg className="w-4 h-4 text-white/30 group-hover:text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-56 glass-panel rounded-xl shadow-2xl shadow-violet-500/10 py-1 z-50 animate-scale-in">
            <div className="px-4 py-3 border-b border-white/[0.06]">
              <p className="text-sm font-medium text-white/80 truncate">{user?.name || 'Signed in'}</p>
              <p className="text-[11px] text-white/40 truncate">{user?.email}</p>
            </div>
            <button
              onClick={handleSignOut}
              disabled={logout.isPending}
              className="w-full text-left px-4 py-2.5 text-sm text-rose-400/80 hover:text-rose-300 hover:bg-white/[0.04] transition-colors disabled:opacity-50"
            >
              {logout.isPending ? 'Signing out…' : 'Sign out'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
