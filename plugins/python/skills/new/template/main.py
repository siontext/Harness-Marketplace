"""FastAPI 앱. 서버 시작 때 연결 창구를 조립하고 API를 연다."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.platform import build_platform


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """서버가 켜질 때 연결 창구를 만들고, 꺼질 때 닫는다."""
    platform = build_platform()
    app.state.platform = platform
    yield
    await platform.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    """서버가 살아 있는지 알려 준다. LLM이나 DB는 부르지 않는다."""
    return {"status": "ok"}
