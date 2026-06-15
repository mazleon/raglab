"use client"

import { Suspense, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useLogin } from '@/hooks/use-auth'
import { AuthShell, Field, SubmitButton } from '@/components/auth-shell'

function LoginForm() {
  const router = useRouter()
  const params = useSearchParams()
  const login = useLogin()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login.mutateAsync({ email, password })
      router.push(params.get('next') || '/chat')
    } catch { /* surfaced below */ }
  }

  return (
    <AuthShell title="Welcome back" subtitle="Sign in to your RAGLab workspace">
      <form onSubmit={onSubmit} className="space-y-4">
        <Field label="Email" type="email" value={email} onChange={setEmail}
          placeholder="you@company.com" autoComplete="email" required />
        <Field label="Password" type="password" value={password} onChange={setPassword}
          placeholder="••••••••" autoComplete="current-password" required />
        {login.isError && (
          <p className="text-xs text-rose-400/90 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
            {(login.error as Error).message}
          </p>
        )}
        <SubmitButton loading={login.isPending}>Sign in</SubmitButton>
      </form>
      <p className="mt-6 text-center text-xs text-muted">
        New here?{' '}
        <Link href="/register" className="text-cyan-400 hover:text-cyan-300 font-medium">Create an account</Link>
      </p>
    </AuthShell>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  )
}
