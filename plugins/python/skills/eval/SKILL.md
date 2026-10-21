---
name: eval
description: 실제 LLM으로 평가 질문(evals/questions.jsonl)을 돌린다 — 연결 확인(LLM·도구 호출 지원 여부) → 비용 확인 → 로컬 서버의 /chat으로 질문 실행 → 결과 저장. 채점 방식은 정하지 않고 사용자와 함께 정한다. API 비용이 들어서 사용자가 /python:eval을 직접 칠 때만 실행한다.
disable-model-invocation: true
argument-hint: "[질문 id 여러 개, 생략하면 전체]"
---

# 평가 실행

이 명령은 **틀만** 맡는다: 연결 확인 → 비용 확인 → 질문 실행 → 결과 저장. 어떻게 채점할지는 정하지 않는다.

스크립트 폴더: `${CLAUDE_PLUGIN_ROOT}/scripts` (비어 있으면 `~/.claude/plugins/marketplaces/team-harness/plugins/python/scripts`). 아래에서 `<scripts>`로 쓴다.

인자: `$ARGUMENTS` — 돌릴 질문 id (예: `q01 q03`). 없으면 전체.

## 절차

### 1. 준비 확인

- `.venv`, `.env`, `evals/questions.jsonl`이 있는지 본다. 없으면 멈추고 알린다.
- `.env`의 `LLM_*` 값이 비어 있으면 멈춘다. 값은 출력하지 않는다.

### 2. 연결 확인

```bash
.venv/bin/python <scripts>/eval_check.py
```

- LLM에 짧게 한 번 묻고, 도구 하나를 붙여 **도구 호출을 지원하는지** 확인한다.
- 연결이 안 되면 평가를 시작하지 않는다.
- 도구 호출을 지원하지 않으면 그 사실을 알린다. 흐름 방식이 `create_agent`면 `langgraph-conventions`의 "LLM이 도구 호출을 지원하지 않을 때"를 안내한다.
- 설계 문서에 대화 기억(Redis)·대화 기록(PostgreSQL)이 있으면 그 연결도 확인한다 (`redis-cli ping`, `pg_isready` 등). 안 되면 멈춘다.

### 3. 비용 확인

- 질문 개수와 예상 LLM 호출 수(질문 수 × 1~3번, 도구를 쓰는 만큼 늘어남)를 보여준다.
- 사용자가 "예"라고 해야 시작한다.

### 4. 실행

```bash
.venv/bin/uvicorn main:app --port 8765          # 백그라운드로 띄운다
python3 <scripts>/eval_run.py --url http://127.0.0.1:8765/chat [질문 id...]
```

- 서버는 로컬 연결 창구(`PLATFORM` 비움)로 띄운다. `/health`가 응답할 때까지 기다린 뒤 실행한다.
- `eval_run.py`가 질문마다 `/chat`을 부르고 답, 걸린 시간, 오류를 모은다 (SSE와 한 번에 응답 모두 처리).
- 끝나면 서버를 끈다.

### 5. 결과 저장과 보고

- 결과는 `evals/results/<날짜>_<시간>.jsonl`과 같은 이름의 `.md` 표에 저장된다. 반출에서 빠진다.
- 사용자에게 표(질문, 유형, 답 앞부분, 시간, 오류)를 보여준다.
- 채점 방식이 아직 없으면 결과를 같이 보면서 정하자고 제안한다. 예: 답이 정해진 질문은 규칙(도구·핵심 단어), 답이 자유로운 질문은 다른 LLM이 채점(LLM-as-a-Judge). **정할 때까지 통과/실패를 판정하지 않는다.**
- 정해진 채점 방식이 `evals/`에 있으면 그대로 따른다.

## 하지 않는 것

- 사용자 확인 없이 평가를 시작하지 않는다.
- `.env`의 키·주소를 출력하거나 결과 파일에 남기지 않는다.
- 평가 결과를 보고 코드나 프롬프트를 묻지 않고 고치지 않는다.
