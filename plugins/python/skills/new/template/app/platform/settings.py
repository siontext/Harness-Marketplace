"""환경 변수 설정. 이 모듈 밖에서는 환경 변수를 읽지 않는다."""

import os
from dataclasses import dataclass
from pathlib import Path

ENV_FILE = Path(".env")


@dataclass(frozen=True)
class Settings:
    """서버가 쓰는 환경 변수 묶음."""

    platform: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str


def load_settings(env_file: Path = ENV_FILE) -> Settings:
    """환경 변수를 읽어 설정을 만든다.

    로컬에서는 .env 파일 값을 함께 읽는다. 이미 설정된 환경 변수가 우선한다.

    Args:
        env_file: 읽을 .env 파일 경로. 없으면 환경 변수만 쓴다.

    Returns:
        읽은 설정.
    """
    values = {**_read_env_file(env_file), **os.environ}
    return Settings(
        platform=values.get("PLATFORM", ""),
        llm_base_url=values.get("LLM_BASE_URL", ""),
        llm_api_key=values.get("LLM_API_KEY", ""),
        llm_model=values.get("LLM_MODEL", ""),
    )


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
