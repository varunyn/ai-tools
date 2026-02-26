import asyncio
import functools
import json
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import client, compartment_id, model_id
from app.schemas import ChatRequest, OpenAIChatRequest
from app.utils import (
    _assistant_tool_response,
    _run_completion,
    _shorten,
    _tool_call_arguments,
    _tool_call_name,
    create_openai_error,
)

router = APIRouter()

@router.post("/api/chat")
async def chat(request: ChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="OCI Client not initialized")

    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages are required")

    if not compartment_id:
        raise HTTPException(status_code=500, detail="OCI_COMPARTMENT_ID environment variable is required")

    try:
        tools = request.tools if request.tools else []

        current_model_id = request.model if request.model else model_id
        print(f"Using model: {current_model_id}")

        messages_data: list[dict[str, object]] = []
        for msg in request.messages:
            msg_dict: dict[str, object] = {"role": msg.role}
            if msg.content:
                msg_dict["content"] = msg.content
            if msg.tool_calls:
                msg_dict["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
            messages_data.append(msg_dict)

        completion_kwargs = {
            "model": current_model_id,
            "messages": messages_data,
            "max_tokens": 1000,
            "temperature": 0.7,
            "tools": tools,
        }

        response = await asyncio.get_event_loop().run_in_executor(
            None, functools.partial(client.chat.completions.create, **completion_kwargs)
        )

        message = response.choices[0].message

        if not hasattr(message, "tool_calls") or not message.tool_calls:
            user_message = str(messages_data[-1].get("content", "")) if messages_data else "N/A"
            print(f"⚠️  No tool calls detected for query: {user_message[:100]}")
            print(f"   LLM response: {message.content[:200] if message.content else 'None'}...")

        if hasattr(message, "tool_calls") and message.tool_calls:
            print(f"🔧 Tool calls detected: {len(message.tool_calls)} tool(s) — forwarding to client")
            return _assistant_tool_response(message)

        return {"role": "assistant", "content": message.content}

    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")

        if "Path doesn't map to a registered service" in error_msg:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Generative AI service not available or not enabled",
                    "details": error_msg,
                    "troubleshooting": [
                        "1. Verify Generative AI service is enabled in your OCI tenancy",
                        "2. Check that your user has permissions to access Generative AI",
                        "3. Ensure you are using a supported region",
                        "4. Verify your compartment has access to Generative AI models",
                    ],
                },
            )

        return JSONResponse(status_code=500, content={"error": "Internal server error", "details": error_msg})


@router.post("/v1/chat/completions")
@router.post("/api/v1/chat/completions")
async def chat_completions_openai(request: OpenAIChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="OCI Client not initialized")

    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages are required")

    if not compartment_id:
        raise HTTPException(status_code=500, detail="OCI_COMPARTMENT_ID environment variable is required")

    try:
        tools = request.tools or []
        tools_list: list[dict[str, object]] = tools

        messages_data: list[dict[str, object]] = []
        for msg in request.messages:
            msg_dict: dict[str, object] = {"role": msg.get("role")}
            if "content" in msg:
                c = msg["content"]
                msg_dict["content"] = c if (msg.get("role") != "tool" or c is None or isinstance(c, str)) else json.dumps(c)
            if "tool_calls" in msg:
                msg_dict["tool_calls"] = msg["tool_calls"]
            if "tool_call_id" in msg:
                msg_dict["tool_call_id"] = msg["tool_call_id"]
            messages_data.append(msg_dict)

        roles = [m.get("role") for m in messages_data]
        client_tool_names: list[str | None] = []
        for t in tools_list:
            if t.get("type") == "function":
                f = t.get("function")
                if isinstance(f, dict):
                    name = f.get("name")
                    client_tool_names.append(name if isinstance(name, str) else None)
        print(
            f"📥 OpenAI chat request: stream={bool(request.stream)} | messages={len(messages_data)} roles={roles} | client_tools={len(client_tool_names)} names={client_tool_names}"
        )
        try:
            last_user = next((m for m in reversed(messages_data) if m.get("role") == "user"), None)
            if last_user and "content" in last_user and last_user.get("content"):
                print(f"   └─ last_user: {_shorten(last_user.get('content'))}")
        except Exception:
            pass
        try:
            print("   └─ backend executes no tools; forwarding tool_calls to client if present")
        except Exception:
            pass

        if request.stream:
            async def generate_stream():
                try:
                    first_resp = await _run_completion(
                        model=request.model,
                        messages=messages_data,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                        tools=tools,
                        stream=False,
                    )
                    first_msg = first_resp.choices[0].message

                    if hasattr(first_msg, "tool_calls") and first_msg.tool_calls:
                        try:
                            tc_infos = []
                            for tc in first_msg.tool_calls:
                                tc_id = tc.get("id", "") if isinstance(tc, dict) else getattr(tc, "id", "")
                                name = _tool_call_name(tc) or ""
                                tc_infos.append({"id": tc_id, "name": name})
                            print(f"🔧 tool_calls: {len(tc_infos)} → {tc_infos} | forwarding_to_client=True")
                        except Exception:
                            pass
                    if hasattr(first_msg, "tool_calls") and first_msg.tool_calls:
                        try:
                            print("↪️ forwarding tool_calls to client (streaming)")
                        except Exception:
                            pass
                        chunk_id = f"chatcmpl-{int(time.time())}"
                        yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'created': int(time.time()), 'model': request.model, 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]})}\n\n"
                        for i, tc in enumerate(first_msg.tool_calls):
                            tc_id = tc.get("id", "") if isinstance(tc, dict) else getattr(tc, "id", "")
                            name = _tool_call_name(tc) or ""
                            args = _tool_call_arguments(tc) or "{}"
                            yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'created': int(time.time()), 'model': request.model, 'choices': [{'index': 0, 'delta': {'tool_calls': [{'index': i, 'id': tc_id, 'function': {'name': name, 'arguments': args}}]}, 'finish_reason': None}]})}\n\n"
                        yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'created': int(time.time()), 'model': request.model, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'tool_calls'}]})}\n\n"
                        yield "data: [DONE]\n\n"
                        return
                    else:
                        content = (getattr(first_msg, "content", None) or "").strip()
                        if not content:
                            content = "(No response generated.)"

                    chunk_id = f"chatcmpl-{int(time.time())}"
                    init_chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
                    }
                    yield f"data: {json.dumps(init_chunk)}\n\n"
                    for i in range(0, len(content), 64):
                        piece = content[i : i + 64]
                        response_chunk = {
                            "id": chunk_id,
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": request.model,
                            "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}],
                        }
                        yield f"data: {json.dumps(response_chunk)}\n\n"
                    yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'created': int(time.time()), 'model': request.model, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as stream_err:
                    print(f"Streaming error: {str(stream_err)}")
                    yield f"data: {json.dumps({'error': str(stream_err)})}\n\n"

            return StreamingResponse(generate_stream(), media_type="text/event-stream")

        first_resp = await _run_completion(
            model=request.model,
            messages=messages_data,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            tools=tools,
            stream=False,
        )
        first_msg = first_resp.choices[0].message

        if hasattr(first_msg, "tool_calls") and first_msg.tool_calls:
            try:
                tc_infos = []
                for tc in first_msg.tool_calls:
                    tc_id = tc.get("id", "") if isinstance(tc, dict) else getattr(tc, "id", "")
                    name = _tool_call_name(tc) or ""
                    tc_infos.append({"id": tc_id, "name": name})
                print(f"🔧 tool_calls: {len(tc_infos)} → {tc_infos} | forwarding_to_client=True")
                print("↪️ forwarding tool_calls to client (non-stream)")
            except Exception:
                pass
            assistant_msg = _assistant_tool_response(first_msg)
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{"index": 0, "message": assistant_msg, "finish_reason": "tool_calls"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
        else:
            content = (getattr(first_msg, "content", None) or "").strip()
            if not content:
                content = "(No response generated.)"

        assistant_message = {"role": "assistant", "content": content}
        response_data = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{"index": 0, "message": assistant_message, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
        return response_data

    except Exception as e:
        error_msg = str(e)
        print(f"Error in OpenAI-compatible endpoint: {error_msg}")
        return create_openai_error(message=error_msg, status_code=500, type="server_error")
