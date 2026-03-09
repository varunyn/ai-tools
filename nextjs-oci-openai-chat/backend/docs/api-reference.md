# Backend API Reference

Base URL (local): `http://localhost:3001`

This backend exposes OpenAI-compatible endpoints plus lightweight compatibility routes.

## Health and Service Info

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Service metadata and endpoint pointers |
| GET | `/v1` | Versioned API root summary |
| GET | `/v1/` | Same as `/v1` |
| GET | `/health` | Liveness probe |

## Models

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/chat/models` | UI-friendly model list from `AVAILABLE_MODELS` |
| GET | `/v1/models` | OpenAI-compatible models list |
| GET | `/api/v1/models` | Alias of `/v1/models` |
| GET | `/v1/tags` | Ollama-style tags response |
| GET | `/api/tags` | Alias of `/v1/tags` |

## Chat

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/chat` | Simpler chat payload shape |
| POST | `/v1/chat/completions` | OpenAI-compatible chat completions |
| POST | `/api/v1/chat/completions` | Alias of `/v1/chat/completions` |

### Chat behavior notes

- `stream: true` returns Server-Sent Events (SSE) chunks.
- Backend forwards `tool_calls` but does **not** execute tools.
- If `tool_calls` are returned by the model, client must execute tools and send follow-up messages.

## Responses API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/v1/responses` | OpenAI Responses-compatible route |
| POST | `/api/responses` | Alias of `/v1/responses` |

### Responses behavior notes

- `stream: true` returns SSE.
- OCI model support is prefix-gated in this app (`openai.gpt*`, `xai.grok*`).
- Unsupported model families should use `/v1/chat/completions`.

## Error Envelope

OpenAI-style errors are returned as:

```json
{
  "error": {
    "message": "...",
    "type": "invalid_request_error",
    "param": null,
    "code": null
  }
}
```
