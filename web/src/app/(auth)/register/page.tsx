"use client"

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useRegister } from '@/hooks/use-auth'
import { AuthShell, Field, SubmitButton } from '@/components/auth-shell'

export default function RegisterPage() {
  const router = useRouter()
  const register = useRegister()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [tenant, setTenant] = useState('')

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await register.mutateAsync({ name, email, password, tenant: tenant || 'default' })
      router.push('/chat')
    } catch { /* surfaced below */ }
  }

  return (
    <AuthShell title="Create your account" subtitle="Spin up an isolated RAGLab workspace">
      <form onSubmit={onSubmit} className="space-y-4">
        <Field label="Name" value={name} onChange={setName} placeholder="Ada Lovelace" autoComplete="name" />
        <Field label="Email" type="email" value={email} onChange={setEmail}
          placeholder="you@company.com" autoComplete="email" required />
        <Field label="Workspace" value={tenant} onChange={setTenant}
          placeholder="acme (optional)" hint="Your team's isolated tenant. Defaults to 'default'." />
        <Field label="Password" type="password" value={password} onChange={setPassword}
          placeholder="At least 8 characters" autoComplete="new-password" required minLength={8} />
        {register.isError && (
          <p className="text-xs text-rose-400/90 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
            {(register.error as Error).message}
          </p>
        )}
        <SubmitButton loading={register.isPending}>Create account</SubmitButton>
      </form>
      <p className="mt-6 text-center text-xs text-muted">
        Already have an account?{' '}
        <Link href="/login" className="text-cyan-400 hover:text-cyan-300 font-medium">Sign in</Link>
      </p>
    </AuthShell>
  )
}
