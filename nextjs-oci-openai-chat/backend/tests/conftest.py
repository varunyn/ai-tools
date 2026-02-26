from typing import List, Tuple

from _pytest.reports import TestReport


_SUMMARY_ROWS: List[Tuple[str, str, float]] = []

_FRIENDLY_NAMES = {
    "tests/test_chat_completions.py::test_non_stream_tool_call_forwarded": "Non-stream tool forwarding",
    "tests/test_chat_completions.py::test_streaming_plain_text_chunks": "Streaming text chunks",
    "tests/test_chat_completions.py::test_streaming_tool_call_forwarded": "Streaming tool forwarding",

    "tests/test_health.py::test_root_returns_service_info": "Health: root service info",
    "tests/test_health.py::test_v1_root_and_trailing_slash": "Health: /v1 root trailing slash",
    "tests/test_health.py::test_health_endpoint": "Health: /health endpoint",
    "tests/test_health.py::test_api_tools_empty_list": "Tools: empty list",

    "tests/test_models.py::test_api_chat_models_returns_available_models": "Models: /api/chat/models lists",
    "tests/test_models.py::test_v1_models_openai_list_shape": "Models: /v1/models OpenAI shape",
    "tests/test_models.py::test_v1_tags_ollama_shape": "Models: /v1/tags Ollama shape",

    "tests/test_utils_errors.py::test_create_openai_error_shape": "Errors: OpenAI envelope shape",
    "tests/test_utils_errors.py::test_conversation_error_response_not_found_maps_404": "Errors: not found maps 404",
    "tests/test_utils_errors.py::test_conversation_error_response_on_create_overrides_message": "Errors: create overrides message",
    "tests/test_utils_errors.py::test_to_jsonable_prefers_model_dump_then_dict_then_str": "Utils: to_jsonable precedence",

    "tests/test_utils_tools.py::test_tool_call_name_arguments_dict_shape": "Tools: tool_call dict arguments",
    "tests/test_utils_tools.py::test_tool_call_name_arguments_object_shape": "Tools: tool_call object arguments",
    "tests/test_utils_tools.py::test_assistant_tool_response_normalizes_multiple_tool_calls": "Tools: normalize multiple tool_calls",
    "tests/test_utils_tools.py::test_shorten_truncates_and_appends_suffix": "Utils: shorten truncates w/ suffix",

    "tests/test_chat_api.py::test_api_chat_happy_path_returns_role_and_content": "API chat: happy path response",
    "tests/test_chat_api.py::test_api_chat_tool_calls_forwarded": "API chat: forwards tool_calls",
    "tests/test_chat_api.py::test_api_chat_errors_client_missing": "API chat: missing client error",
    "tests/test_chat_api.py::test_api_chat_errors_messages_required": "API chat: messages required error",
    "tests/test_chat_api.py::test_api_chat_errors_compartment_missing": "API chat: missing compartment error",

    "tests/test_responses.py::test_responses_unsupported_model_prefix_returns_openai_error": "Responses: unsupported model prefix",
    "tests/test_responses.py::test_responses_client_without_responses_returns_501": "Responses: missing client returns 501",
    "tests/test_responses.py::test_responses_non_stream_returns_dict_from_model_dump": "Responses: non-stream model_dump dict",
    "tests/test_responses.py::test_responses_stream_sse_yields_chunks_and_done": "Responses: stream yields chunks + done",
    "tests/test_responses.py::test_responses_stream_sse_emits_error_and_done": "Responses: stream emits error + done",

    "tests/test_chat_completions.py::test_validation_error_returns_openai_envelope": "Chat completions: validation error envelope",
    "tests/test_chat_completions.py::test_http_exception_returns_openai_envelope_messages_required": "Chat completions: messages required envelope",
    "tests/test_chat_completions.py::test_empty_content_returns_no_response_generated_fallback": "Chat completions: empty content fallback",
}


def pytest_runtest_logreport(report: TestReport):
    if report.when != "call":
        return
    nodeid = report.nodeid
    outcome = report.outcome.upper()
    duration = getattr(report, "duration", 0.0)
    _SUMMARY_ROWS.append((nodeid, outcome, duration))


def pytest_terminal_summary(terminalreporter):
    if not _SUMMARY_ROWS:
        return

    terminalreporter.write_line("")
    terminalreporter.write_sep("=", "Backend Test Summary")
    header = f"{'Scenario':50} | {'Result':7} | Duration (s)"
    terminalreporter.write_line(header)
    terminalreporter.write_line("-" * len(header))

    for nodeid, outcome, duration in _SUMMARY_ROWS:
        label = _FRIENDLY_NAMES.get(nodeid, nodeid)
        terminalreporter.write_line(f"{label:50} | {outcome:7} | {duration:>10.3f}")

    terminalreporter.write_sep("=", "End of Summary")
