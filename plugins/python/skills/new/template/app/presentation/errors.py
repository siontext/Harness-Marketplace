"""전역 예외 핸들러. 올라온 예외를 ApiResponse 실패 응답으로 바꾼다.

예외 → 상태 코드·code·안내 문구 대응은 이 파일의 표 한 곳에만 둔다.
안내 문구 자체는 app/presentation/response/messages.py에 모아 둔다.
스트리밍 중 오류(SSE error 이벤트)도 ErrorRuleBook으로 같은 표를 쓴다.
어떤 예외를 어느 핸들러 메서드가 잡는지는 main.py에서 등록한다.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass, replace
from http import HTTPStatus

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.errors import AgentTimeoutError, AppError, UpstreamError
from app.presentation.response import messages
from app.presentation.response.api_response import ApiResponse
from app.presentation.response.error_code import ErrorCode

logger = logging.getLogger(__name__)


# ── 오류 규칙 ───────────────────────────────────────────────────────────
# 본문을 실을 수 없는 상태 코드.
NO_BODY_STATUS_CODES: frozenset[int] = frozenset(
    {HTTPStatus.NO_CONTENT, HTTPStatus.RESET_CONTENT, HTTPStatus.NOT_MODIFIED}
)


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

    def to_response(self, headers: Mapping[str, str] | None = None) -> Response:
        """이 규칙을 오류 응답으로 바꾼다. 본문을 실을 수 없는 상태 코드는 본문을 뺀다.

        Args:
            headers: 응답에 그대로 실을 헤더 (예: 405의 Allow).

        Returns:
            ApiResponse 실패 본문을 실은 응답. 본문을 실을 수 없으면 상태 코드만.
        """
        status_code = self.status_code
        if status_code < HTTPStatus.OK or status_code in NO_BODY_STATUS_CODES:
            return Response(status_code=status_code, headers=headers)
        body = ApiResponse[None].fail(self.code, self.message)
        return JSONResponse(
            body.model_dump(mode="json"), status_code=status_code, headers=headers
        )


# ── 예상하지 못한 오류 (기본값) ─────────────────────────────────────────
# 아래 어디에도 해당하지 않는 오류는 모두 이 규칙으로 답한다.
INTERNAL_ERROR_RULE = ErrorRule(
    HTTPStatus.INTERNAL_SERVER_ERROR,
    ErrorCode.INTERNAL_ERROR,
    messages.INTERNAL_ERROR,
)

# ── 우리가 만든 예외 (app/common/errors.py) ────────────────────────────────────
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

STREAMING_LOG_SUFFIX = " [스트리밍 중: error 이벤트로 응답]"


# ── 규칙 찾기 · 실패 로그 · 전역 예외 핸들러 ─────────────────────────────
class ErrorRuleBook:
    """올라온 예외에 맞는 오류 규칙을 위의 대응표에서 찾는다.

    전역 핸들러와 스트리밍 응답(SseResponse)이 같은 대응표를 쓰도록
    이 클래스를 거친다.
    """

    def find(self, exc: Exception) -> ErrorRule:
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

    def find_for_status(self, status_code: int) -> ErrorRule:
        """HTTPException의 상태 코드는 그대로 두고 code와 안내 문구를 고른다.

        Args:
            status_code: HTTPException의 상태 코드.

        Returns:
            5xx면 그 상태 코드의 INTERNAL_ERROR 규칙, 4xx면 INVALID_REQUEST 규칙.
        """
        if status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
            return replace(INTERNAL_ERROR_RULE, status_code=status_code)
        message = HTTP_CLIENT_ERROR_MESSAGES.get(status_code, messages.CLIENT_ERROR)
        return ErrorRule(status_code, ErrorCode.INVALID_REQUEST, message)


class FailureLogger:
    """실패를 로그에 남긴다. 요청 본문, 쿼리 값, 헤더는 남기지 않는다.

    전역 핸들러와 스트리밍 응답(SseResponse)이 같은 규칙으로 남기도록
    이 클래스를 거친다.
    """

    def log(
        self,
        request: Request,
        rule: ErrorRule,
        exc: Exception,
        *,
        streaming: bool = False,
    ) -> None:
        """실패를 남긴다. 5xx는 ERROR·스택 포함, 그 밖은 WARNING·스택 없음.

        Args:
            request: 실패한 요청.
            rule: 그 실패에 적용한 오류 규칙.
            exc: 올라온 예외.
            streaming: 스트리밍이 시작된 뒤의 실패면 True. 이때 실제 HTTP 응답은
                200이고 오류는 error 이벤트로 나가므로 로그에 그 사실을 표시한다.
        """
        suffix = STREAMING_LOG_SUFFIX if streaming else ""
        args = (
            request.method,
            request.url.path,
            rule.status_code,
            rule.code.value,
            type(exc).__name__,
            suffix,
        )
        if rule.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
            logger.error("서버 오류: %s %s -> %d %s (%s)%s", *args, exc_info=exc)
        else:
            logger.warning("호출자 오류: %s %s -> %d %s (%s)%s", *args)

    def log_invalid_request(
        self, request: Request, rule: ErrorRule, exc: RequestValidationError
    ) -> None:
        """요청 형식 오류를 WARNING으로 남긴다. 틀린 필드의 위치와 종류만 남긴다.

        Args:
            request: 실패한 요청.
            rule: 요청 형식 오류 규칙.
            exc: FastAPI가 던진 요청 형식 오류.
        """
        logger.warning(
            "요청 형식 오류: %s %s -> %d %s (%s) 틀린 곳: %s",
            request.method,
            request.url.path,
            rule.status_code,
            rule.code.value,
            type(exc).__name__,
            self._describe_invalid_fields(exc),
        )

    @staticmethod
    def _describe_invalid_fields(exc: RequestValidationError) -> str:
        """틀린 필드의 위치와 종류만 문장으로 만든다. 보낸 값(input)은 넣지 않는다."""
        return ", ".join(
            f"{'.'.join(str(part) for part in error['loc'])}({error['type']})"
            for error in exc.errors()
        )


class GlobalExceptionHandler:
    """모든 오류 응답을 ApiResponse 실패 응답으로 통일한다.

    메서드 하나가 예외 종류 하나를 맡는다. 어떤 예외를 어느 메서드가 잡는지는
    main.py에서 등록한다. 상태 코드·code·안내 문구는 메서드에 적지 않고
    대응표에서 찾는다.
    """

    def __init__(self) -> None:
        # 설정도 바꿔 끼울 구현도 없는 도우미라 받지 않고 여기서 만든다.
        self._rules = ErrorRuleBook()
        self._failures = FailureLogger()

    async def handle_app_error(self, request: Request, exc: AppError) -> Response:
        """우리가 만든 예외(AppError 하위) → 대응표의 규칙 (504, 502, 500)."""
        return self._respond(request, exc, self._rules.find(exc))

    async def handle_validation_error(
        self, request: Request, exc: RequestValidationError
    ) -> Response:
        """요청 형식 오류 → 422 · INVALID_REQUEST."""
        rule = INVALID_REQUEST_RULE
        self._failures.log_invalid_request(request, rule, exc)
        return rule.to_response()

    async def handle_http_exception(
        self, request: Request, exc: StarletteHTTPException
    ) -> Response:
        """없는 주소(404)·틀린 방식(405) 등 → 원래 상태 코드와 헤더 그대로."""
        rule = self._rules.find_for_status(exc.status_code)
        self._failures.log(request, rule, exc)
        return rule.to_response(exc.headers)

    async def handle_unexpected(self, request: Request, exc: Exception) -> Response:
        """처리하지 못한 그 밖의 모든 예외 → 500 · INTERNAL_ERROR."""
        return self._respond(request, exc, INTERNAL_ERROR_RULE)

    def _respond(self, request: Request, exc: Exception, rule: ErrorRule) -> Response:
        """실패를 로그에 남기고 규칙대로 답한다."""
        self._failures.log(request, rule, exc)
        return rule.to_response()
