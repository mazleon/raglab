"use client"

type Theme = 'dark' | 'light'

function current(): Theme {
  return document.documentElement.classList.contains('light') ? 'light' : 'dark'
}

function apply(theme: Theme) {
  const root = document.documentElement
  root.classList.toggle('light', theme === 'light')
  root.classList.toggle('dark', theme === 'dark')
}

/**
 * Theme toggle with no React state.
 *
 * The blocking script in <head> sets `.light`/`.dark` on <html> before
 * hydration, so the icon is driven purely by those classes via arbitrary
 * variants — the rendered DOM is identical on server and client (no
 * hydration mismatch) and `toggle()` reads the live class from the DOM.
 */
export function ThemeToggle() {
  const toggle = () => {
    const next: Theme = current() === 'dark' ? 'light' : 'dark'
    localStorage.setItem('raglab-theme', next)
    apply(next)
  }

  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      title="Toggle theme"
      className="p-2 rounded-xl surface-hover text-muted hover:text-primary transition-all"
    >
      {/* Sun icon — shown only in light mode (ancestor <html class="light">) */}
      <svg
        className="w-5 h-5 hidden [.light_&]:block"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.8}
          d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
        />
      </svg>
      {/* Moon icon — shown only in dark mode (hidden when <html class="light">) */}
      <svg
        className="w-5 h-5 [.light_&]:hidden"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.8}
          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
        />
      </svg>
    </button>
  )
}