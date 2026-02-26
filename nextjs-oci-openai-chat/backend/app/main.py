from collections.abc import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health as health_router
from app.routers import models as models_router
from app.routers import chat as chat_router
from app.routers import responses as responses_router
from app.utils import create_openai_error

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    print(f"DEBUG REQUEST: {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"DEBUG RESPONSE: {response.status_code}")
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    return create_openai_error(message=exc.detail, status_code=exc.status_code)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    return create_openai_error(message=str(exc), status_code=400)

app.include_router(health_router.router)
app.include_router(models_router.router)
app.include_router(chat_router.router)
app.include_router(responses_router.router)
