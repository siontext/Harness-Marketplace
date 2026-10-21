#!/usr/bin/env bash
# 운영 플랫폼에서 서버를 띄운다. 플랫폼 전용 견본이 있으면 /python:new가 이 파일을 덮어쓴다.
# 운영 플랫폼용 연결 창구를 쓰려면 PLATFORM에 그 이름(app/platform/<이름>.py)을 적는다.
set -euo pipefail

export PLATFORM="${PLATFORM:-}"
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
