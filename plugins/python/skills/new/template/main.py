"""부트스트랩. FastAPI 앱을 만들고 연결 창구·엔드포인트·전역 예외 핸들러를 붙인다.

무엇이 무엇에 연결됐는지는 이 파일만 보면 다 보인다.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.errors import AppError
from app.infrastructure import Platform
from app.infrastructure.settings import Settings
from app.presentation.exception.global_exception_handler import (
    GlobalExceptionHandler,
)
from app.presentation.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """서버가 켜질 때 연결 창구를 만들고, 꺼질 때 닫는다.

    채팅 기능을 만들면 여기서 조립 객체를 만들어 결과를 app.state에 둔다:
    app.state.chat = Container(platform, settings).build_chat_service()
    """
    settings = Settings.from_env()
    platform = Platform.from_settings(settings)
    yield
    await platform.aclose()


app = FastAPI(lifespan=lifespan)

# ── 전역 예외 핸들러 등록 (어떤 예외를 어느 메서드가 잡는지) ──────────────
# add_exception_handler는 핸들러의 예외 인자를 Exception으로만 받아 타입 검사에
# 걸린다. 그래서 데코레이터용 exception_handler를 함수처럼 불러 붙인다.
handler = GlobalExceptionHandler()
# AppError를 따로 붙여야 Exception 핸들러와 달리 응답 뒤에 다시 던져지지 않는다.
app.exception_handler(AppError)(handler.handle_app_error)
app.exception_handler(RequestValidationError)(handler.handle_validation_error)
# 라우터가 내는 404·405는 Starlette 쪽 클래스라 그쪽으로 붙여야 잡힌다.
app.exception_handler(StarletteHTTPException)(handler.handle_http_exception)
app.exception_handler(Exception)(handler.handle_unexpected)

# ── 엔드포인트 ──────────────────────────────────────────────────────────
app.include_router(router)
