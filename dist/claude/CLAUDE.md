# Project Guidelines

## 핵심 원칙

- **아키텍처**: `layered-architecture`, `oop-principles`, `design-doc`, `implementation-doc`, `implementation-checkpoint`
- **코딩 컨벤션**: `general-style`, `java-style`, `kotlin-style`
- **테스트**: `java-testing`, `kotlin-testing`, `api-verification`
- **프레임워크**: `spring-boot-conventions`
- **프로젝트 컨텍스트**: `project-context`
- **Git**: `git-conventions`, `commit-splitting`

## 보안 — 금지 명령

다음 명령은 절대 실행하지 마세요:

- `rm -rf*` — 재귀 삭제 금지 → 대신: 개별 파일 삭제(rm file) 또는 사용자에게 확인 요청
- `git push --force*` — 강제 푸시 금지 → 대신: git push --force-with-lease 사용
- `git reset --hard*` — 하드 리셋 금지 → 대신: git stash 또는 git revert 사용
- `sudo *` — 관리자 권한 금지 → 대신: 사용자에게 직접 실행 요청
- `DROP TABLE*` — 테이블 삭제 금지 → 대신: 사용자에게 확인 후 직접 실행 요청

## 워크플로우

- 브레인스토밍/설계 작업 시 `oop-principles`, `layered-architecture` 스킬을 반드시 참조할 것.
- 설계 방향이 결정되면 `designer` 에이전트에게 문서 작성을 위임할 것.
- 코드 검증/리뷰 시 `reviewer` 에이전트에게 위임할 것.

## 에이전트 위임

### 서브에이전트 실행/정리 방식

- 서브에이전트는 background(`run_in_background`)로 띄우지 말고, **`name`을 붙여 포그라운드 teammate로 띄울 것** — tmux pane(패널)에 작업 진행 상황이 보여야 한다.
- 서브에이전트가 작업을 마치고 **idle 알림을 보내면, 결과 회수 후 즉시 `shutdown_request`를 보내 정리할 것** — idle 상태로 방치하지 않는다.
- 이유: Claude Code에 "완료 시 자동 정리" 설정이 없음. background는 pane이 안 떠서 진행 상황이 안 보이고, 포그라운드는 끝나도 idle로 대기함.

다음 서브에이전트를 사용할 수 있습니다:
- **reviewer**: 설계 문서를 기반으로 구현 코드를 검증하고 불일치 시 직접 수정하는 리뷰어
- **pr-docs**: 검증 완료된 변경 사항의 커밋, PR, 문서 초안을 준비하는 문서 작성자
- **designer**: 요구사항을 분석하고 설계 문서를 작성하는 설계 전문가
- **backend-dev**: 설계 문서를 기반으로 Java/Spring Boot 코드를 구현하는 백엔드 개발자
