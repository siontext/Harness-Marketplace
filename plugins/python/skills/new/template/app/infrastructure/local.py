"""로컬 개발용 연결 창구 묶음. 로컬 구현들을 모아 Platform을 만든다."""

from app.infrastructure import Platform
from app.infrastructure.guardrail.pass_through import PassThroughGuardrail
from app.infrastructure.llm.openai_compatible import OpenAiCompatibleLlm
from app.infrastructure.prompt.file_prompt_store import FilePromptStore
from app.infrastructure.settings import Settings


def create_platform(settings: Settings) -> Platform:
    """로컬 연결 창구 묶음을 만든다."""
    return Platform(
        llm=OpenAiCompatibleLlm(settings),
        prompts=FilePromptStore(),
        guardrail=PassThroughGuardrail(),
    )
