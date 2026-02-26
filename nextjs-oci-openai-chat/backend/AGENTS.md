# AGENTS — `backend/`

## OVERVIEW

FastAPI service that proxies OpenAI-compatible chat requests to OCI Generative AI, enforcing “tools are executed outside FastAPI”. Everything runs under Python 3.10+ with `uv`.

## STRUCTURE

| Path                  | Purpose                                                                 |
| --------------------- | ----------------------------------------------------------------------- |
| `app/main.py`         | Builds the FastAPI app, registers routers + middleware.                 |
| `app/routers/chat.py` | `/api/chat`, `/v1/chat/completions`, streaming SSE, tool forwarding.    |
| `app/utils.py`        | `_run_completion`, logging helpers, tool-call serialization.            |
| `scripts/`            | Dev helpers (`start_fastapi.sh`, `test_chat_curl.sh`, `test_tools.sh`). |
| `docs/`               | Detailed RAG + tool-forwarding guidance.                                |

Tool clients (Oracle RAG, calculator MCP) live at **repo root** in `tools/`; see root AGENTS.md and `tools/README.md`.

## COMMANDS

```bash
uv sync                                 # install deps
uv run uvicorn app.main:app --reload    # dev server
uv run pytest                           # backend tests
uv run pytest backend/tests/test_chat_completions.py -k stream  # single test
uv run black . && uv run flake8         # format + lint
./scripts/test_chat_curl.sh             # OpenAI parity smoke test
./scripts/test_tools.sh                 # verifies tool forwarding (non-exec)
```

## CONVENTIONS

1. **OCI config** lives at `backend/oci-config` by default; environment overrides via `OCI_CONFIG_FILE`, `OCI_CONFIG_PROFILE`.
2. **Logs** use emoji markers (`📥`, `🔧`, `↪️`). Keep truncation via `_shorten` to avoid leaking prompts or secrets.
3. **Tool calls**: backend never executes them. When `tool_calls` appear, return `_assistant_tool_response` with `finish_reason="tool_calls"` (both streaming + non-streaming). Tool execution happens in Next.js server (MCP) or via root `tools/` harness.
4. **Streaming pattern**: `_run_completion(stream=False)` is invoked first to inspect whether tool calls exist before pushing SSE chunks.
5. **Testing**: only `backend/tests/test_chat_completions.py` exists; it mocks `_run_completion`. Add new tests under `backend/tests/` and use pytest fixtures.

## ANTI-PATTERNS

- Do **not** import or run MCP/Oracle tools inside FastAPI routes—breaks the client-only contract.
- Do **not** log full OCI responses, wallets, or user prompts; always redact via `_shorten`.
- Do **not** bypass `uv` for dependency installs; keep `pyproject.toml` + `uv.lock` as source of truth.

## TIPS

- Use `app/config.py` helpers (`client`, `compartment_id`, `model_id`) instead of rebuilding OCI clients per request.
- CLI smoke tests (`tools/oracle/run_rag_tool_client.py`, `tools/calculator/run_calculator_tool_client.py`) expect environment variables such as `FASTAPI_BACKEND_URL`, `CALCULATOR_MCP_URL`, and Oracle DSN credentials. Run from repo root with `PYTHONPATH=. uv run --project backend python -m tools.*`.
- When adding routers, always include them in `app/main.py` and ensure they respect CORS + logging conventions.

---

Generated 2026-02-16
