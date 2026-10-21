#!/usr/bin/env python3
"""평가 전 연결 확인 — 실제 LLM에 짧게 묻고, 도구 호출을 지원하는지 본다.

프로젝트 폴더에서 프로젝트 가상환경으로 실행한다:
    .venv/bin/python <이 파일>

연결 창구(app.platform.build_platform)로 LLM을 가져오므로 .env 설정을 그대로 쓴다.
키·주소는 출력하지 않는다.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from langchain_core.tools import tool  # noqa: E402

from app.platform import build_platform  # noqa: E402


@tool
def get_weather(city: str) -> str:
    """도시 이름으로 오늘 날씨를 조회한다.

    Args:
        city: 도시 이름 (예: 서울).
    """
    return f"{city}: 맑음"


async def main() -> int:
    platform = build_platform()
    model = platform.llm.chat_model()
    try:
        reply = await model.ainvoke("연결 확인입니다. '확인'이라고만 답하세요.")
    except Exception as e:  # 어떤 연결 오류든 원인 이름만 보여주고 멈춘다
        print(f"✗ LLM 연결 실패: {type(e).__name__}")
        return 1
    print(f"✓ LLM 연결 성공 (답 길이 {len(reply.text)}자)")

    try:
        tool_reply = await model.bind_tools([get_weather]).ainvoke(
            "서울 날씨를 get_weather 도구로 조회해 주세요."
        )
        supported = bool(getattr(tool_reply, "tool_calls", None))
    except Exception as e:  # 도구 연결 자체를 거부하는 모델도 있다
        print(f"! 도구 호출 확인 중 오류: {type(e).__name__}")
        supported = False
    print("✓ 도구 호출 지원" if supported else "! 도구 호출 미지원 (또는 이번 답에서 쓰지 않음)")
    await platform.aclose()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
