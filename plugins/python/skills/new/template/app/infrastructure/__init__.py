"""연결 창구 묶음과 로컬/운영 구현 선택.

창구의 모양(포트, ABC)은 app/application/<기능>/port.py에 있고,
이 패키지는 그 구현을 둔다.
"""

import importlib
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.application.agent.port import Guardrail
from app.infrastructure.llm.port import LlmProvider
from app.infrastructure.prompt.port import PromptStore
from app.infrastructure.settings import Settings

LOCAL = "local"


class PlatformLoadError(RuntimeError):
    """PLATFORM 값에 맞는 연결 창구를 불러오지 못했을 때."""


@dataclass(frozen=True)
class Platform:
    """서버 시작 때 한 번 만들어 조립(app/container.py)에 넘기는 연결 창구 묶음."""

    llm: LlmProvider
    prompts: PromptStore
    guardrail: Guardrail
    closers: tuple[Callable[[], Awaitable[None]], ...] = ()

    @classmethod
    def from_settings(cls, settings: Settings) -> "Platform":
        """PLATFORM 값에 맞는 구현 모듈의 factory로 연결 창구 묶음을 만든다.

        비어 있으면 로컬 구현(app/infrastructure/local.py)을, 그 밖의 값이면
        app/infrastructure/<값>.py를 쓴다. 운영 구현을 불러오지 못하면 로컬로
        바꾸지 않고 오류를 낸다.

        Args:
            settings: 서버 시작 때 읽은 설정.

        Raises:
            PlatformLoadError: 구현 모듈이 없거나 불러오지 못할 때.
        """
        name = settings.platform or LOCAL
        try:
            module = importlib.import_module(f"app.infrastructure.{name}")
        except ImportError as e:
            raise PlatformLoadError(
                f"연결 창구를 불러오지 못했다: PLATFORM={name}"
            ) from e
        factory: PlatformFactory = module.factory
        return factory.create(settings)

    async def aclose(self) -> None:
        """열어 둔 연결을 닫는다."""
        for close in self.closers:
            await close()


class PlatformFactory(ABC):
    """연결 창구 묶음을 만드는 창구.

    로컬·운영 구현 모듈(app/infrastructure/<이름>.py)마다 구현 클래스를 하나 두고,
    그 인스턴스를 모듈의 factory 이름으로 내놓는다.
    """

    @abstractmethod
    def create(self, settings: Settings) -> Platform:
        """설정으로 연결 창구 묶음을 만든다.

        Args:
            settings: 서버 시작 때 읽은 설정.

        Returns:
            그 플랫폼의 구현을 모은 묶음.
        """
        ...
