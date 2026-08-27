from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.context import request_id_ctx, user_id_ctx
from app.core.exceptions import (
    AIProviderError,
    InvalidTranscriptError,
    MeetingNotFoundError,
    MeetingNotReadyError,
    RateLimitExceededError,
)
from app.core.logging import configure_logging, logger

configure_logging()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    user_id = request.headers.get("X-User-Id", "local")
    request_token = request_id_ctx.set(request_id)
    user_token = user_id_ctx.set(user_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_ctx.reset(request_token)
        user_id_ctx.reset(user_token)


@app.exception_handler(MeetingNotFoundError)
async def meeting_not_found_handler(_: Request, exc: MeetingNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(MeetingNotReadyError)
async def meeting_not_ready_handler(_: Request, exc: MeetingNotReadyError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(InvalidTranscriptError)
async def invalid_transcript_handler(_: Request, exc: InvalidTranscriptError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(RateLimitExceededError)
async def rate_limit_handler(_: Request, exc: RateLimitExceededError):
    return JSONResponse(status_code=429, content={"detail": str(exc)})


@app.exception_handler(AIProviderError)
async def ai_provider_handler(_: Request, exc: AIProviderError):
    error = str(exc) if settings.enable_ai_traces else "redacted"
    logger.exception("ai_provider_error", error=error)
    return JSONResponse(status_code=502, content={"detail": "AI provider request failed"})


app.include_router(api_router, prefix="/api/v1")
