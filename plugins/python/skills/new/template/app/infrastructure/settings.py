"""환경 변수 설정. 이 모듈 밖에서는 환경 변수를 읽지 않는다."""

import os
from dataclasses import dataclass
from pathlib import Path

ENV_FILE = Path(".env")
# 설계 문서 개요 "시간 제한"의 우리 쪽 값. AGENT_TIMEOUT_SECONDS를 비우면 이 값을 쓴다.
DEFAULT_AGENT_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class Settings:
    """서버가 쓰는 환경 변수 묶음.

    Attributes:
        platform: 연결 창구 이름. 비어 있으면 로컬.
        llm_base_url: 로컬 LLM(OpenAI 호환 API) 주소.
        llm_api_key: 로컬 LLM 키.
        llm_model: 로컬 LLM 모델 이름.
        agent_timeout_seconds: 질문 하나에 답하는 전체 시간 제한(초).
    """

    platform: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    agent_timeout_seconds: float = DEFAULT_AGENT_TIMEOUT_SECONDS


def load_settings(env_file: Path = ENV_FILE) -> Settings:
    """환경 변수를 읽어 설정을 만든다.

    로컬에서는 .env 파일 값을 함께 읽는다. 이미 설정된 환경 변수가 우선한다.

    Args:
        env_file: 읽을 .env 파일 경로. 없으면 환경 변수만 쓴다.

    Returns:
        읽은 설정.

    Raises:
        ValueError: AGENT_TIMEOUT_SECONDS가 숫자가 아니거나 0 이하일 때.
    """
    values = {**_read_env_file(env_file), **os.environ}
    return Settings(
        platform=values.get("PLATFORM", ""),
        llm_base_url=values.get("LLM_BASE_URL", ""),
        llm_api_key=values.get("LLM_API_KEY", ""),
        llm_model=values.get("LLM_MODEL", ""),
        agent_timeout_seconds=_read_seconds(
            "AGENT_TIMEOUT_SECONDS",
            values.get("AGENT_TIMEOUT_SECONDS", ""),
            DEFAULT_AGENT_TIMEOUT_SECONDS,
        ),
    )


def _read_seconds(name: str, raw: str, default: float) -> float:
    """초 단위 설정 값을 읽는다. 비어 있으면 기본값을 쓴다.

    0 이하면 모든 질문이 바로 시간 초과가 되므로 서버가 뜨지 않게 오류를 낸다.
    """
    value = raw.strip()
    if not value:
        return default
    seconds = float(value)
    if seconds <= 0:
        raise ValueError(f"{name}는 0보다 커야 한다: {value}")
    return seconds


def _read_env_file(env_file: Path) -> dict[str, str]:
    """KEY=VALUE 형식의 .env 파일을 딕셔너리로 읽는다."""
    if not env_file.is_file():
        return {}
    values: dict[str, str] = {}
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values
