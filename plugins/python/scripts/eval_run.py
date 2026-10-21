#!/usr/bin/env python3
"""평가 질문 실행 — evals/questions.jsonl의 질문을 /chat에 보내고 답을 모은다.

채점은 하지 않는다. 결과를 evals/results/<날짜>_<시간>.jsonl과 .md로 남긴다.
SSE(text/event-stream)와 한 번에 응답(JSON) 모두 처리한다.

사용 (프로젝트 폴더에서):
    python3 eval_run.py --url http://127.0.0.1:8765/chat [질문 id ...]

맥 기본 python3(3.9)로도 돌도록 표준 라이브러리만 쓴다.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

QUESTIONS = Path("evals/questions.jsonl")
RESULTS_DIR = Path("evals/results")
TIMEOUT_SECONDS = 120
PREVIEW_LENGTH = 60


def load_questions(ids: list[str]) -> list[dict]:
    questions = []
    for lineno, line in enumerate(QUESTIONS.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        item = json.loads(line)
        missing = [k for k in ("id", "question", "type") if k not in item]
        if missing:
            raise ValueError(f"{QUESTIONS}:{lineno} 필수 칸 없음: {', '.join(missing)}")
        if not ids or item["id"] in ids:
            questions.append(item)
    return questions


def read_sse(response) -> tuple[str, str]:
    """SSE 본문에서 token을 이어 붙여 답을, error가 있으면 오류를 돌려준다."""
    answer, error, event, data = [], "", "message", []
    for raw in response:
        line = raw.decode("utf-8").rstrip("\r\n")
        if line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].strip())
        elif line == "":
            if data:
                payload = json.loads("\n".join(data))
                if event == "token":
                    answer.append(payload.get("text", ""))
                elif event == "error":
                    error = f"{payload.get('code')}: {payload.get('message')}"
            event, data = "message", []
    return "".join(answer), error


def ask(url: str, item: dict) -> dict:
    body = json.dumps(
        {"conversation_id": f"eval-{item['id']}", "message": item["question"]},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    started = time.monotonic()
    answer, error = "", ""
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            if "text/event-stream" in response.headers.get("Content-Type", ""):
                answer, error = read_sse(response)
            else:
                answer = json.loads(response.read().decode("utf-8")).get("answer", "")
    except urllib.error.HTTPError as e:
        error = f"HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')[:200]}"
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        error = f"{type(e).__name__}: {e}"
    elapsed = round(time.monotonic() - started, 2)
    return {**item, "answer": answer, "error": error, "seconds": elapsed}


def write_results(results: list[dict]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    jsonl = RESULTS_DIR / f"{stamp}.jsonl"
    jsonl.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in results),
        encoding="utf-8",
    )
    rows = ["| id | 유형 | 질문 | 답 (앞부분) | 초 | 오류 |", "|---|---|---|---|---|---|"]
    for r in results:
        preview = r["answer"].replace("\n", " ")[:PREVIEW_LENGTH]
        cells = [r["id"], r["type"], r["question"], preview, str(r["seconds"]), r["error"]]
        rows.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    jsonl.with_suffix(".md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description="평가 질문 실행")
    parser.add_argument("--url", required=True, help="/chat 주소")
    parser.add_argument("ids", nargs="*", help="돌릴 질문 id (생략하면 전체)")
    args = parser.parse_args()

    questions = load_questions(args.ids)
    if not questions:
        print("✗ 돌릴 질문이 없습니다.")
        return 1
    results = []
    for index, item in enumerate(questions, 1):
        print(f"[{index}/{len(questions)}] {item['id']} ...", flush=True)
        results.append(ask(args.url, item))
    path = write_results(results)
    errors = sum(1 for r in results if r["error"])
    print(f"\n✓ 완료: {len(results)}개 (오류 {errors}개) → {path}, {path.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
