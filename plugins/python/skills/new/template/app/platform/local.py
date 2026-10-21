"""로컬 개발용 연결 창구 구현."""

from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.platform import Platform
from app.platform.ports import GuardResult
from app.platform.settings import Settings

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


class PromptNotFoundError(LookupError):
    """요청한 이름의 프롬프트 파일이 없을 때."""


class OpenAiCompatibleLlm:
    """.env의 OpenAI 호환 API로 채팅 모델을 만든다."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def chat_model(self) -> BaseChatModel:
        return ChatOpenAI(
            base_url=self._settings.llm_base_url or None,
            api_key=SecretStr(self._settings.llm_api_key),
            model=self._settings.llm_model,
        )


class FilePromptStore:
    """app/prompts/<이름>.md 파일에서 프롬프트를 읽는다."""

    def __init__(self, prompt_dir: Path = PROMPT_DIR) -> None:
        self._prompt_dir = prompt_dir

    def get(self, name: str) -> str:
        path = self._prompt_dir / f"{name}.md"
        if not path.is_file():
            raise PromptNotFoundError(f"프롬프트 파일이 없다: {path.name}")
        return path.read_text(encoding="utf-8")


class PassThroughGuardrail:
    """로컬에서는 검사 없이 그대로 통과시킨다. 필수 규칙은 코드에 따로 둔다."""

    async def check_input(self, text: str) -> GuardResult:
        return GuardResult(text=text)

    async def check_output(self, text: str) -> GuardResult:
        return GuardResult(text=text)


def create_platform(settings: Settings) -> Platform:
    """로컬 연결 창구 묶음을 만든다."""
    return Platform(
        llm=OpenAiCompatibleLlm(settings),
        prompts=FilePromptStore(),
        guardrail=PassThroughGuardrail(),
    )
