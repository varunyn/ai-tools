import time
from typing import cast

from fastapi import APIRouter

from app.config import AVAILABLE_MODELS

router = APIRouter()

@router.get("/api/chat/models")
async def get_models() -> dict[str, list[dict[str, object]]]:
    return {"models": AVAILABLE_MODELS}

@router.get("/v1/models")
@router.get("/api/v1/models")
async def get_models_openai() -> dict[str, object]:
    models_data: list[dict[str, object]] = []
    for model in AVAILABLE_MODELS:
        model_id = str(cast(object, model["id"]))
        owned_by = str(cast(object, model.get("chef", "oci"))).lower()
        models_data.append(
            {
                "id": model_id,
                "object": "model",
                "created": int(time.time()),
                "owned_by": owned_by,
                "permission": [],
                "root": model_id,
                "parent": None,
            }
        )
    return {"object": "list", "data": models_data}

@router.get("/api/tags")
@router.get("/v1/tags")
async def get_tags_ollama() -> dict[str, list[dict[str, object]]]:
    models_data: list[dict[str, object]] = [
        {
            "name": str(cast(object, model["id"])),
            "model": str(cast(object, model["id"])),
            "modified_at": "2024-01-01T00:00:00Z",
            "size": 1000000000,
            "digest": f"sha256:{hash(str(cast(object, model['id'])))}",
            "details": {
                "parent_model": "",
                "format": "gguf",
                "family": str(cast(object, model.get("chef", "llama"))).lower(),
                "families": [str(cast(object, model.get("chef", "llama"))).lower()],
                "parameter_size": "7B",
                "quantization_level": "Q4_0",
            },
        }
        for model in AVAILABLE_MODELS
    ]
    return {"models": models_data}
