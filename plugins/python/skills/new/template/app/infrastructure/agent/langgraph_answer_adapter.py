"""답 만들기 어댑터. LangGraph의 create_agent로 답을 만들고 글자 조각으로 바꿔 내놓는다.

LangChain·LangGraph를 아는 것은 이 파일이다. 바깥 모양을 우리 모양으로 바꾼다.
- 메시지: 조각(AIMessageChunk)으로 오든 한 번에(AIMessage) 오든 답 글자만 내놓는다.
- 실패: LLM 호출 실패를 UpstreamError로 바꾼다.
"""

from collections.abc import AsyncIterator, Awaitable, Callable, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.tools import BaseTool
from typing_extensions import override

from app.application.agent.port import AnswerGenerator
from app.common.errors import UpstreamError


class LangGraphAnswerAdapter(AnswerGenerator):
    """create_agent로 만든 에이전트가 낸 답을 글자 조각으로 내놓는다."""

    def __init__(
        self, model: BaseChatModel, tools: Sequence[BaseTool], system_prompt: str
    ) -> None:
        """에이전트를 만든다.

        Args:
            model: 에이전트가 쓸 채팅 모델.
            tools: 에이전트가 고를 도구.
            system_prompt: 시스템 프롬프트 문장.
        """
        self._agent = create_agent(
            model=model,
            tools=list(tools),
            system_prompt=system_prompt,
            middleware=[UpstreamErrorMiddleware()],
        )

    @override
    async def stream(self, question: str) -> AsyncIterator[str]:
        stream = self._agent.astream(
            {"messages": [HumanMessage(question)]}, stream_mode="messages"
        )
        async for message, _metadata in stream:
            text = self._answer_text(message)
            if text:
                yield text

    @staticmethod
    def _answer_text(message: object) -> str:
        """사용자에게 보낼 답 글자를 꺼낸다. 도구 호출과 도구 결과는 빈 글자다.

        LLM이 조각으로 보내면 AIMessageChunk가 여러 번, 한 번에 보내면 AIMessage가
        한 번 온다. AIMessageChunk는 AIMessage의 하위 클래스라서 먼저 확인한다.
        """
        if isinstance(message, AIMessageChunk):
            return "" if message.tool_call_chunks else message.text
        if isinstance(message, AIMessage):
            return "" if message.tool_calls else message.text
        return ""


class UpstreamErrorMiddleware(AgentMiddleware):
    """LLM 호출 실패를 UpstreamError로 바꿔 던진다. 도구 실행은 감싸지 않는다."""

    @override
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        try:
            return await handler(request)
        # LLM 구현마다 던지는 예외가 달라 타입을 좁힐 수 없다.
        except Exception as e:
            raise UpstreamError(f"LLM 호출 실패: {type(e).__name__}") from e
