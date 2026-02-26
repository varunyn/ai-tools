# AGENTS — `frontend/`

## OVERVIEW
Next.js 16 App Router UI written in TypeScript + Tailwind CSS, using Vercel AI SDK v6. The `/api/chat` route calls the FastAPI OpenAI-compatible backend and executes tools server-side via MCP.

## STRUCTURE
| Path | Purpose |
| --- | --- |
| `src/app/page.tsx` | Main chat surface. |
| `src/app/api/chat/route.ts` | AI SDK v6 route handler (`streamText`) calling FastAPI `/v1/chat/completions`. |
| `src/lib/mcp/*` | Server-side MCP client + tool discovery/execution. |
| `src/app/api/models/route.ts` | Proxies backend `/api/chat/models` for model selector. |
| `src/components/ui/*` | Shadcn-styled primitives (buttons, dialogs, etc.). |
| `src/components/ai-elements/*` | Streaming-specific widgets (chat bubbles, loaders). |
| `src/lib/` | Utility helpers (class merging, data transforms). |
| `components.json` | Shadcn configuration (aliases: `@/components`, `@/lib/utils`, etc.). |

## COMMANDS
```bash
pnpm install                 # enforced by .cursor rule
pnpm dev                     # http://localhost:3000
pnpm lint                    # ESLint (Next.js config)
pnpm build && pnpm start     # production bundle + serve
pnpm exec playwright test    # E2E (see playwright.config.ts; dev server uses port 4000)
```

## DATA FLOW
* UI components collect AI SDK `messages` (with `parts`).
* `src/app/api/chat/route.ts` is a standard AI SDK v6 handler: `streamText` → `toUIMessageStreamResponse`.
* It calls FastAPI via OpenAI-compatible provider (`/v1/chat/completions`).
* Tools are discovered and executed **server-side** through MCP (`src/lib/mcp/*`), producing tool parts in the UI.

## CONVENTIONS
1. **Package manager**: always use `pnpm` (`pnpm add`, `pnpm lint`, etc.). Delete `package-lock.json` if it reappears.
2. **Imports**: rely on alias map from `components.json` (`@/components`, `@/lib/utils`). Avoid relative hell.
3. **Styling**: Tailwind v4 preview + Shadcn. Keep class strings readable; reuse utilities in `src/lib`.
4. **Components**: React Server Components by default; mark client pieces with `"use client"` when hooks/state required.
5. **Icons/animations**: Lucide + `tw-animate-css`. Keep bundle lean—tree-shake icons.

## ANTI-PATTERNS
* Introducing other package managers (npm/yarn/bun) in scripts or docs.
* Bypassing the `/api/chat` route to call FastAPI directly from client components—keeps credentials server-side.
* Logging sensitive chat content without truncation (mirror backend practice).

## NOTES
* Frontend README is the default Next.js stub; prefer this file for accurate workflow.
* Type defs live in `next-env.d.ts` + `tsconfig.json`; keep strict mode.
* Tailwind config is implicit (v4 preview). Use `src/app/globals.css` for globals; no `tailwind.config.js`.

Generated 2026-02-16
