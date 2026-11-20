"""로컬 개발용 LLM 창구 구현. OpenAI 호환 API에 붙는다."""

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.infrastructure.llm.port import LlmProvider
from app.infrastructure.settings import Settings


class OpenAiCompatibleLlm(LlmProvider):
    """.env의 OpenAI 호환 API로 채팅 모델을 만든다."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def chat_model(self) -> BaseChatModel:
        return ChatOpenAI(
            base_url=self._settings.llm_base_url or None,
            api_key=SecretStr(self._settings.llm_api_key),
            model=self._settings.llm_model,
        )
