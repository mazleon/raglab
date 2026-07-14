"use client"

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Conversation } from '@/types'
import { apiGet, apiDelete } from '@/lib/api'

interface ConversationsResponse { conversations: Conversation[] }

async function fetchConversations(): Promise<Conversation[]> {
  try {
    const data = await apiGet<ConversationsResponse>('/api/conversations')
    return data.conversations ?? []
  } catch {
    // Listing is best-effort: show an empty sidebar rather than an error state.
    return []
  }
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
    mutationFn: (id: string) => apiDelete(`/api/conversations/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['conversations'] }),
  })
}