"""엔드포인트. 요청을 받아 에이전트에 넘기고 답을 돌려준다."""

from fastapi import APIRouter

from app.presentation.schemas import HealthStatus

router = APIRouter()


@router.get("/health")
async def health() -> HealthStatus:
    """서버가 살아 있는지 알려 준다. LLM이나 DB는 부르지 않는다.

    운영 플랫폼이 본문을 읽을 수 있어 ApiResponse로 감싸지 않는다.
    """
    return HealthStatus(status="ok")
