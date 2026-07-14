"use client"

import { useState } from 'react'

function ToggleSwitch({ enabled, onChange, label }: { enabled: boolean; onChange: (v: boolean) => void; label?: string }) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 ${
        enabled ? 'bg-gradient-to-r from-cyan-500 to-violet-600 shadow-sm shadow-cyan-500/20' : 'surface-2'
      }`}
      role="switch"
      aria-checked={enabled}
      aria-label={label}
    >
      <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform duration-300 ${
        enabled ? 'translate-x-6' : 'translate-x-1'
      }`} />
    </button>
  )
}

const apiKeys = [
  { name: 'OpenAI API Key', desc: 'Used for LLM-judge evaluations', configured: true },
  { name: 'Google Gemini API Key', desc: 'Alternative judge model', configured: false },
  { name: 'Cohere API Key', desc: 'Reranking and embedding models', configured: true },
  { name: 'OpenRouter API Key', desc: 'Multi-provider LLM access', configured: true },
]

export default function SettingsPage() {
  const [darkMode, setDarkMode] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-gradient-cyan">Settings</h1>
        <p className="text-sm text-muted mt-1">Manage your API keys and application preferences</p>
      </div>

      {/* API Configuration */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-base bg-gradient-to-r from-cyan-500/5 to-violet-500/5">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-primary">API Configuration</h2>
              <p className="text-xs text-subtle">Configure your API keys for LLM providers</p>
            </div>
          </div>
        </div>
        <div className="divide-y divide-white/[0.06]">
          {apiKeys.map((item) => (
            <div key={item.name} className="flex items-center justify-between px-6 py-4 hover:surface transition-colors">
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  item.configured ? 'bg-emerald-500/10 text-emerald-400' : 'surface text-subtle'
                }`}>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                  </svg>
                </div>
                <div>
                  <div className="font-medium text-sm text-muted">{item.name}</div>
                  <div className="text-xs text-subtle">{item.desc}</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                {item.configured && (
                  <span className="flex items-center space-x-1 text-[10px] text-emerald-400 font-medium">
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" /></svg>
                    <span>Configured</span>
                  </span>
                )}
                <button className="px-3 py-1.5 surface-2 text-muted rounded-lg text-xs font-medium surface-hover hover:text-muted transition-all active:scale-95">
                  {item.configured ? 'Update' : 'Configure'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Preferences */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-base bg-gradient-to-r from-violet-500/5 to-rose-500/5">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-rose-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.955 2.288a1.724 1.724 0 002.573 1.066c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c-.94 1.543-2.826.826-2.288 2.955a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.955a1.724 1.724 0 00-2.573-1.066c-.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543.94 3.31-.826 2.955a1.724 1.724 0 002.573 1.066zM15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-primary">Preferences</h2>
              <p className="text-xs text-subtle">Customize your workspace experience</p>
            </div>
          </div>
        </div>
        <div className="divide-y divide-white/[0.06]">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <svg className="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              </div>
              <div>
                <div className="font-medium text-sm text-muted">Dark Mode</div>
                <div className="text-xs text-subtle">Toggle dark theme</div>
              </div>
            </div>
            <ToggleSwitch enabled={darkMode} onChange={setDarkMode} label="Dark Mode" />
          </div>
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center">
                <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </div>
              <div>
                <div className="font-medium text-sm text-muted">Auto-refresh</div>
                <div className="text-xs text-subtle">Auto-refresh experiment results</div>
              </div>
            </div>
            <ToggleSwitch enabled={autoRefresh} onChange={setAutoRefresh} label="Auto-refresh" />
          </div>
        </div>
      </div>
    </div>
  )
}
