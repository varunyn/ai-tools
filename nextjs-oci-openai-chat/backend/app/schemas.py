from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str | None = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: str | None = None


class ChatRequest(BaseModel):
    messages: list[Message]
    tools: Optional[List[Dict[str, Any]]] = None
    model: str | None = None


# OpenAI-compatible request model
class OpenAIChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    tools: Optional[List[Dict[str, Any]]] = None
    temperature: float | None = 0.7
    max_tokens: int | None = 1000
    stream: bool | None = False


# OCI Responses API request
# input: str or List[Dict]. With tools, OCI accepts string or messages.
# tools: optional list — type "mcp" (server_label, require_approval, server_url, optional authorization) or type "function" (name, description, parameters)
# store: optional; when True, OCI stores the response for follow-up (e.g. previous_response_id)
class CreateResponseRequest(BaseModel):
    model: str
    input: Any  # str or List[Dict]: single prompt or messages
    previous_response_id: str | None = None
    stream: bool | None = False
    tools: Optional[List[Dict[str, Any]]] = None
    store: bool | None = None
