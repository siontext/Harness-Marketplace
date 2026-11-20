"""공통 응답 틀(ApiResponse) 단위 테스트."""

from app.api.response.api_response import ApiResponse
from app.api.response.error_code import ErrorCode
from app.api.schemas import HealthStatus


def test_성공_응답은_SUCCESS_코드와_내용을_담는다() -> None:
    # When
    response = ApiResponse.success(HealthStatus(status="ok"))

    # Then
    assert response.model_dump(mode="json") == {
        "code": "SUCCESS",
        "message": None,
        "data": {"status": "ok"},
    }


def test_내용_없는_성공_응답은_data가_비어_있다() -> None:
    # When
    response = ApiResponse.success()

    # Then
    assert response.code == "SUCCESS"
    assert response.data is None


def test_실패_응답은_오류_종류와_안내_문구를_담고_data가_비어_있다() -> None:
    # When
    response = ApiResponse.fail(ErrorCode.TIMEOUT, "응답이 늦어지고 있습니다.")

    # Then
    assert response.model_dump(mode="json") == {
        "code": "TIMEOUT",
        "message": "응답이 늦어지고 있습니다.",
        "data": None,
    }
