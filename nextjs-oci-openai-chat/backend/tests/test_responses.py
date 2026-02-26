# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnusedParameter=false, reportAny=false

from collections.abc import Mapping
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app as main_app
from app.routers import responses as responses_module


def _assert_openai_error_envelope(body: dict[str, object]):
    assert "error" in body
    err = body["error"]
    assert isinstance(err, dict)
    required = {"message", "type", "param", "code"}
    assert required.issubset(err.keys())


class _FakeChunk:
    def __init__(self, payload: Mapping[str, object]):
        self._payload: Mapping[str, object] = payload

    def model_dump(self):
        return self._payload


def test_responses_unsupported_model_prefix_returns_openai_error(monkeypatch):
    def _noop_create(**_kwargs):
        return None

    fake_client_api = SimpleNamespace(responses=SimpleNamespace(create=_noop_create))
    monkeypatch.setattr(responses_module, "client_api", fake_client_api)
    monkeypatch.setattr(responses_module, "compartment_id", "ocid1.test")

    api_client = TestClient(main_app)
    response = api_client.post(
        "/v1/responses",
        json={"model": "meta.llama-3-70b", "input": "hello"},
    )

    assert response.status_code == 400
    _assert_openai_error_envelope(response.json())


def test_responses_client_without_responses_returns_501(monkeypatch):
    fake_client_api = SimpleNamespace()
    monkeypatch.setattr(responses_module, "client_api", fake_client_api)
    monkeypatch.setattr(responses_module, "compartment_id", "ocid1.test")

    api_client = TestClient(main_app)
    response = api_client.post(
        "/v1/responses",
        json={"model": "openai.gpt-4o-mini", "input": "hello"},
    )

    assert response.status_code == 501
    _assert_openai_error_envelope(response.json())


def test_responses_missing_client_api_returns_500(monkeypatch):
    monkeypatch.setattr(responses_module, "client_api", None)
    monkeypatch.setattr(responses_module, "compartment_id", "ocid1.test")

    api_client = TestClient(main_app)
    response = api_client.post(
        "/v1/responses",
        json={"model": "openai.gpt-4o-mini", "input": "hello"},
    )

    assert response.status_code == 500
    _assert_openai_error_envelope(response.json())


def test_responses_missing_compartment_id_returns_500(monkeypatch):
    def _noop_create(**_kwargs):
        return None

    fake_client_api = SimpleNamespace(responses=SimpleNamespace(create=_noop_create))
    monkeypatch.setattr(responses_module, "client_api", fake_client_api)
    monkeypatch.setattr(responses_module, "compartment_id", None)

    api_client = TestClient(main_app)
    response = api_client.post(
        "/v1/responses",
        json={"model": "openai.gpt-4o-mini", "input": "hello"},
    )

    assert response.status_code == 500
    _assert_openai_error_envelope(response.json())


def test_responses_missing_input_returns_400(monkeypatch):
    def _noop_create(**_kwargs):
        return None

    fake_client_api = SimpleNamespace(responses=SimpleNamespace(create=_noop_create))
    monkeypatch.setattr(responses_module, "client_api", fake_client_api)
    monkeypatch.setattr(responses_module, "compartment_id", "ocid1.test")

    api_client = TestClient(main_app)
    response = api_client.post(
        "/v1/responses",
        json={"model": "openai.gpt-4o-mini", "input": ""},
    )

    assert response.status_code == 400
    _assert_openai_error_envelope(response.json())


def test_responses_non_stream_returns_dict_from_model_dump(monkeypatch):
    expected = {"id": "resp_1", "output_text": "ok"}

    def _create(**_kwargs):
        return _FakeChunk(expected)

    fake_client_api = SimpleNamespace(responses=SimpleNamespace(create=_create))
    monkeypatch.setattr(responses_module, "client_api", fake_client_api)
    monkeypatch.setattr(responses_module, "compartment_id", "ocid1.test")

    api_client = TestClient(main_app)
    response = api_client.post(
        "/v1/responses",
        json={"model": "openai.gpt-4o-mini", "input": "hello", "stream": False},
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_responses_non_stream_returns_wrapped_non_dict(monkeypatch):
    def _create(**_kwargs):
        return "ok"

    fake_client_api = SimpleNamespace(responses=SimpleNamespace(create=_create))
    monkeypatch.setattr(responses_module, "client_api", fake_client_api)
    monkeypatch.setattr(responses_module, "compartment_id", "ocid1.test")

    api_client = TestClient(main_app)
    response = api_client.post(
        "/v1/responses",
        json={"model": "openai.gpt-4o-mini", "input": "hello", "stream": False},
    )

    assert response.status_code == 200
    assert response.json() == {"response": "ok"}


def test_responses_stream_sse_yields_chunks_and_done(monkeypatch):
    first_chunk: dict[str, object] = {"id": "chunk_1", "delta": "hi"}
    second_chunk: dict[str, object] = {"id": "chunk_2", "delta": "there"}

    def _create(**_kwargs):
        return iter([
            _FakeChunk(first_chunk),
            _FakeChunk(second_chunk),
        ])

    fake_client_api = SimpleNamespace(responses=SimpleNamespace(create=_create))
    monkeypatch.setattr(responses_module, "client_api", fake_client_api)
    monkeypatch.setattr(responses_module, "compartment_id", "ocid1.test")

    api_client = TestClient(main_app)
    payload = {"model": "openai.gpt-4o-mini", "input": "hello", "stream": True}
    with api_client.stream("POST", "/v1/responses", json=payload) as resp:
        assert resp.status_code == 200
        body = b"".join(resp.iter_bytes()).decode()

    assert "data: " in body
    assert "data: [DONE]" in body
    assert "chunk_1" in body


def test_responses_stream_sse_emits_error_and_done(monkeypatch):
    def _create(**_kwargs):
        raise RuntimeError("stream boom")

    fake_client_api = SimpleNamespace(responses=SimpleNamespace(create=_create))
    monkeypatch.setattr(responses_module, "client_api", fake_client_api)
    monkeypatch.setattr(responses_module, "compartment_id", "ocid1.test")

    api_client = TestClient(main_app)
    payload = {"model": "openai.gpt-4o-mini", "input": "hello", "stream": True}
    with api_client.stream("POST", "/v1/responses", json=payload) as resp:
        assert resp.status_code == 200
        body = b"".join(resp.iter_bytes()).decode()

    assert "data: " in body
    assert "data: [DONE]" in body
    assert "stream boom" in body
