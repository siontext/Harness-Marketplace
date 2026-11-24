"""환경 변수 설정. 이 모듈 밖에서는 환경 변수를 읽지 않는다."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = ".env"
# 설계 문서 개요 "시간 제한"의 우리 쪽 값. AGENT_TIMEOUT_SECONDS를 비우면 이 값을 쓴다.
DEFAULT_AGENT_TIMEOUT_SECONDS = 30.0


class Settings(BaseSettings):
    """서버가 쓰는 환경 변수 묶음. 서버 시작 때 Settings()로 한 번 만든다.

    칸 이름을 대문자로 바꾼 환경 변수에서 값을 읽는다 (llm_model ← LLM_MODEL).
    로컬에서는 .env 파일 값을 함께 읽는다. 이미 설정된 환경 변수가 우선한다.
    값이 비어 있으면 기본값을 쓴다. 형식이 맞지 않으면 ValidationError
    (ValueError의 하위)가 나서 서버가 뜨지 않는다.

    Attributes:
        platform: 연결 창구 이름. 비어 있으면 로컬.
        llm_base_url: 로컬 LLM(OpenAI 호환 API) 주소.
        llm_api_key: 로컬 LLM 키.
        llm_model: 로컬 LLM 모델 이름.
        agent_timeout_seconds: 질문 하나에 답하는 전체 시간 제한(초). 0보다 커야 한다.
    """

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        frozen=True,
    )

    platform: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    # 0 이하면 모든 질문이 바로 시간 초과가 되므로 서버가 뜨지 않게 막는다.
    agent_timeout_seconds: float = Field(default=DEFAULT_AGENT_TIMEOUT_SECONDS, gt=0)
