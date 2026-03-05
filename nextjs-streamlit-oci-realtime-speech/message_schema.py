from __future__ import annotations

from datetime import datetime, timezone


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def ws_transcription(transcript: str, is_final: bool = True) -> dict[str, object]:
    return {
        "type": "transcription",
        "status": "success",
        "transcript": transcript,
        "is_final": is_final,
        "timestamp": _timestamp(),
    }


def ws_session_started(session_id: str | None) -> dict[str, object]:
    return {
        "type": "session_started",
        "status": "success",
        "sessionId": session_id,
        "timestamp": _timestamp(),
    }


def ws_session_stopped() -> dict[str, object]:
    return {
        "type": "session_stopped",
        "status": "success",
        "timestamp": _timestamp(),
    }


def ws_error(message: str) -> dict[str, object]:
    return {
        "type": "error",
        "status": "error",
        "message": message,
        "timestamp": _timestamp(),
    }


def ws_connection_closed(code: int, message: str) -> dict[str, object]:
    return {
        "type": "connection_closed",
        "status": "info",
        "code": code,
        "message": message,
        "timestamp": _timestamp(),
    }


def health_payload(service: str = "oracle-speech-websocket") -> dict[str, object]:
    return {
        "status": "ok",
        "service": service,
        "timestamp": _timestamp(),
    }


def readiness_payload(ready: bool, reason: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": "ready" if ready else "not_ready",
        "ready": ready,
        "timestamp": _timestamp(),
    }
    if reason:
        payload["reason"] = reason
    return payload
