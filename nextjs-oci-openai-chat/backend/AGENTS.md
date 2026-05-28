# AGENTS — `backend/`

## What matters here

- FastAPI entrypoint is `app/main.py`. It registers `health`, `models`, `chat`, and `responses` routers, adds permissive CORS, and prints `DEBUG REQUEST/RESPONSE` for every request.
- OCI setup in `app/config.py` is easy to break: the backend uses **two** `OciOpenAI` clients.
  - `client_chat` uses a base URL **with** `/actions/v1` for `chat.completions`
  - `client_api` uses a base URL **without** `/actions/v1` for `responses` / conversations
  - Reusing the wrong client/base URL causes 404-style path errors.

## Verified commands

Run from `backend/` unless noted otherwise.

```bash
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
./scripts/start_fastapi.sh

./.venv/bin/python3 -m pytest
./.venv/bin/python3 -m pytest tests/test_responses.py
./.venv/bin/python3 -m pytest tests/test_chat_completions.py -k stream

uv run ruff check app tests
uv run ruff format app tests

./scripts/test_chat_curl.sh
```

## Test/runtime quirks

- `backend/.venv/bin/pytest` may point at a stale absolute path. If `uv run pytest` or the wrapper fails, use `./.venv/bin/python3 -m pytest ...`.
- `pyproject.toml` sets `pythonpath = [".."]` for pytest so tests can import repo-root `tools` modules while running from `backend/`.
- Test coverage is broader than chat-completions only. `backend/tests/` includes responses, chat API, health, models, and utils tests; `tests/conftest.py` prints a custom backend summary table.
- Some live OCI tests are intentionally skipped unless OCI env/config is present.

## Route contracts agents usually guess wrong

- `POST /api/chat`
  - returns `{ "role": "assistant", "content": ... }` for plain responses
  - returns an assistant message with `tool_calls` when OCI asks the client to execute tools
- `POST /v1/chat/completions` and `/api/v1/chat/completions`
  - OpenAI-style JSON envelope for non-stream responses
  - SSE for `stream=true`
  - tool calls are **forwarded**, never executed in FastAPI
- `POST /v1/responses` and `/api/responses`
  - only accepts model ids starting with `openai.gpt` or `xai.grok`
  - rejects other models with an OpenAI-style 400 error envelope
  - structured outputs follow the **Responses API** shape: use `text.format`
  - legacy top-level `response_format` is only a compatibility shim; backend maps it to `text.format`

## Structured output contract

- For `POST /v1/chat/completions`, OpenAI-style structured output belongs on top-level `response_format`.
- For `POST /v1/responses`, OpenAI-style structured output belongs under `text.format`, not top-level `response_format`.
- If debugging “Invalid json output”, check the request shape first before changing parsing logic.

## Constraints to preserve

- Do **not** execute MCP / Oracle / RAG tools inside FastAPI routes. The backend only forwards tool calls to the client.
- Do **not** collapse `client_chat` and `client_api` into one OCI client unless you also rework the base URL rules.
- Keep OpenAI-style error envelopes intact; `app/main.py` converts `HTTPException` and validation errors through `create_openai_error`.
- `scripts/test_chat_curl.sh` is the only verified smoke script under `backend/scripts/`. `test_tools.sh` is not present.
