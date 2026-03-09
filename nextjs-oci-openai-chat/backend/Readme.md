# Backend — FastAPI + OCI Gen AI

FastAPI backend for the OCI OpenAI chat application: OpenAI-compatible chat, optional tool calling, and OCI Generative AI.

## Quick start

From the **backend** directory:

```bash
uv sync
cp env.example .env
# Edit .env (OCI_*, MODEL_*, optional Oracle/RAG vars)

./scripts/start_fastapi.sh
```

Server: **http://localhost:3001**

### OCI configuration

The FastAPI client reads credentials from an OCI config file. By default it looks for `backend/oci-config`:

1. Copy your `~/.oci/config` into `backend/oci-config` (or point `OCI_CONFIG_FILE` to another path).
2. Set `OCI_CONFIG_PROFILE` to the profile name you want (defaults to `CHICAGO`).
3. Ensure the config references the correct key file. Keep private keys out of git.

## Tool forwarding contract

**Tools are not enabled by default.** This backend only forwards `tool_calls`; clients (Next.js server, Open WebUI, or any external helper service) must declare tools in the request and execute them.

## Structure

| Path           | Purpose                                                                                         |
| -------------- | ----------------------------------------------------------------------------------------------- |
| `app/main.py`  | FastAPI app entrypoint (uvicorn target `app.main:app`)                                          |
| `app/routers/` | Chat, models, health, responses                                                                 |
| `tests/`       | Pytest tests (health, models, chat, responses, utils); see [Tests](#tests)                      |
| `scripts/`     | Dev/test helpers (`start_fastapi.sh`, `test_chat_curl.sh`, `test_rag_tool.sh`, `test_tools.sh`) |
| `env.example`  | Required and optional environment variables                                                     |
| `oci-config`   | Local OCI config file used by default (override with `OCI_CONFIG_FILE`)                         |

## Scripts

Run from **backend** directory:

- `./scripts/start_fastapi.sh` — Start dev server (reload)
- `./scripts/test_chat_curl.sh [BASE_URL]` — Smoke test `/v1/chat/completions` (text + streaming)
- `./scripts/test_rag_tool.sh [BASE_URL]` — Ensures RAG tool_calls are forwarded (no execution)
- `./scripts/test_tools.sh [BASE_URL]` — Generic tool forwarding check (non-stream + stream)
- `uv run python scripts/run_conversation_create_test.py` — Exercise the responses/conversation create flow

## Tests

Backend tests live in **`tests/`** and use **pytest** with the FastAPI `TestClient`. Most tests mock OCI and `_run_completion`; a few are live OCI tests and are skip-if-gated when credentials are missing.

### How to run

From the **backend** directory:

```bash
uv sync
uv run pytest
```

| Command                                                                    | Description                            |
| -------------------------------------------------------------------------- | -------------------------------------- |
| `uv run pytest`                                                            | Run all tests                          |
| `uv run pytest tests/test_health.py`                                       | Run one test file                      |
| `uv run pytest tests/test_chat_completions.py -k stream`                   | Run tests whose name contains `stream` |
| `uv run pytest tests/ -v`                                                  | Run all with verbose output            |
| `uv run pytest tests/test_chat_completions.py::test_non_stream_plain_text` | Run a single test                      |

Live OCI tests (e.g. in `test_chat_completions.py`: `test_chat_completion_live`, `test_chat_completion_stream_live`, `test_chat_tool_call_search_knowledge_base_live`) are skipped unless OCI config and `OCI_COMPARTMENT_ID` / `MODEL_ID` are set. To run them, configure `.env` and run the same pytest commands.

### Test modules

| File                       | What it covers                                                                                                    |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `test_health.py`           | Root `/`, `/v1`, `/health`, `/api/tools` responses                                                                |
| `test_models.py`           | `/api/chat/models`, `/v1/models`, `/v1/tags` (OpenAI/Ollama shapes)                                               |
| `test_chat_api.py`         | `POST /api/chat`: happy path, tool forwarding, client/compartment/messages errors                                 |
| `test_chat_completions.py` | `POST /v1/chat/completions`: streaming/non-stream, tool_calls, validation/HTTP error envelopes, live OCI (skipif) |
| `test_responses.py`        | OCI Responses API: create (stream/non-stream), error mapping, missing client/compartment/input                    |
| `test_utils_tools.py`      | `_tool_call_name`, `_tool_call_arguments`, `_assistant_tool_response`, `_shorten`                                 |
| `test_utils_errors.py`     | `create_openai_error` shape, `_conversation_error_response` (404/override), `_to_jsonable`                        |
| `conftest.py`              | Shared fixtures: `client` (TestClient), `api_client`, `live_api_client` (skipif), and optional summary hooks      |

For a quick sanity check after changes: `uv run pytest tests/test_health.py tests/test_models.py tests/test_utils_tools.py tests/test_utils_errors.py`.

## Client-provided tools only

The backend does not define or execute tools. Tool definitions come from the client; when the model returns `tool_calls`, the backend forwards them to the client for execution in an OpenAI-compatible format.

## Docker / Compose

If you prefer containers, the repo root includes `docker-compose.yml` that brings up both frontend and backend:

```bash
docker compose build
docker compose up -d
```

- Backend will be reachable on `http://localhost:3001` (same as dev script).
- Frontend maps to `http://localhost:3040` (container port 3000).
- Stop with `docker compose down` (add `-v` to drop volumes).

Run these commands from the repository root, not from `backend/`.
