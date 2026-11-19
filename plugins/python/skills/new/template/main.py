"""FastAPI 앱 조립. 연결 창구를 만들고 엔드포인트와 전역 예외 핸들러를 붙인다."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes import router
from app.platform import build_platform


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """서버가 켜질 때 연결 창구를 만들고, 꺼질 때 닫는다."""
    platform = build_platform()
    app.state.platform = platform
    yield
    await platform.aclose()


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)
app.include_router(router)
