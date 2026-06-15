"use client"

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { User } from '@/types'

async function fetchMe(): Promise<User | null> {
  const res = await fetch('/api/auth/me', { cache: 'no-store' })
  if (res.status === 401) return null
  if (!res.ok) throw new Error('Failed to load session')
  const data = await res.json()
  return data.user ?? null
}

export function useAuth() {
  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: fetchMe,
    staleTime: 1000 * 60 * 5,
    retry: false,
  })
}

interface Credentials {
  email: string
  password: string
  name?: string
  tenant?: string
}

async function postAuth(path: string, body: Credentials): Promise<User> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({ error: 'Request failed' }))
  if (!res.ok) throw new Error(data.error ?? 'Request failed')
  return data.user
}

export function useLogin() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (creds: Credentials) => postAuth('/api/auth/login', creds),
    onSuccess: (user) => qc.setQueryData(['auth', 'me'], user),
  })
}

export function useRegister() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (creds: Credentials) => postAuth('/api/auth/register', creds),
    onSuccess: (user) => qc.setQueryData(['auth', 'me'], user),
  })
}

export function useLogout() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      await fetch('/api/auth/logout', { method: 'POST' })
    },
    onSuccess: () => {
      qc.setQueryData(['auth', 'me'], null)
      qc.clear()
    },
  })
}
