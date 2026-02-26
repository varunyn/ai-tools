# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnusedParameter=false, reportAny=false

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app as main_app
from app.routers import chat as chat_module


def _make_fake_client(*, content: str, tool_calls: list[dict[str, object]] | None = None):
    tool_calls = tool_calls or []

    def _create(**_kwargs):
        message = SimpleNamespace(content=content, tool_calls=tool_calls)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=_create)))


def _assert_openai_error_envelope(body: dict[str, object]):
    assert "error" in body
    err = body["error"]
    assert isinstance(err, dict)
    required = {"message", "type", "param", "code"}
    assert required.issubset(err.keys())


def test_api_chat_happy_path_returns_role_and_content(monkeypatch):
    fake_client = _make_fake_client(content="hi")
    monkeypatch.setattr(chat_module, "client", fake_client)
    monkeypatch.setattr(chat_module, "compartment_id", "ocid1.test")

    api_client = TestClient(main_app)
    response = api_client.post(
        "/api/chat",
        json={
            "messages": [
                {"role": "user", "content": "hello"},
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "assistant"
    assert body["content"] == "hi"


def test_api_chat_tool_calls_forwarded(monkeypatch):
    tool_call: dict[str, object] = {
        "id": "call_123",
        "type": "function",
        "function": {"name": "search_knowledge_base", "arguments": "{}"},
    }
    fake_client = _make_fake_client(content="", tool_calls=[tool_call])
    monkeypatch.setattr(chat_module, "client", fake_client)
    monkeypatch.setattr(chat_module, "compartment_id", "ocid1.test")

    api_client = TestClient(main_app)
    response = api_client.post(
        "/api/chat",
        json={
            "messages": [
                {"role": "user", "content": "Call a tool"},
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()

    assert body["role"] == "assistant"
    assert "tool_calls" in body
    assert len(body["tool_calls"]) == 1
    assert body["tool_calls"][0]["id"] == "call_123"
    assert body["tool_calls"][0]["function"]["name"] == "search_knowledge_base"
    assert body["tool_calls"][0]["function"]["arguments"] == "{}"


def test_api_chat_errors_client_missing(monkeypatch):
    monkeypatch.setattr(chat_module, "client", None)
    monkeypatch.setattr(chat_module, "compartment_id", "ocid1.test")

    api_client = TestClient(main_app)
    response = api_client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )
    assert response.status_code == 500
    body = response.json()
    _assert_openai_error_envelope(body)


def test_api_chat_errors_messages_required(monkeypatch):
    fake_client = _make_fake_client(content="hi")
    monkeypatch.setattr(chat_module, "client", fake_client)
    monkeypatch.setattr(chat_module, "compartment_id", "ocid1.test")

    api_client = TestClient(main_app)
    response = api_client.post(
        "/api/chat",
        json={"messages": []},
    )
    assert response.status_code == 400
    body = response.json()
    _assert_openai_error_envelope(body)


def test_api_chat_errors_compartment_missing(monkeypatch):
    fake_client = _make_fake_client(content="hi")
    monkeypatch.setattr(chat_module, "client", fake_client)
    monkeypatch.setattr(chat_module, "compartment_id", None)

    api_client = TestClient(main_app)
    response = api_client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )
    assert response.status_code == 500
    body = response.json()
    _assert_openai_error_envelope(body)
