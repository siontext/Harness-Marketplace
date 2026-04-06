# Project Guidelines

## 핵심 원칙

- **아키텍처**: `layered-architecture`, `oop-principles`
- **코딩 컨벤션**: `general-style`, `java-style`
- **프레임워크**: `spring-boot-conventions`
- **프로젝트 컨텍스트**: `project-context`
- **Git**: `git-conventions`, `commit-splitting`

## 보안 — 금지 명령

다음 명령은 절대 실행하지 마세요:

- `rm -rf*` — 재귀 삭제 금지
- `git push --force*` — 강제 푸시 금지
- `git reset --hard*` — 하드 리셋 금지
- `sudo *` — 관리자 권한 금지
- `DROP TABLE*` — 테이블 삭제 금지

## 에이전트 위임

다음 서브에이전트를 사용할 수 있습니다:
- **reviewer**: 설계 문서를 기반으로 구현 코드를 검증하고 불일치 시 직접 수정하는 리뷰어
- **pr-docs**: 검증 완료된 변경 사항의 커밋, PR, 문서 초안을 준비하는 문서 작성자
- **designer**: 요구사항을 분석하고 설계 문서를 작성하는 설계 전문가
- **backend-dev**: 설계 문서를 기반으로 Java/Spring Boot 코드를 구현하는 백엔드 개발자
