"use client"

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { User } from '@/types'
import { ApiError, apiGet, apiPost } from '@/lib/api'

interface AuthResponse { user: User }

async function fetchMe(): Promise<User | null> {
  try {
    const data = await apiGet<AuthResponse>('/api/auth/me')
    return data.user ?? null
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) return null
    throw e
  }
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

export function useLogin() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (creds: Credentials) => apiPost<AuthResponse>('/api/auth/login', creds),
    onSuccess: (data) => qc.setQueryData(['auth', 'me'], data.user),
  })
}

export function useRegister() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (creds: Credentials) => apiPost<AuthResponse>('/api/auth/register', creds),
    onSuccess: (data) => qc.setQueryData(['auth', 'me'], data.user),
  })
}

export function useLogout() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      // Fire-and-forget; the local cache is cleared regardless of the response.
      await apiPost('/api/auth/logout').catch(() => {})
    },
    onSuccess: () => {
      qc.setQueryData(['auth', 'me'], null)
      qc.clear()
    },
  })
}