"""로컬 개발용 연결 창구 묶음. 로컬 구현들을 모아 Platform을 만든다."""

from typing_extensions import override

from app.infrastructure import Platform, PlatformFactory
from app.infrastructure.guardrail.pass_through_guardrail_adapter import (
    PassThroughGuardrailAdapter,
)
from app.infrastructure.llm.openai_compatible_llm_adapter import (
    OpenAiCompatibleLlmAdapter,
)
from app.infrastructure.prompt.file_prompt_adapter import FilePromptAdapter
from app.infrastructure.settings import Settings


class LocalPlatformFactory(PlatformFactory):
    """로컬 구현들을 모아 연결 창구 묶음을 만든다."""

    @override
    def create(self, settings: Settings) -> Platform:
        return Platform(
            llm=OpenAiCompatibleLlmAdapter(settings),
            prompts=FilePromptAdapter(),
            guardrail=PassThroughGuardrailAdapter(),
        )


# Platform.from_settings가 PLATFORM 값으로 이 모듈을 불러 이 이름으로 찾는다.
factory = LocalPlatformFactory()
