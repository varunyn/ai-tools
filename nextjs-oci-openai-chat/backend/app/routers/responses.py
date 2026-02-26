import asyncio
import json
import queue
import threading
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import client_api, compartment_id
from app.schemas import CreateResponseRequest
from app.utils import create_openai_error

router = APIRouter()

RESPONSES_API_MODEL_PREFIXES = ("openai.gpt", "xai.grok")

@router.post("/api/responses")
@router.post("/v1/responses")
async def create_response(request: CreateResponseRequest):
    if not client_api:
        raise HTTPException(status_code=500, detail="OCI Client not initialized")
    if not compartment_id:
        raise HTTPException(status_code=500, detail="OCI_COMPARTMENT_ID environment variable is required")
    if (isinstance(request.input, str) and request.input == "") or not request.model:
        raise HTTPException(status_code=400, detail="model and input are required")

    model_id = (request.model or "").strip()
    if not any(model_id.startswith(prefix) for prefix in RESPONSES_API_MODEL_PREFIXES):
        return create_openai_error(
            message=(
                f"Responses API is not supported for model '{model_id}'. "
                "On OCI, only models like openai.gpt-* and xai.grok-* are supported. "
                "For meta.llama-* and other models, use POST /v1/chat/completions instead."
            ),
            type="invalid_request_error",
            status_code=400,
        )

    input_value = request.input

    try:
        create_kwargs: dict[str, Any] = {
            "model": request.model,
            "input": input_value,
            "previous_response_id": request.previous_response_id,
            "stream": request.stream,
        }
        if request.tools:
            create_kwargs["tools"] = request.tools
        if request.store is not None:
            create_kwargs["store"] = request.store
        if not hasattr(client_api, "responses"):
            return create_openai_error(
                message="OCI client does not support responses API (responses.create). Check oci-openai package version.",
                type="invalid_request_error",
                status_code=501,
            )

        if request.stream:
            chunk_queue: queue.Queue[object] = queue.Queue()

            def consume_stream():
                try:
                    stream = client_api.responses.create(**create_kwargs)
                    for chunk in stream:
                        chunk_queue.put(chunk)
                except Exception as e:
                    chunk_queue.put({"error": str(e)})
                finally:
                    chunk_queue.put(None)

            thread = threading.Thread(target=consume_stream, daemon=True)
            thread.start()

            async def generate_stream():
                loop = asyncio.get_event_loop()
                while True:
                    chunk = await loop.run_in_executor(None, chunk_queue.get)
                    if chunk is None:
                        break
                    if isinstance(chunk, dict) and "error" in chunk:
                        yield f"data: {json.dumps(chunk)}\n\n"
                        break
                    try:
                        if hasattr(chunk, "model_dump"):
                            data = getattr(chunk, "model_dump")()
                        else:
                            data = getattr(chunk, "__dict__", None) or str(chunk)
                        if isinstance(data, dict):
                            yield f"data: {json.dumps(data)}\n\n"
                        else:
                            yield f"data: {json.dumps({'content': str(data)})}\n\n"
                    except Exception:
                        yield f"data: {json.dumps({'content': str(chunk)})}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(generate_stream(), media_type="text/event-stream")

        response = client_api.responses.create(**create_kwargs)
        try:
            out = response.model_dump() if hasattr(response, "model_dump") else response
        except Exception:
            out = str(response)
        return out if isinstance(out, dict) else {"response": out}
    except Exception as e:
        error_msg = str(e)
        print(f"Responses API error: {error_msg}")
        return create_openai_error(message=error_msg, status_code=500, type="server_error")
