# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportUnnecessaryComparison=false
import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app as main_app
from app.routers import chat as chat_module

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _oci_configured() -> bool:
    """True if OCI chat is configured (compartment + client available)."""
    if not os.getenv("OCI_COMPARTMENT_ID"):
        return False
    try:
        from app.config import client, compartment_id
        return client is not None and compartment_id is not None
    except Exception:
        return False


@pytest.fixture()
def api_client(monkeypatch):
    monkeypatch.setattr(chat_module, "client", object())
    monkeypatch.setattr(chat_module, "compartment_id", "ocid1.test")
    return TestClient(main_app)


@pytest.fixture()
def live_api_client():
    """TestClient with real app (no mocks). For live OCI tests only."""
    return TestClient(main_app)


def _completion_with_tool(tool_name: str):
    tool_call = {
        "id": "call_123",
        "type": "function",
        "function": {"name": tool_name, "arguments": "{}"},
    }
    message = SimpleNamespace(content="", tool_calls=[tool_call])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _completion_with_content(text: str):
    message = SimpleNamespace(content=text, tool_calls=[])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _mock_run_completion(monkeypatch, factory):
    async def _fake_run_completion(**kwargs):
        return factory()

    monkeypatch.setattr(chat_module, "_run_completion", _fake_run_completion)


def test_non_stream_tool_call_forwarded(monkeypatch, api_client):
    _mock_run_completion(monkeypatch, lambda: _completion_with_tool("run_oci_command"))

    payload = {
        "model": "meta.llama-test",
        "messages": [{"role": "user", "content": "Call a tool"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "run_oci_command",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ],
    }

    response = api_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    body = response.json()

    choice = body["choices"][0]
    assert choice["finish_reason"] == "tool_calls"
    assert choice["message"]["tool_calls"][0]["function"]["name"] == "run_oci_command"


def test_streaming_plain_text_chunks(monkeypatch, api_client):
    _mock_run_completion(monkeypatch, lambda: _completion_with_content("Hello from backend"))

    payload = {
        "model": "meta.llama-test",
        "messages": [{"role": "user", "content": "Say hello"}],
        "stream": True,
    }

    with api_client.stream("POST", "/v1/chat/completions", json=payload) as response:
        assert response.status_code == 200
        body = b"".join(response.iter_bytes()).decode()

    assert '"role": "assistant"' in body
    assert "Hello from backend" in body
    assert '"finish_reason": "stop"' in body


def test_streaming_tool_call_forwarded(monkeypatch, api_client):
    _mock_run_completion(monkeypatch, lambda: _completion_with_tool("search_knowledge_base"))

    payload = {
        "model": "meta.llama-test",
        "messages": [{"role": "user", "content": "Need tool"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ],
        "stream": True,
    }

    with api_client.stream("POST", "/v1/chat/completions", json=payload) as response:
        assert response.status_code == 200
        body = b"".join(response.iter_bytes()).decode()

    assert '"tool_calls"' in body
    assert '"finish_reason": "tool_calls"' in body


def test_non_stream_plain_text(monkeypatch, api_client):
    _mock_run_completion(monkeypatch, lambda: _completion_with_content("Hello world"))

    payload = {
        "model": "meta.llama-test",
        "messages": [{"role": "user", "content": "Say hello"}],
    }

    response = api_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["object"] == "chat.completion"
    assert body["model"] == "meta.llama-test"
    assert "id" in body
    assert "created" in body

    choice = body["choices"][0]
    assert choice["message"]["role"] == "assistant"
    assert choice["message"]["content"] == "Hello world"
    assert choice["finish_reason"] == "stop"


def test_accepts_tool_role_messages(monkeypatch, api_client):
    _mock_run_completion(monkeypatch, lambda: _completion_with_content("OK"))

    payload = {
        "model": "meta.llama-test",
        "messages": [
            {"role": "user", "content": "Run a tool and continue"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "run_oci_command", "arguments": "{}"},
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "call_123", "content": "{}"},
        ],
    }

    response = api_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["object"] == "chat.completion"
    choice = body["choices"][0]
    assert choice["message"]["role"] == "assistant"
    assert choice["message"]["content"] == "OK"
    assert choice["finish_reason"] == "stop"


def _assert_openai_error_envelope(body: dict[str, object]):
    assert isinstance(body, dict)
    assert "error" in body
    err = body["error"]
    assert isinstance(err, dict)
    assert "message" in err
    assert "type" in err
    assert "param" in err
    assert "code" in err
    return err


def test_validation_error_returns_openai_envelope(api_client):
    payload = {
        "messages": [{"role": "user", "content": "Hi"}],
        "stream": False,
    }

    response = api_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 400
    err = _assert_openai_error_envelope(response.json())
    assert err["type"] == "invalid_request_error"
    assert isinstance(err["message"], str) and len(err["message"]) > 0
    assert "model" in err["message"].lower()


def test_http_exception_returns_openai_envelope_messages_required(api_client):
    payload = {
        "model": "meta.llama-test",
        "messages": [],
        "stream": False,
    }

    response = api_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 400
    err = _assert_openai_error_envelope(response.json())
    assert "messages are required" in (err["message"] or "").lower()


def test_empty_content_returns_no_response_generated_fallback(monkeypatch, api_client):
    _mock_run_completion(monkeypatch, lambda: _completion_with_content(""))

    payload = {
        "model": "meta.llama-test",
        "messages": [{"role": "user", "content": "Say something"}],
        "stream": False,
    }

    response = api_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "chat.completion"
    choice = body["choices"][0]
    assert choice["finish_reason"] == "stop"
    assert choice["message"]["content"] == "(No response generated.)"


# ---- Live tests (real OCI backend). Skipped when OCI not configured. ----
_live_mark = pytest.mark.skipif(
    not _oci_configured(),
    reason="OCI_COMPARTMENT_ID and OCI config required for live chat tests",
)


@_live_mark
def test_chat_completion_live(live_api_client):
    """Non-stream chat completion against real OCI. Asserts 200 and valid completion."""
    payload = {
        "model": os.getenv("MODEL_ID", "meta.llama-4-scout-17b-16e-instruct"),
        "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
    }
    response = live_api_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("object") == "chat.completion"
    assert "choices" in body and len(body["choices"]) >= 1
    choice = body["choices"][0]
    assert choice["message"]["role"] == "assistant"
    assert choice["finish_reason"] == "stop"
    # Content may be "OK" or a longer reply; ensure we got some text
    content = choice["message"].get("content") or ""
    assert isinstance(content, str)
    assert len(content.strip()) >= 1


@_live_mark
def test_chat_completion_stream_live(live_api_client):
    """Streaming chat completion against real OCI. Asserts 200 and SSE with assistant content."""
    payload = {
        "model": os.getenv("MODEL_ID", "meta.llama-4-scout-17b-16e-instruct"),
        "messages": [{"role": "user", "content": "Say hello in one word."}],
        "stream": True,
    }
    with live_api_client.stream("POST", "/v1/chat/completions", json=payload) as response:
        assert response.status_code == 200, (response.headers, response.iter_bytes())
        body = b"".join(response.iter_bytes()).decode()
    assert '"role": "assistant"' in body or "assistant" in body
    assert '"finish_reason": "stop"' in body or '"finish_reason":"stop"' in body
    # Should have at least one content delta
    assert "content" in body or "delta" in body.lower()


def _search_knowledge_base_tool_schema():
    """Real search_knowledge_base tool schema (matches run_rag_tool_client / MCP)."""
    default_table = os.getenv("ORACLE_TABLE_NAME", "web_embeddings")
    return {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the Oracle 23ai knowledge base for information. "
                "Call this when the user asks to search the knowledge base or get answers from the RAG database."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language query for the knowledge base."},
                    "top_k": {"type": "integer", "description": "Number of rows (1-20).", "default": 5},
                    "table_name": {"type": "string", "description": "Oracle table to query.", "default": default_table},
                },
                "required": ["query"],
            },
        },
    }


@_live_mark
def test_chat_tool_call_search_knowledge_base_live(live_api_client):
    """Live: request with real search_knowledge_base tool; assert OCI returns tool_calls and we forward them."""
    payload = {
        "model": os.getenv("MODEL_ID", "meta.llama-4-scout-17b-16e-instruct"),
        "messages": [
            {"role": "user", "content": "Search the knowledge base for: OIC URL. Call the search_knowledge_base tool with that query."},
        ],
        "tools": [_search_knowledge_base_tool_schema()],
        "stream": False,
    }
    response = live_api_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("object") == "chat.completion"
    assert "choices" in body and len(body["choices"]) >= 1
    choice = body["choices"][0]
    assert choice["message"]["role"] == "assistant"
    # Backend forwards tool_calls from OCI; we expect the model to call search_knowledge_base
    assert choice["finish_reason"] == "tool_calls", (
        f"Expected tool_calls, got finish_reason={choice['finish_reason']!r} and message={choice['message']!r}"
    )
    tool_calls = choice["message"].get("tool_calls") or []
    names = [tc["function"]["name"] for tc in tool_calls if isinstance(tc.get("function"), dict)]
    assert "search_knowledge_base" in names, f"Expected search_knowledge_base in tool_calls, got {names}"
