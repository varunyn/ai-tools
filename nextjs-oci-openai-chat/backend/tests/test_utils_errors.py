import json

from typing import cast

from fastapi.responses import JSONResponse

from app.utils import create_openai_error, _conversation_error_response, _to_jsonable  # pyright: ignore[reportPrivateUsage]


def _json_body(resp: JSONResponse) -> dict[str, object]:
    body_bytes = cast(bytes, resp.body)
    return cast(dict[str, object], json.loads(body_bytes.decode("utf-8")))


def test_create_openai_error_shape():
    resp = create_openai_error(
        message="Bad request",
        type="invalid_request_error",
        code="bad_request",
        status_code=418,
    )

    assert resp.status_code == 418

    body = _json_body(resp)
    assert "error" in body
    err = cast(dict[str, object], body["error"])
    assert err["message"] == "Bad request"
    assert err["type"] == "invalid_request_error"
    assert err["param"] is None
    assert err["code"] == "bad_request"


def test_conversation_error_response_not_found_maps_404():
    resp = _conversation_error_response(Exception("Not Found"))
    assert resp.status_code == 404

    body = _json_body(resp)
    err = cast(dict[str, object], body["error"])
    assert err["type"] == "invalid_request_error"
    assert err["message"] == "Not Found"
    assert err["param"] is None
    assert err["code"] is None


def test_conversation_error_response_on_create_overrides_message():
    resp = _conversation_error_response(Exception("Not Found"), on_create=True)
    assert resp.status_code == 404

    body = _json_body(resp)
    err = cast(dict[str, object], body["error"])
    assert err["type"] == "invalid_request_error"
    assert "Conversations API is not available" in cast(str, err["message"])


def test_to_jsonable_prefers_model_dump_then_dict_then_str():
    class HasModelDump:
        a: int

        def model_dump(self):
            return {"a": 1}

        def __init__(self):
            self.a = 999

    class HasDict:
        x: int

        def __init__(self):
            self.x = 2

    assert _to_jsonable(HasModelDump()) == {"a": 1}
    assert _to_jsonable(HasDict()) == {"x": 2}
    assert _to_jsonable(123) == "123"
