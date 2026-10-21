"""연결 창구 묶음과 로컬/운영 구현 선택."""

import importlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.platform.ports import Guardrail, LlmProvider, PromptStore
from app.platform.settings import Settings, load_settings

LOCAL = "local"


class PlatformLoadError(RuntimeError):
    """PLATFORM 값에 맞는 연결 창구를 불러오지 못했을 때."""


@dataclass(frozen=True)
class Platform:
    """서버 시작 때 한 번 만들어 에이전트에 넘기는 연결 창구 묶음."""

    llm: LlmProvider
    prompts: PromptStore
    guardrail: Guardrail
    closers: tuple[Callable[[], Awaitable[None]], ...] = ()

    async def aclose(self) -> None:
        """열어 둔 연결을 닫는다."""
        for close in self.closers:
            await close()


def build_platform(settings: Settings | None = None) -> Platform:
    """PLATFORM 환경 변수에 맞는 연결 창구 묶음을 만든다.

    비어 있으면 로컬 구현(app/platform/local.py)을, 그 밖의 값이면
    app/platform/<값>.py를 쓴다. 운영 구현을 불러오지 못하면 로컬로
    바꾸지 않고 오류를 낸다.

    Args:
        settings: 쓸 설정. 없으면 환경 변수와 .env에서 읽는다.

    Raises:
        PlatformLoadError: 구현 모듈이 없거나 불러오지 못할 때.
    """
    settings = settings or load_settings()
    name = settings.platform or LOCAL
    try:
        module = importlib.import_module(f"app.platform.{name}")
    except ImportError as e:
        raise PlatformLoadError(f"연결 창구를 불러오지 못했다: PLATFORM={name}") from e
    return module.create_platform(settings)
