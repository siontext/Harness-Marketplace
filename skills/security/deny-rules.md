---
id: deny-rules
description: "위험 명령어 차단"
section: "보안"
type: deny-rules
---

| 패턴 | 설명 |
|---|---|
| rm -rf* | 재귀 삭제 금지 |
| git push --force* | 강제 푸시 금지 |
| git reset --hard* | 하드 리셋 금지 |
| sudo * | 관리자 권한 금지 |
| DROP TABLE* | 테이블 삭제 금지 |
