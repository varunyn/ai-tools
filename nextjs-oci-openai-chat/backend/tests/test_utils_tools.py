from typing import cast
from types import SimpleNamespace

from app.utils import (
    _assistant_tool_response,  # pyright: ignore[reportPrivateUsage]
    _shorten,  # pyright: ignore[reportPrivateUsage]
    _tool_call_arguments,  # pyright: ignore[reportPrivateUsage]
    _tool_call_name,  # pyright: ignore[reportPrivateUsage]
)


def test_tool_call_name_arguments_dict_shape():
    tc = {"function": {"name": "search_knowledge_base", "arguments": '{"q":"oci"}'}}
    assert _tool_call_name(tc) == "search_knowledge_base"
    assert _tool_call_arguments(tc) == '{"q":"oci"}'


def test_tool_call_name_arguments_object_shape():
    tc = SimpleNamespace(function=SimpleNamespace(name="calculator", arguments='{"expr":"2+2"}'))
    assert _tool_call_name(tc) == "calculator"
    assert _tool_call_arguments(tc) == '{"expr":"2+2"}'


def test_assistant_tool_response_normalizes_multiple_tool_calls():
    dict_tc_missing_args = {"id": "call_1", "type": "function", "function": {"name": "calculator"}}

    obj_tc_default_type = SimpleNamespace(
        id="call_2",
        function=SimpleNamespace(name="search_knowledge_base", arguments='{"q":"oci"}'),
    )

    obj_tc_missing_args = SimpleNamespace(id="call_3", type="function", function=SimpleNamespace(name="noop"))

    message = SimpleNamespace(content=None, tool_calls=[dict_tc_missing_args, obj_tc_default_type, obj_tc_missing_args])
    out = _assistant_tool_response(message)

    assert out["role"] == "assistant"
    assert out["content"] == ""
    tool_calls = cast(list[dict[str, object]], out["tool_calls"])
    assert isinstance(tool_calls, list)
    assert len(tool_calls) == 3

    by_id: dict[str, dict[str, object]] = {cast(str, tc["id"]): tc for tc in tool_calls}
    assert set(by_id) == {"call_1", "call_2", "call_3"}

    for tc in by_id.values():
        assert "id" in tc
        assert "type" in tc
        assert "function" in tc
        fn = cast(dict[str, object], tc["function"])
        assert "name" in fn
        assert "arguments" in fn
        assert isinstance(fn["arguments"], str)

    call_1 = by_id["call_1"]
    call_1_fn = cast(dict[str, object], call_1["function"])
    assert cast(str, call_1["type"]) == "function"
    assert cast(str, call_1_fn["name"]) == "calculator"
    assert cast(str, call_1_fn["arguments"]) == "{}"

    call_2 = by_id["call_2"]
    call_2_fn = cast(dict[str, object], call_2["function"])
    assert cast(str, call_2["type"]) == "function"
    assert cast(str, call_2_fn["name"]) == "search_knowledge_base"
    assert cast(str, call_2_fn["arguments"]) == '{"q":"oci"}'

    call_3 = by_id["call_3"]
    call_3_fn = cast(dict[str, object], call_3["function"])
    assert cast(str, call_3["type"]) == "function"
    assert cast(str, call_3_fn["name"]) == "noop"
    assert cast(str, call_3_fn["arguments"]) == "{}"


def test_shorten_truncates_and_appends_suffix():
    s = "abcdefghijklmnopqrstuvwxyz"
    out = _shorten(s, max_chars=10)
    assert out.startswith("abcdefghij")
    assert out.endswith("... (truncated)")
