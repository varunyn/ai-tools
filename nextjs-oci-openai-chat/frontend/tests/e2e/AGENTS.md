# AGENTS — `frontend/tests/e2e/`

## OVERVIEW
Playwright E2E tests that validate the tool-call loop end-to-end using deterministic mock servers (mock OpenAI backend + mock MCP servers).

## WHERE TO LOOK
| Task | Location | Notes |
|---|---|---|
| Main E2E test | `tool-loop.spec.ts` | Sends a chat prompt and asserts tool UI + final assistant output. |
| Mock OpenAI backend | `servers/mock-openai-backend.ts` | Implements `/v1/chat/completions` including SSE streaming (`stream: true`) and tool_calls. |
| Mock MCP servers | `servers/mock-mcp-calculator.ts`, `servers/mock-mcp-rag.ts` | Minimal JSON-RPC handlers for `initialize`, `tools/list`, `tools/call`. |

## RUNNING
```bash
cd frontend
pnpm exec playwright test
```

## PORTS / ENV
- Playwright runs Next dev server on **port 4000** (see `frontend/playwright.config.ts`).
- Mock servers use:
  - OpenAI backend: 4545 (`FASTAPI_BACKEND_URL=http://localhost:4545`)
  - MCP calculator: 3020 (`MCP_CALCULATOR_URL=http://localhost:3020/mcp`)
  - MCP RAG: 3021 (`MCP_ORACLE_RAG_URL=http://localhost:3021/mcp`)

## ARTIFACTS
- `test-results/` and `playwright-report/` are ignored via `frontend/.gitignore`.
