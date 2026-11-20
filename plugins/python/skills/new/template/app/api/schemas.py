"""엔드포인트별 요청·응답 내용. 공통 응답 틀은 app/api/response에 둔다."""

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """/health가 돌려주는 내용."""

    status: str = Field(description="서버 상태. 살아 있으면 ok")
