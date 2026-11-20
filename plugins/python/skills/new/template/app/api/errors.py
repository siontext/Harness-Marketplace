"""전역 예외 핸들러. 올라온 예외를 ApiResponse 실패 응답으로 바꾼다.

예외 → 상태 코드·code·안내 문구 대응은 이 파일의 표 한 곳에만 둔다.
안내 문구 자체는 app/api/response/messages.py에 모아 둔다.
스트리밍 중 오류(SSE error 이벤트)도 find_error_rule로 같은 표를 쓴다.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass, replace
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.response import messages
from app.api.response.api_response import ApiResponse
from app.api.response.error_code import ErrorCode
from app.errors import AgentTimeoutError, AppError, UpstreamError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ErrorRule:
    """오류 하나를 무엇으로 답할지 정한 규칙.

    Attributes:
        status_code: HTTP 상태 코드.
        code: 오류 응답의 code 값.
        message: 사용자에게 보여줄 고정 안내 문구.
    """

    status_code: int
    code: ErrorCode
    message: str


# ── 예상하지 못한 오류 (기본값) ─────────────────────────────────────────
# 아래 어디에도 해당하지 않는 오류는 모두 이 규칙으로 답한다.
INTERNAL_ERROR_RULE = ErrorRule(
    HTTPStatus.INTERNAL_SERVER_ERROR,
    ErrorCode.INTERNAL_ERROR,
    messages.INTERNAL_ERROR,
)

# ── 우리가 만든 예외 (app/errors.py) ────────────────────────────────────
# 예외 → 상태 코드·code·안내 문구 대응은 이 표 한 곳에만 둔다.
ERROR_RULES: dict[type[AppError], ErrorRule] = {
    AgentTimeoutError: ErrorRule(
        HTTPStatus.GATEWAY_TIMEOUT,
        ErrorCode.TIMEOUT,
        messages.TIMEOUT,
    ),
    UpstreamError: ErrorRule(
        HTTPStatus.BAD_GATEWAY,
        ErrorCode.UPSTREAM_ERROR,
        messages.UPSTREAM_ERROR,
    ),
    AppError: INTERNAL_ERROR_RULE,
}

# ── FastAPI가 던지는 예외 ───────────────────────────────────────────────
# 요청 형식 오류(RequestValidationError).
INVALID_REQUEST_RULE = ErrorRule(
    HTTPStatus.UNPROCESSABLE_ENTITY,
    ErrorCode.INVALID_REQUEST,
    messages.INVALID_REQUEST,
)

# HTTPException은 상태 코드를 그대로 쓰므로 4xx의 안내 문구만 상태 코드로 고른다.
HTTP_CLIENT_ERROR_MESSAGES: dict[int, str] = {
    HTTPStatus.NOT_FOUND: messages.NOT_FOUND,
    HTTPStatus.METHOD_NOT_ALLOWED: messages.METHOD_NOT_ALLOWED,
}

# ── 오류 규칙이 아닌 설정 ───────────────────────────────────────────────
# 본문을 실을 수 없는 상태 코드.
NO_BODY_STATUS_CODES: frozenset[int] = frozenset(
    {HTTPStatus.NO_CONTENT, HTTPStatus.RESET_CONTENT, HTTPStatus.NOT_MODIFIED}
)


# ── 핸들러가 불러 쓰는 함수 ─────────────────────────────────────────────
def find_error_rule(exc: Exception) -> ErrorRule:
    """예외에 맞는 오류 규칙을 찾는다.

    대응표에 없는 하위 예외는 상속을 따라 가장 가까운 부모의 규칙을 쓴다.

    Args:
        exc: 올라온 예외.

    Returns:
        그 예외의 규칙. 프로젝트 예외가 아니면 500 · INTERNAL_ERROR 규칙.
    """
    for exc_type in type(exc).__mro__:
        rule = ERROR_RULES.get(exc_type)
        if rule is not None:
            return rule
    return INTERNAL_ERROR_RULE


def _find_http_error_rule(status_code: int) -> ErrorRule:
    """HTTPException의 상태 코드는 그대로 두고 code와 안내 문구를 고른다."""
    if status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
        return replace(INTERNAL_ERROR_RULE, status_code=status_code)
    message = HTTP_CLIENT_ERROR_MESSAGES.get(status_code, messages.CLIENT_ERROR)
    return ErrorRule(status_code, ErrorCode.INVALID_REQUEST, message)


def _log_failure(request: Request, rule: ErrorRule, exc: Exception) -> None:
    """실패를 로그에 남긴다. 5xx는 ERROR·스택 포함, 그 밖은 WARNING·스택 없음.

    요청 본문, 쿼리 값, 헤더는 남기지 않는다.
    """
    args = (
        request.method,
        request.url.path,
        rule.status_code,
        rule.code.value,
        type(exc).__name__,
    )
    if rule.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
        logger.error("서버 오류: %s %s -> %d %s (%s)", *args, exc_info=exc)
    else:
        logger.warning("호출자 오류: %s %s -> %d %s (%s)", *args)


def _describe_invalid_fields(exc: RequestValidationError) -> str:
    """틀린 필드의 위치와 종류만 문장으로 만든다. 보낸 값(input)은 넣지 않는다."""
    return ", ".join(
        f"{'.'.join(str(part) for part in error['loc'])}({error['type']})"
        for error in exc.errors()
    )


def _to_response(rule: ErrorRule, headers: Mapping[str, str] | None = None) -> Response:
    """규칙을 오류 응답으로 바꾼다. 본문을 실을 수 없는 상태 코드는 본문을 뺀다."""
    status_code = rule.status_code
    if status_code < HTTPStatus.OK or status_code in NO_BODY_STATUS_CODES:
        return Response(status_code=status_code, headers=headers)
    body = ApiResponse[None].fail(rule.code, rule.message)
    return JSONResponse(
        body.model_dump(mode="json"), status_code=status_code, headers=headers
    )


# ── 핸들러 함수 ─────────────────────────────────────────────────────────
async def _handle_error(request: Request, exc: Exception) -> Response:
    """프로젝트 예외와 처리하지 못한 예외를 대응표의 규칙으로 답한다."""
    rule = find_error_rule(exc)
    _log_failure(request, rule, exc)
    return _to_response(rule)


async def _handle_validation_error(
    request: Request, exc: RequestValidationError
) -> Response:
    """요청 형식 오류를 422 · INVALID_REQUEST로 답한다."""
    rule = INVALID_REQUEST_RULE
    logger.warning(
        "요청 형식 오류: %s %s -> %d %s (%s) 틀린 곳: %s",
        request.method,
        request.url.path,
        rule.status_code,
        rule.code.value,
        type(exc).__name__,
        _describe_invalid_fields(exc),
    )
    return _to_response(rule)


async def _handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> Response:
    """HTTPException을 원래 상태 코드와 헤더 그대로, 통일된 본문으로 답한다."""
    rule = _find_http_error_rule(exc.status_code)
    _log_failure(request, rule, exc)
    return _to_response(rule, exc.headers)


# ── 핸들러 등록 (어떤 예외를 어느 핸들러가 잡는지) ──────────────────────
def register_exception_handlers(app: FastAPI) -> None:
    """모든 오류 응답을 ApiResponse 실패 응답으로 통일하는 핸들러를 붙인다.

    Args:
        app: 핸들러를 붙일 FastAPI 앱.
    """
    # add_exception_handler는 핸들러의 예외 인자를 Exception으로만 받아 타입 검사에
    # 걸린다. 그래서 데코레이터용 exception_handler를 함수처럼 불러 붙인다.
    # AppError를 따로 붙여야 Exception 핸들러와 달리 응답 뒤에 다시 던져지지 않는다.
    app.exception_handler(AppError)(_handle_error)
    app.exception_handler(RequestValidationError)(_handle_validation_error)
    # 라우터가 내는 404·405는 Starlette 쪽 클래스라 그쪽으로 붙여야 잡힌다.
    app.exception_handler(StarletteHTTPException)(_handle_http_exception)
    app.exception_handler(Exception)(_handle_error)
