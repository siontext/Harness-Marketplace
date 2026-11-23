"""프로젝트 공통 예외. 표준 라이브러리만 쓰고 HTTP(상태 코드, code)를 모른다.

여러 레이어가 던지거나 전역 핸들러(app/presentation/exception/)가 구분해 답해야
하는 예외만 둔다.
한 레이어 안에서만 쓰는 예외는 그 레이어에 둔다.
어떤 예외를 무엇으로 답할지는 app/presentation/exception/error_rule.py의
ErrorRuleBook 대응표가 정한다.
"""


class AppError(Exception):
    """프로젝트 코드가 던지는 예외의 기반.

    메시지에는 맥락(id 등)을 넣되 키·개인정보는 넣지 않는다.
    다른 예외를 바꿔 던질 때는 `raise ... from e`로 원인을 잇는다.
    """


class UpstreamError(AppError):
    """LLM이나 외부 시스템이 실패했을 때."""


class AgentTimeoutError(AppError):
    """에이전트 실행이 시간 제한을 넘겼을 때.

    내장 TimeoutError를 가리지 않도록 이름에 Agent를 붙였다.
    """
