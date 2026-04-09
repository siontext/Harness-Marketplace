---
id: deny-rules
description: 위험한 셸 명령어를 차단해야 할 때 사용.
section: "보안"
type: deny-rules
---

| 패턴 | 설명 | 대체 방법 |
|---|---|---|
| rm -rf* | 재귀 삭제 금지 | 개별 파일 삭제(rm file) 또는 사용자에게 확인 요청 |
| git push --force* | 강제 푸시 금지 | git push --force-with-lease 사용 |
| git reset --hard* | 하드 리셋 금지 | git stash 또는 git revert 사용 |
| sudo * | 관리자 권한 금지 | 사용자에게 직접 실행 요청 |
| DROP TABLE* | 테이블 삭제 금지 | 사용자에게 확인 후 직접 실행 요청 |
