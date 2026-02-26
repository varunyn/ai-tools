import asyncio
import functools
import json
from typing import Any, Dict, List, Optional

from fastapi.responses import JSONResponse

from .config import client


def create_openai_error(
    message: str,
    type: str = "invalid_request_error",
    code: Optional[str] = None,
    status_code: int = 400,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": message,
                "type": type,
                "param": None,
                "code": code,
            }
        },
    )


def _conversation_error_response(exc: Exception, on_create: bool = False) -> JSONResponse:
    """Map OCI conversation API errors to appropriate status (e.g. 404 for Not Found)."""
    msg = str(exc).strip()
    lower = msg.lower()
    status_code = 500
    error_type = "server_error"
    if "not found" in lower or "404" in msg or getattr(exc, "status_code", None) == 404:
        status_code = 404
        error_type = "invalid_request_error"
        if on_create:
            msg = (
                "Conversations API is not available on this OCI endpoint (Not Found). "
                "This deployment may only support chat completions and responses. "
                "Use POST /v1/chat/completions for conversation-style flows."
            )
    return create_openai_error(message=msg, status_code=status_code, type=error_type)


def _tool_call_name(tc: Any) -> Optional[str]:
    if hasattr(tc, "function") and getattr(tc.function, "name", None):
        return tc.function.name
    if isinstance(tc, dict):
        fn = tc.get("function") or {}
        return fn.get("name")
    return None


def _tool_call_arguments(tc: Any) -> Optional[str]:
    if hasattr(tc, "function") and getattr(tc.function, "arguments", None):
        return tc.function.arguments
    if isinstance(tc, dict):
        fn = tc.get("function") or {}
        return fn.get("arguments")
    return None


def _assistant_tool_response(message: Any) -> Dict[str, Any]:
    return {
        "role": "assistant",
        "content": getattr(message, "content", None) or "",
        "tool_calls": [
            {
                "id": (tc.get("id", "") if isinstance(tc, dict) else getattr(tc, "id", "")),
                "type": (tc.get("type", "function") if isinstance(tc, dict) else getattr(tc, "type", "function")),
                "function": {
                    "name": _tool_call_name(tc),
                    "arguments": _tool_call_arguments(tc) or "{}",
                },
            }
            for tc in getattr(message, "tool_calls", [])
        ],
    }


def _shorten(value: Any, max_chars: int = 200) -> str:
    """Return a concise string preview for logging. Avoids dumping large payloads/secrets.
    - Converts dict/list to JSON (non-ASCII preserved)
    - Truncates to max_chars and appends '... (truncated)'
    - Ensures return type is str
    """
    try:
        if value is None:
            s = ""
        elif isinstance(value, (str, bytes)):
            s = value.decode("utf-8", "ignore") if isinstance(value, bytes) else value
        else:
            s = json.dumps(value, ensure_ascii=False)
    except Exception:
        try:
            s = str(value)
        except Exception:
            s = "<unprintable>"
    if len(s) > max_chars:
        return s[:max_chars] + "... (truncated)"
    return s


async def _run_completion(
    *,
    model: str,
    messages: List[Dict[str, Any]],
    temperature: Optional[float],
    max_tokens: Optional[int],
    tools: Optional[List[Dict[str, Any]]] = None,
    stream: bool = False,
):
    """Run client.chat.completions.create in an executor to avoid blocking."""
    loop = asyncio.get_event_loop()
    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "tools": tools or [],
        "stream": stream,
    }
    return await loop.run_in_executor(None, functools.partial(client.chat.completions.create, **kwargs))


def _to_jsonable(obj: Any) -> Any:
    """Convert OCI SDK response to JSON-serializable dict."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)
