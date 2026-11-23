"""전역 예외 핸들러. 올라온 예외를 ApiResponse 실패 응답으로 바꾼다.

어떤 예외를 어느 메서드가 잡는지는 main.py에서 등록한다.
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.errors import AppError
from app.presentation.exception.error_rule import ErrorRule, ErrorRuleBook
from app.presentation.exception.failure_logger import FailureLogger


class GlobalExceptionHandler:
    """모든 오류 응답을 ApiResponse 실패 응답으로 통일한다.

    메서드 하나가 예외 종류 하나를 맡는다. 상태 코드·code·안내 문구는 메서드에
    적지 않고 ErrorRuleBook에 묻는다.
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
        rule = self._rules.find_for_invalid_request()
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
        return self._respond(request, exc, self._rules.find_for_unexpected())

    def _respond(self, request: Request, exc: Exception, rule: ErrorRule) -> Response:
        """실패를 로그에 남기고 규칙대로 답한다."""
        self._failures.log(request, rule, exc)
        return rule.to_response()
