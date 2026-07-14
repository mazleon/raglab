# Frontend Architecture Review — web/

Scope: `web/` only. Every claim below is backed by a file path read during this
review. Backend (`src/raglab/`) is out of scope. Where something is already
good, I say so and move on.

Stack observed: Next.js 16.2.9 (App Router) + React 19.2.7 + TypeScript 6
(strict), TanStack React Query 5, Tailwind v4 (CSS-first, `@import "tailwindcss"`),
`lucide-react` + a lot of hand-rolled inline SVG. Zustand 5 is in
`package.json` but **unused** (see §3).

## Current Structure (routes, components, hooks, stores, lib — with paths)

```
web/src/
  app/
    layout.tsx                         (server component, RSC)
    globals.css                        (theme tokens + utilities, 202 lines)
    agents/page.tsx        (client)    experiments/page.tsx (client)
    chat/page.tsx          (client)    knowledge/page.tsx   (client)
    login/page.tsx         (client)    memory/page.tsx      (client)
    register/page.tsx      (client)    settings/page.tsx    (client)
    api/
      auth/{login,logout,me,register}/route.ts
      chat/stream/route.ts            (SSE proxy)
      config/route.ts
      conversations/route.ts  conversations/[id]/route.ts
      documents/route.ts     ingest/route.ts     query/route.ts
  components/   13 files, flat, kebab-case
    app-shell.tsx  auth-shell.tsx  command-palette.tsx  composer.tsx
    conversation-sidebar.tsx  experiment-list.tsx  left-nav.tsx
    message-item.tsx  message-list.tsx  model-selector.tsx
    query-provider.tsx  tenant-switcher.tsx  theme-toggle.tsx  user-menu.tsx
  hooks/        6 files: use-auth, use-chat-stream, use-config,
                use-conversations, use-experiments, use-knowledge
  stores/       EMPTY (no files)
  lib/          backend.ts (44 lines, server-only BFF helpers)
                utils.ts  (just cn())
  types.ts      single manual type barrel (~80+ lines, all backend DTOs)
  global.d.ts   one line: `declare module '*.css'`
```

Total: 9 pages, 13 components, 6 hooks, 12 route handlers, 2 lib files.
Small enough that a full `features/` restructure is premature (see §7).

## App-Router & Component Organization

**What's good.**
- `app/layout.tsx` is a true server component (no `'use client'`); it wraps
  children in `<QueryProvider><AppShell>` — both correctly client. The RSC
  boundary is exactly where it should be.
- A pre-paint theme script in `layout.tsx` reads `localStorage` and adds
  `dark`/`light` to `<html>` before hydration, with `suppressHydrationWarning`.
  Correct, minimal flash-of-wrong-theme handling.
- `app/api/*` is used as a backend-for-frontend (BFF): the browser never calls
  FastAPI directly, every call goes through a route handler. Clean.
- The dynamic route `conversations/[id]/route.ts` correctly awaits
  `Promise<{ id: string }>` params (Next 16 async-params API) and implements
  GET/PATCH/DELETE via the shared `proxyJson`. Good.

**What's weak.**
1. **No route groups for auth.** `AppShell` (`components/app-shell.tsx`)
   hardcodes `BARE_ROUTES = ['/login', '/register']` and short-circuits the
   chrome via a `pathname.startsWith` check. This works but pushes routing
   knowledge into a component. Idiomatic App Router is a route group:
   ```
   app/(auth)/login/page.tsx
   app/(auth)/register/page.tsx
   app/(auth)/layout.tsx     ← bare shell, no AppShell
   app/(app)/chat/page.tsx   ... etc.
   app/(app)/layout.tsx     ← AppShell + QueryProvider
   app/layout.tsx           ← <html><body> only
   ```
   This also lets you drop the `BARE_ROUTES` array entirely.
2. **Every page is `'use client'`.** All 9 pages start with `"use client"`.
   There is no server component page, no streaming RSC, no Suspense boundary
   authored by you. `login/page.tsx` does wrap a child in `<Suspense>`
   (because `useSearchParams` requires it) — that's correct — but otherwise
   pages are client components that fetch via React Query. For a data-heavy
   dashboard this is defensible (auth gating, heavy interactivity), but it
   leaves RSC streaming and SEO/offload on the table. Not a bug, a deliberate
   trade-off worth naming.
3. **No `loading.tsx` / `error.tsx` / `not-found.tsx` anywhere.** `find` returns
   zero. Every page hand-rolls its own loading spinner (e.g.
   `experiments/page.tsx` renders an inline `animate-spin` div). A shared
   `app/loading.tsx` + `app/error.tsx` would centralize this and let React
   Query's `isLoading` focus on data, not shell.
4. **`agents/page.tsx` and `memory/page.tsx` are stubs.** Both render a
   placeholder "empty state" with a disabled-looking "New Agent"/"New Memory"
   button that does nothing. They're routes with no behavior. Either wire them
   up or mark them as not-yet-implemented so reviewers don't expect behavior.

## State Management & Data Fetching (stores, hooks, SSE, API client)

**What's good.**
- Server state is uniformly TanStack Query. One `QueryClient` in
  `components/query-provider.tsx` with sane defaults (`refetchOnWindowFocus:
  false`, `retry: 1`, `staleTime: 60s`). Each hook owns its query key
  (`['auth','me']`, `['config']`, `['conversations']`, `['documents']`,
  `['experiments']`); mutations invalidate the right keys. This is the right
  pattern and it's applied consistently across all 6 hooks.
- SSE is handled in a single place: `hooks/use-chat-stream.ts`. It owns the
  message list in local `useState`, opens a `fetch` to `/api/chat/stream`,
  manually parses SSE blocks (`parseSSEBlock`), and folds `meta`/`trace`/
  `delta`/`sources`/`metrics`/`error` events into the active assistant
  message. AbortController-backed `stop()`. This is well-factored — the rest
  of the app just consumes `{ messages, isStreaming, send, stop }`.
- The SSE BFF route (`app/api/chat/stream/route.ts`) is a 30-line pass-through
  to FastAPI with `duplex: 'half'` (correctly `@ts-expect-error`-annotated for
  undici) and proper streaming headers. The browser never talks to FastAPI
  directly and never has to handle CORS for the stream.

**What's weak.**
1. **`stores/` is an empty directory and Zustand is a dead dependency.**
   `web/src/stores/` has zero files; `grep -rn "zustand" src/` returns nothing,
   yet `package.json` lists `"zustand": "^5.0.14"`. Either introduce a store
   (the chat `messages`/`activeId`/`selectedModel` cluster in `chat/page.tsx`
   is a candidate — it's passed around as props and reset on route change) or
   delete the directory and the dep. Carrying an unused runtime dep is sloppy
   signal.
2. **Conversation loading duplicates a hook.** `chat/page.tsx`'s `handleSelect`
   does a raw `fetch('/api/conversations/${id}')` and `setMessages(...)` by
   hand, but `hooks/use-conversations.ts` already exports `useConversation(id)`
   returning `ConversationDetail` with the same shape. The hook is unused by
   the chat page (it exists, so something may have used it once). Pick one:
   either drive the chat view off `useConversation` (and convert its output to
   `ChatMessage[]` in a small `useMemo`), or delete `useConversation`. Today
   the manual fetch in `chat/page.tsx` bypasses cache + invalidation that the
   hook would give you for free.
3. **`useChatStream` keeps `messages` in component state, not Query cache.**
   That's actually correct for a streaming buffer (you don't want React Query
   fighting your incremental patchAssistant). But `chat/page.tsx` also holds
   `activeId`, `selectedPipeline`, `selectedModel`, `selectedEmbedding` as
   local `useState`. None of that survives a navigation away from `/chat` and
   back. If preserving chat config across nav is desired, that's the one place
   a Zustand store (or a `chat` route-level layout holding the state) would
   earn its keep. If it's not desired, ignore.
4. **`useDocuments` polls every 5s unconditionally** (`refetchInterval: 5000`
   in `use-knowledge.ts`). Fine on the knowledge page, but the query stays
   mounted only while that page is active (React Query unmounts), so the blast
   radius is bounded. Worth a comment saying *why* it polls (status changes
   after upload/ingest) so a future reader doesn't "optimize" it away.

## lib/ Boundaries & Type Sharing with Backend

**What's good.**
- `lib/backend.ts` is a tight 44-line server-only module: `BACKEND_URL`,
  `SESSION_COOKIE`, `backend(path)`, `sessionToken(req)`,
  `authHeaders(req, extra)`, `proxyJson(req, path, init)`. Every route handler
  in `app/api/*` uses these. No scattered `fetch('http://localhost:8000')`
  strings, no duplicated auth-header logic. This is the right abstraction and
  it's actually used everywhere.
- `lib/utils.ts` is the standard shadcn `cn()` (clsx + tailwind-merge). One
  export, one job.

**What's weak.**
1. **No client-side API client.** Client code calls `fetch('/api/...')`
   directly inside each hook (`use-auth`, `use-config`, `use-conversations`,
   `use-knowledge`, `use-experiments`). URLs and `cache: 'no-store'` defaults
   are duplicated across hooks. A tiny `lib/api.ts` (client) with
   `api.get('/conversations')` / `api.post('/auth/login', body)` would shrink
   every hook and centralize error normalization. Today, error handling is
   inconsistent: `use-config` throws a generic `Error('Failed to fetch
   configuration')`, `use-auth` reads `data.error ?? 'Request failed'`,
   `use-knowledge` reads `err.error`. One shape, please.
2. **`lib/backend.ts` is server-only but not marked or separated.** It imports
   `NextRequest` and reads `process.env.BACKEND_URL` — importing it from a
   client component would crash at build. It's only imported by route handlers
   today, so it's safe, but adding `'server-only'` (already a Next built-in)
   would make the boundary a hard error instead of a convention. One line.
3. **Type sharing with backend is manual and lives in one file.**
   `web/src/types.ts` hand-mirrors backend DTOs: `RAGContext`, `RAGMetrics`,
   `RAGResult`, `TrajectoryStep`, `ChatMessage`, `User`, `Conversation`,
   `StoredMessage`, `Experiment`, `ModelOption`, `EmbeddingOption`,
   `PipelineOption`, `Document`. There is no OpenAPI/JSON-schema codegen, no
   shared package, no `zod` runtime validation. Drift is silent: if FastAPI
   renames `conversation_id` to `conv_id`, the SSE handler in
   `use-chat-stream.ts` silently stops matching. For the current size this is
   an acceptable trade-off, but it's the single biggest correctness risk in
   the frontend. Mitigations, in increasing order of effort:
   - add a `zod` schema for the SSE event shapes and parse in `parseSSEBlock`;
   - or generate `types.ts` from FastAPI's OpenAPI (`pydantic2ts` or
     `openapi-typescript`) as a CI step. Either makes drift loud.
4. **No `lib/auth.ts` for client.** Auth state lives entirely in
   `hooks/use-auth.ts` (the `fetchMe`/`postAuth`/`useLogin`/`useRegister`/
   `useLogout` cluster). That's fine, but the `User` type it returns comes
   from the single `types.ts` barrel. If `types.ts` grows, consider splitting
   domain types (`lib/types/chat.ts`, `lib/types/auth.ts`) — but YAGNI today.

## Naming & Convention Findings (concrete, with paths)

**Consistent (good).**
- Files: kebab-case everywhere (`message-item.tsx`, `use-chat-stream.ts`,
  `app-shell.tsx`). No PascalCase files, no mixed case. Verified across all
  13 components, 6 hooks, 12 route handlers.
- Component exports: PascalCase (`MessageList`, `AppShell`, `QueryProvider`).
- Hooks: all `use*`, exported as named functions (`useAuth`, `useConfig`,
  `useChatStream`, `useConversations`, `useExperiments`, `useKnowledge`).
  No default exports from hooks (good).
- Route handlers: all export `async function GET/POST/...` named exports.
  Consistent.

**Concrete inconsistencies.**
1. **Pages use `export default`, components use named exports.** Every
   `app/*/page.tsx` does `export default function ChatPage()`; every component
   in `components/` does `export function Composer(...)`. App Router *requires*
   default for `page.tsx`/`layout.tsx`, so this is correct, not a bug — but
   components are named-export-only while pages are default-only. Pick a
   project rule and write it down (e.g. "components: named; pages: default;
   hooks: named") so a new contributor doesn't guess.
2. **Inline color logic duplicated.** `chat/page.tsx` defines
   `providerColor(provider)` and `pipelineColorMap` at module top;
   `knowledge/page.tsx` redefines analogous `bg-cyan-400`/`bg-emerald-500/10`
   semantic color pairs; `model-selector.tsx` hardcodes `bg-slate-900` for
   `<option>`. There's no shared `lib/provider-colors.ts`. Minor, but if a
   provider is added you edit two files. Extract one map.
3. **`useConversation` (named, exported) is unused by the only place that
   would want it** (`chat/page.tsx` uses raw `fetch`). Either dead code or a
   leftover — flag with a grep, then either wire it in or delete it. Don't
   leave a hook exported-but-unused.
4. **`auth-shell.tsx` is a mini form library.** It exports `AuthShell`,
   `Field`, `SubmitButton` from one file (`components/auth-shell.tsx`).
   That's fine for three things, but if more form primitives appear they
   should go into a `components/ui/` (see §7). Don't grow `auth-shell.tsx` into
   a general form kit.
5. **`global.d.ts` is essentially empty** (`declare module '*.css'`). With
   Tailwind v4 CSS-first this may be unnecessary; verify `tsc` still needs it
   before deleting. Low priority.

## Theming Consistency

The token system in `app/globals.css` is **good**: `:root, .dark` and `.light`
define `--accent`, `--accent-2`, `--bg-0..2`, `--text`, `--text-muted`,
`--surface`, `--border`, `--panel`, etc. Semantic utilities (`.text-primary`,
`.text-muted`, `.surface`, `.border-base`, `.glass-panel`, `.space-bg`,
`.neon-ring`) are all var-driven. `theme-toggle.tsx` toggles `.light`/`.dark`
on `<html>` and persists to `localStorage`. The pre-paint script in
`layout.tsx` prevents FOUC. This is a solid, minimal theming system.

**Real leaks (theme breaks in light mode).**
1. **`<option>` elements hardcode `bg-slate-900`** in
   `components/model-selector.tsx` (lines ~45, ~52) and `app/knowledge/page.tsx`
   (line ~80). In light mode, the native dropdown will render a dark
   background inside a light page. Fix: drop the `bg-slate-900` class and let
   options inherit, or add a `--option-bg` token. Two files, ~4 occurrences.
2. **`experiments/page.tsx` uses Tailwind `dark:` variants** that don't match
   the project's class strategy. Lines ~17-22:
   ```
   text-red-600 dark:text-red-400
   text-gray-500 dark:text-gray-400
   border-blue-500
   ```
   Tailwind v4's `dark:` keys off `prefers-color-scheme` by default unless you
   configure a `@custom-variant dark (&:where(.dark, .dark *))`. The project
   uses a `.dark` class on `<html>`, so these `dark:` utilities likely never
   activate (or activate based on OS preference, which is wrong). This is
   leftover code from before the theme migration. Fix: replace with
   token-based classes (`text-rose-400/90`, `text-muted`, `border-base`) or
   add the `@custom-variant` to `globals.css`. One file, ~3 lines.
3. **Error styling hardcodes `text-rose-400/90` + `bg-rose-500/10`** in
   `login/page.tsx`, `register/page.tsx`, `use-auth.ts`-adjacent surfaces.
   Acceptable (red-for-error is conventional and theme-stable enough), but if
   you want full token discipline add `--error` / `--error-surface` tokens.

**Acceptable, not leaks.** The `bg-cyan-400`/`bg-violet-500`/`bg-emerald-500`
dots in `chat/page.tsx`'s `pipelineColorMap` and `providerColor`, and the
`from-cyan-500 to-violet-600` brand gradient, are **semantic/brand colors**,
not theme-surface colors. They read fine on both themes. Don't token-ize these
— they're intentionally fixed.

The recent migration of ~20 components to tokens is largely consistent. The
three issues above are the residual surface area.

## Recommended Restructuring (concrete proposed target layout, minimal, prioritized P0/P1/P2)

Proposed target (incremental — each level is independently shippable):

```
web/src/
  app/
    layout.tsx                      (unchanged: <html><body>, theme script)
    (auth)/
      layout.tsx                    (NEW: bare shell, replaces BARE_ROUTES hack)
      login/page.tsx                (moved from app/login)
      register/page.tsx             (moved from app/register)
    (app)/
      layout.tsx                    (NEW: <QueryProvider><AppShell>{children})
      chat/page.tsx  agents/  knowledge/  memory/  experiments/  evaluations/
      loading.tsx                   (NEW: shared loading shell)
      error.tsx                     (NEW: shared error boundary)
      not-found.tsx                 (NEW)
    api/...                         (unchanged)
  components/
    ui/                             (NEW, P1: shared primitives)
      button.tsx  input.tsx  card.tsx  spinner.tsx  select.tsx
    chat/                           (NEW, P1: chat-domain group, optional)
      message-list.tsx  message-item.tsx  composer.tsx  conversation-sidebar.tsx
      model-selector.tsx
    app-shell.tsx  left-nav.tsx  command-palette.tsx  user-menu.tsx
    tenant-switcher.tsx  theme-toggle.tsx  query-provider.tsx  auth-shell.tsx
  hooks/        (unchanged)
  lib/
    backend.ts                      (add `import 'server-only'`)
    api.ts                          (NEW, P0: client fetch wrapper, used by hooks)
    provider-colors.ts              (NEW, P1: shared provider/pipeline color map)
    utils.ts                        (unchanged)
  types.ts                          (P1: consider zod schemas for SSE events)
  stores/                           (P0: delete, empty)
```

**P0 — do first (tiny diffs, high signal, zero risk).**
- Delete `web/src/stores/` (empty) and remove `zustand` from `package.json`.
  Touches: `package.json`, `web/src/stores/`. No code changes.
- Add `import 'server-only'` to `web/src/lib/backend.ts`. One line. Makes the
  server/client boundary a hard error.
- Fix the three theming leaks: drop `bg-slate-900` from `model-selector.tsx`
  and `knowledge/page.tsx`; replace `dark:` variants in `experiments/page.tsx`
  with token classes. Touches 3 files, ~8 lines.
- Wire `useConversation` into `chat/page.tsx` *or* delete `useConversation`
  from `use-conversations.ts`. Today it's exported, unused, and the chat page
  hand-rolls a duplicate fetch. Pick one. Touches 1-2 files.

**P1 — structural, do once, ship as one PR.**
- Introduce route groups `(auth)` and `(app)` with their own layouts; delete
  `BARE_ROUTES` from `app-shell.tsx`. Touches: `app/login/`, `app/register/`
  (moved), new `app/(auth)/layout.tsx`, new `app/(app)/layout.tsx`,
  `app/layout.tsx` (slimmed), `components/app-shell.tsx` (drops the
  pathname check). Moves only — no behavior change.
- Add `lib/api.ts` (client) and route all hook `fetch` calls through it;
  normalize error shape to one `ApiError`. Touches: new `lib/api.ts`, all 6
  hooks. Mechanical.
- Add `app/(app)/loading.tsx` + `error.tsx` + `not-found.tsx`. Removes the
  per-page inline spinners. Touches: 3 new files, then simplify
  `experiments/page.tsx` (and any other page with an inline spinner).
- Extract `lib/provider-colors.ts` from `chat/page.tsx` and `knowledge/page.tsx`.
  Touches: new file, 2 consumers.

**P2 — defer until there's a concrete need.**
- A `components/ui/` primitive set (Button/Input/Card/Select/Spinner). Only
  worth it once a 4th or 5th form page appears; right now `auth-shell.tsx`
  covers the only forms. Don't build it speculatively.
- Split `types.ts` into `lib/types/{chat,auth,config,document}.ts`. Only when
  it crosses ~200 lines or two unrelated domains start importing each other.
- OpenAPI/`openapi-typescript` codegen from FastAPI, or `zod` runtime parsing
  of SSE events in `use-chat-stream.ts`. This is the highest-value P2:
  it kills the silent-drift risk called out in §3.3. Start with zod on the
  SSE event shapes (one file, `use-chat-stream.ts`), graduate to full codegen
  if the backend schema churns.
- A `components/chat/` subgroup. Only worth it once `components/` crosses
  ~20 files; today 13 flat files is fine.

## Risk & Dependency Impact (blast radius of renames/restructure)

- **Delete `stores/` + `zustand` (P0):** zero imports, zero usages. Safe. Run
  `pnpm install` to lock the dep removal; `tsc --noEmit` and `next build`
  should be unchanged.
- **Theme leak fixes (P0):** 3 files, ~8 lines, visual-only. Test by
  toggling theme on `/experiments`, `/knowledge`, and opening a model
  `<select>` dropdown in light mode. No type risk.
- **`useConversation` deletion (P0):** grep confirms no import of
  `useConversation` outside its own file; `chat/page.tsx` imports `StoredMessage`
  from types but not the hook. Safe to delete. Wiring it *in* instead is a
  slightly bigger change (the chat page's `handleSelect` would become a
  `useEffect` on `activeId` + a `useMemo` mapping `StoredMessage[]` →
  `ChatMessage[]`); test conversation switching and "new chat" reset.
- **Route groups `(auth)`/`(app)` (P1):** moves 9 page files into folders.
  URLs do **not** change (route groups are URL-transparent). Risk is in the
  layout split: `app/layout.tsx` currently mounts `QueryProvider` + `AppShell`
  globally. After the split, `(auth)/layout.tsx` must render children bare
  (no AppShell) but still wrap in `QueryProvider` if auth hooks are used
  during login/register (they are — `useLogin`/`useRegister` use React Query).
  Easiest: keep `QueryProvider` in the root `app/layout.tsx`, move only
  `AppShell` into `(app)/layout.tsx`. Verify the login flow still has query
  client context. One CI run catches it.
- **`lib/api.ts` (P1):** touches all 6 hooks mechanically. Risk: error
  shapes change for consumers. Audit every `error.message` read site (login,
  register, knowledge upload) and update. One PR, ~6 files.
- **`loading.tsx`/`error.tsx` (P1):** adding them is additive; the only
  risk is double spinners if a page still renders its own. Remove the inline
  spinner in `experiments/page.tsx` in the same PR.
- **`components/ui/` and `components/chat/` (P2):** pure moves with import-path
  updates. `@/components/message-list` → `@/components/chat/message-list`.
  Blast radius is every importer (mostly `chat/page.tsx`). Low risk, low
  value at current size — defer.
- **OpenAPI codegen (P2):** introduces a build step and a contract between
  repos. Blast radius is `types.ts` (regenerated) and any hand-written type
  that diverges. Coordinate with backend owner. High value, medium effort,
  do last.

The single highest-leverage change is **zod parsing of SSE events in
`use-chat-stream.ts`** (P2): it's a one-file change that turns the biggest
silent-failure mode (backend renames an SSE field) into a loud runtime error
during development. Everything else is hygiene.