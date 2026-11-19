from http import HTTPStatus

from app.api.errors import find_error_rule
from app.api.schemas import ErrorCode
from app.errors import AgentTimeoutError, AppError, UpstreamError


class _LlmRateLimitError(UpstreamError):
    """대응표에 없는 UpstreamError의 하위 예외."""


class _OrderRuleError(AppError):
    """대응표에 없는 AppError의 새 하위 예외."""


def test_UpstreamError는_502와_UPSTREAM_ERROR로_바뀐다() -> None:
    # Given
    exc = UpstreamError("LLM 호출 실패: model=test-model")

    # When
    rule = find_error_rule(exc)

    # Then
    assert rule.status_code == HTTPStatus.BAD_GATEWAY
    assert rule.code == ErrorCode.UPSTREAM_ERROR
    assert rule.message == (
        "연결된 시스템에 문제가 있어 답하지 못했습니다. 잠시 후 다시 시도해 주세요."
    )


def test_AgentTimeoutError는_504와_TIMEOUT으로_바뀐다() -> None:
    # Given
    exc = AgentTimeoutError("에이전트 실행 시간 초과")

    # When
    rule = find_error_rule(exc)

    # Then
    assert rule.status_code == HTTPStatus.GATEWAY_TIMEOUT
    assert rule.code == ErrorCode.TIMEOUT


def test_AppError_그대로면_500과_INTERNAL_ERROR로_바뀐다() -> None:
    # Given
    exc = AppError("분류되지 않은 프로젝트 오류")

    # When
    rule = find_error_rule(exc)

    # Then
    assert rule.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert rule.code == ErrorCode.INTERNAL_ERROR


def test_대응표에_없는_하위_예외는_가장_가까운_부모_규칙을_따른다() -> None:
    # When
    upstream_child_rule = find_error_rule(_LlmRateLimitError("호출 한도 초과"))
    app_child_rule = find_error_rule(_OrderRuleError("주문 규칙 위반"))

    # Then
    assert upstream_child_rule.status_code == HTTPStatus.BAD_GATEWAY
    assert upstream_child_rule.code == ErrorCode.UPSTREAM_ERROR
    assert app_child_rule.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert app_child_rule.code == ErrorCode.INTERNAL_ERROR


def test_프로젝트_예외가_아니면_500과_INTERNAL_ERROR로_바뀐다() -> None:
    # Given
    exc = RuntimeError("미리 생각하지 못한 오류")

    # When
    rule = find_error_rule(exc)

    # Then
    assert rule.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert rule.code == ErrorCode.INTERNAL_ERROR
