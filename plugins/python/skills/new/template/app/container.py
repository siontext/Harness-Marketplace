"""조립. 연결 창구 구현을 서비스·도구·에이전트에 넣어 실행 재료를 만든다.

app/infrastructure와 app/application을 함께 아는 곳은 이 파일 하나다.
application은 구현을 모르고, 여기서 넣어 준 것만 쓴다.
에이전트를 만들면 조립 함수(예: build_agent_context)를 여기에 두고 main.py가 부른다.
"""
