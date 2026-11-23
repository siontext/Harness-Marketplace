"""글자 조각 흐름을 문장 흐름으로 바꾸기. 출력 검사를 문장 단위로 하려고 쓴다."""

import re
from collections.abc import AsyncGenerator, AsyncIterator

# 문장이 끝나는 자리: 마침표·물음표·느낌표 뒤 공백, 또는 줄바꿈.
# 숫자 바로 뒤의 점(목록 번호 "1. ")과 공백 없는 점("3.5일")에서는 끊지 않는다.
_SENTENCE_END = re.compile(r"(?<![0-9])[.!?。！？]+\s+|\n+")


class SentenceSplitter:
    """글자 조각을 이어 붙여 문장이 끝날 때마다 내보낸다."""

    async def split(self, texts: AsyncIterator[str]) -> AsyncGenerator[str]:
        """글자 조각 흐름을 문장 흐름으로 바꾼다. 남은 글자는 끝에 내보낸다.

        문장 뒤 공백은 문장에 붙인다. 이어 붙이면 원래 글자가 된다.

        Args:
            texts: 글자 조각 흐름 (예: LLM 답 조각).

        Yields:
            문장 하나. 마지막은 문장 끝 표시가 없는 남은 글자일 수 있다.
        """
        pending = ""
        async for text in texts:
            pending += text
            start = 0
            for match in _SENTENCE_END.finditer(pending):
                yield pending[start : match.end()]
                start = match.end()
            pending = pending[start:]
        if pending:
            yield pending
