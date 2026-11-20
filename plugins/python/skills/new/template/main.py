"""FastAPI 앱 조립. 연결 창구를 만들고 엔드포인트와 전역 예외 핸들러를 붙인다."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure import build_platform
from app.infrastructure.settings import load_settings
from app.presentation.errors import register_exception_handlers
from app.presentation.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """서버가 켜질 때 연결 창구를 만들고, 꺼질 때 닫는다.

    채팅 기능을 만들면 여기서 조립 함수를 불러 결과를 app.state에 둔다:
    app.state.chat = build_chat_service(platform, settings.agent_timeout_seconds)
    """
    settings = load_settings()
    platform = build_platform(settings)
    yield
    await platform.aclose()


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)
app.include_router(router)
