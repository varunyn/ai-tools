"""
Unified OCI Generative AI inference using GenericChatRequest and model_id.

Supports multiple models (OpenAI, xAI Grok, Meta Llama, etc.) via OnDemandServingMode.
Model-specific parameters are applied by model_id prefix (xai., meta., else default).
"""
import json
import os
import time
from typing import Any, Callable

import oci
from oci.generative_ai_inference.models import (
    BaseChatRequest,
    ChatDetails,
    GenericChatRequest,
    OnDemandServingMode,
    SystemMessage,
    TextContent,
    UserMessage,
)

from utils.oci_client import get_oci_client, load_config
from utils.logger import get_logger

logger = get_logger(__name__)

ENDPOINT = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"
CHUNK_SIZE_CHARS = 6000
LARGE_DOCUMENT_THRESHOLD = 8000


def _chat_request_params(model_id: str) -> dict[str, Any]:
    """Build GenericChatRequest params by model_id prefix (google., xai., meta., else default)."""
    is_gemini = model_id.startswith("google.")
    is_xai = model_id.startswith("xai.")
    is_meta = model_id.startswith("meta.")

    if is_gemini:
        # Gemini: OCI requires top_k >= 1.0; use sample params for Gemini Pro
        return {
            "max_tokens": 6000,
            "temperature": 1,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "top_p": 0.95,
            "top_k": 1,
        }
    if is_xai:
        return {
            "max_tokens": 128000,
            "temperature": 1.0,
            "top_p": 1.0,
            "top_k": 0,
        }
    if is_meta:
        return {
            "max_tokens": 4000,
            "temperature": 1,
            "top_p": 0.75,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
    # Default for OpenAI and others
    return {
        "max_tokens": 128000,
        "temperature": 0.5,
        "top_p": 0.8,
        "top_k": -1,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    }


def chat(model_id: str, user_prompt: str, system_prompt: str = "") -> str:
    """
    Send a chat request to OCI Gen AI with the given model_id and prompts.

    Args:
        model_id: OCI model ID (e.g. meta.llama-3.3-70b-instruct, openai.gpt-oss-120b).
        user_prompt: The user message content.
        system_prompt: Optional system message; if empty, only user message is sent.

    Returns:
        Assistant response text.

    Raises:
        Exception: On API or parsing errors.
    """
    config_data = load_config()
    compartment_id = config_data["compartment_id"]
    config_profile = config_data["config_profile"]
    client = get_oci_client(config_profile, ENDPOINT)

    user_msg = UserMessage(content=[TextContent(text=user_prompt)])
    messages = [user_msg]
    if system_prompt:
        system_msg = SystemMessage(content=[TextContent(text=system_prompt)])
        messages = [system_msg, user_msg]

    params = _chat_request_params(model_id)
    chat_request = GenericChatRequest(
        api_format=BaseChatRequest.API_FORMAT_GENERIC,
        messages=messages,
        **params,
    )
    chat_detail = ChatDetails(
        compartment_id=compartment_id,
        serving_mode=OnDemandServingMode(model_id=model_id),
        chat_request=chat_request,
    )

    response = client.chat(chat_detail)
    return _extract_text_from_response(response)


def _extract_text_from_response(response: Any) -> str:
    """Extract assistant text from chat response (choices[0].message.content or fallbacks)."""
    try:
        data_dict = vars(response)
        if "data" not in data_dict:
            return "No data in response"
        raw = data_dict["data"]
        try:
            json_result = json.loads(str(raw))
        except (TypeError, json.JSONDecodeError):
            return str(raw)
        chat_resp = json_result.get("chat_response") or json_result
        if not chat_resp:
            return "No chat_response in response"
        choices = chat_resp.get("choices")
        if choices and len(choices) > 0:
            msg = choices[0].get("message") or choices[0]
            content = msg.get("content")
            if isinstance(content, list) and len(content) > 0:
                first = content[0]
                if isinstance(first, dict) and "text" in first:
                    return first["text"]
                if isinstance(first, str):
                    return first
            if isinstance(content, str):
                return content
            if msg.get("text"):
                return msg["text"]
        if chat_resp.get("text"):
            return chat_resp["text"]
        if chat_resp.get("content"):
            return chat_resp["content"]
        return "Could not extract text from response"
    except Exception as e:
        logger.error(f"Error extracting text: {e}", exc_info=True)
        raise


def chunk_text(text: str, max_chars: int = CHUNK_SIZE_CHARS) -> list[str]:
    """Split text into chunks, breaking at paragraph boundaries."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    paragraphs = text.split("\n\n")
    current = ""
    for para in paragraphs:
        if len(para) > max_chars:
            for sentence in para.replace(". ", ".\n").split("\n"):
                if len(current) + len(sentence) + 2 > max_chars and current:
                    chunks.append(current)
                    current = sentence
                else:
                    current = (current + " " + sentence) if current else sentence
        elif len(current) + len(para) + 2 > max_chars and current:
            chunks.append(current)
            current = para
        else:
            current = (current + "\n\n" + para) if current else para
    if current:
        chunks.append(current)
    return chunks


def summarize_with_model(
    model_id: str,
    text: str,
    prompt_template: str,
    progress_file: str | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> str:
    """
    Summarize text using the given model_id. Uses chunking for long documents.

    Args:
        model_id: OCI model ID from GENAI_MODELS.
        text: Document text to summarize.
        prompt_template: Prompt with {} placeholder for content.
        progress_file: Optional path to write chunk progress (e.g. "1/5").
        progress_callback: Optional callback(current, total, message) for progress.

    Returns:
        Summary text.
    """
    if len(text) <= LARGE_DOCUMENT_THRESHOLD:
        prompt = prompt_template.format(text)
        return chat(model_id, prompt)

    chunks = chunk_text(text)
    total = len(chunks)
    logger.info(f"Summarizing in {total} chunks")
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        if progress_file:
            try:
                with open(progress_file, "w") as f:
                    f.write(f"{i}/{total}")
            except OSError:
                pass
        if progress_callback:
            try:
                progress_callback(i, total, f"Chunk {i + 1} of {total}")
            except Exception:
                pass
        chunk_prompt = (
            f"This is part {i + 1} of {total} of a longer document. "
            f"Summarize this part concisely.\n\n{chunk}"
        )
        chunk_summaries.append(chat(model_id, chunk_prompt))
        time.sleep(0.2)

    if progress_file:
        try:
            with open(progress_file, "w") as f:
                f.write("Finalizing summary...")
        except OSError:
            pass
    combined = "\n\n".join(chunk_summaries)
    final_prompt = (
        "You are provided with summaries of different parts of a document. "
        "Create one coherent summary that combines all the information:\n\n"
        + combined
    )
    return chat(model_id, final_prompt)
