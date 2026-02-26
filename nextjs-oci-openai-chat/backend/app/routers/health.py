from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "OCI OpenAI Backend",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "models": "/v1/models",
            "chat": "/v1/chat/completions",
            "responses": "/api/responses",
        },
    }

@router.get("/v1")
@router.get("/v1/")
async def v1_root() -> dict[str, object]:
    return {
        "status": "ok",
        "api_version": "v1",
        "endpoints": {
            "models": "/v1/models",
            "chat_completions": "/v1/chat/completions",
            "responses": "/v1/responses",
        },
    }

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}

@router.get("/api/tools")
async def get_tools() -> dict[str, list[dict[str, object]]]:
    return {"tools": []}
