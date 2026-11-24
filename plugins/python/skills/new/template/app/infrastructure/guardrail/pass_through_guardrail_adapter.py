"""로컬 개발용 가드레일 창구 구현. 검사하지 않고 통과시킨다."""

from typing_extensions import override

from app.application.agent.port import Guardrail, GuardResult


class PassThroughGuardrailAdapter(Guardrail):
    """로컬에서는 검사 없이 그대로 통과시킨다. 필수 규칙은 코드에 따로 둔다."""

    @override
    async def check_input(self, text: str) -> GuardResult:
        return GuardResult(text=text)

    @override
    async def check_output(self, text: str) -> GuardResult:
        return GuardResult(text=text)
