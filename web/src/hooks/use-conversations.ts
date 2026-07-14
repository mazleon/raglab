"use client"

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Conversation } from '@/types'

async function fetchConversations(): Promise<Conversation[]> {
  const res = await fetch('/api/conversations', { cache: 'no-store' })
  if (!res.ok) return []
  const data = await res.json()
  return data.conversations ?? []
}

export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: fetchConversations,
    staleTime: 1000 * 30,
  })
}

export function useDeleteConversation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await fetch(`/api/conversations/${id}`, { method: 'DELETE' })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['conversations'] }),
  })
}
