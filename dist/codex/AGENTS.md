# Project Guidelines

## 핵심 원칙

- **아키텍처**: `layered-architecture`, `oop-principles`, `design-doc`, `implementation-doc`
- **코딩 컨벤션**: `general-style`, `java-style`, `kotlin-style`
- **테스트**: `java-testing`, `kotlin-testing`, `api-verification`
- **프레임워크**: `spring-boot-conventions`
- **프로젝트 컨텍스트**: `project-context`
- **Git**: `git-conventions`, `commit-splitting`

## 사용 가능한 에이전트

Codex가 자동으로 에이전트를 로드합니다:
- **reviewer**: 설계 문서를 기반으로 구현 코드를 검증하고 불일치 시 직접 수정하는 리뷰어
- **pr-docs**: 검증 완료된 변경 사항의 커밋, PR, 문서 초안을 준비하는 문서 작성자
- **designer**: 요구사항을 분석하고 설계 문서를 작성하는 설계 전문가
- **backend-dev**: 설계 문서를 기반으로 Java/Spring Boot 코드를 구현하는 백엔드 개발자

## 사용 가능한 스킬

### 아키텍처
- `layered-architecture` — 4-Layered + Hexagonal(Port/Adapter) 아키텍처 규칙. 레이어 간 의존 방향, 패키지 배치, Port/Adapter 구현 기준. 코드 구현 및 리뷰 시 참조.
- `oop-principles` — 객체지향 설계 원칙 — SOLID, 캡슐화, 다형성, 디자인패턴 적용 가이드. 코드 설계 및 리뷰 시 참조.
- `design-doc` — 설계 문서 작성 가이드 — 필수 구성 요소, 시니어 검증 관점, 대안 비교 기준. 설계 문서를 작성하거나 리뷰할 때 참조.
- `implementation-doc` — 구현 문서 작성 가이드 — 설계를 코드로 옮기기 위한 구체적 명세. 구현 문서를 작성하거나 구현 작업 시 참조. 구현이 완료되면 반드시 이 스킬의 전체 API 동작 검증 절차를 실행.
### 코딩 컨벤션
- `general-style` — 언어에 무관한 공통 코딩 컨벤션을 적용할 때 사용.
- `java-style` — Java 코드 스타일 가이드라인 — 네이밍, 포맷, import, 예외 처리 규칙. Java 코드를 작성하거나 리뷰할 때 참조.
- `kotlin-style` — Kotlin 코드를 작성하거나 리뷰할 때 사용하는 스타일 가이드. null safety, 이디엄, 스코프 함수, KDoc 규칙을 포함한다.
### 테스트
- `java-testing` — Java/Spring Boot 코드의 테스트를 작성하거나 리뷰할 때 사용하는 가이드. 레이어별 테스트 전략, 어노테이션, Mock 규칙을 포함한다.
- `kotlin-testing` — Kotlin/Spring Boot 코드의 테스트를 작성하거나 리뷰할 때 사용하는 가이드. MockK, 코루틴 테스트, 레이어별 전략을 포함한다.
- `api-verification` — 구현 완료 후 전체 API 동작 검증 절차 — 애플리케이션을 실제로 기동하고 모든 엔드포인트를 curl로 호출하여 설계 스펙과 대조한다. reviewer 에이전트가 검증 단계에서 실행한다.
### 프레임워크
- `spring-boot-conventions` — Spring Boot 코드를 작성하거나 리뷰할 때 사용 — DI, 어노테이션, 설정 관리, 예외 처리 규칙 적용.
### 프로젝트 컨텍스트
- `project-context` — 프로젝트의 기술 스택, 빌드 환경, 디렉토리 구조를 파악할 때 사용.
### Git
- `git-conventions` — 브랜치 네이밍, 커밋 메시지, PR 템플릿, 이슈 관리 규칙. 커밋/PR 작성 시 참조.
- `commit-splitting` — 커밋을 관심사, 역할, 변경 이유 기준으로 분리하는 규칙. 커밋 전략 수립, 스테이징 범위 결정, PR 전 커밋 정리에 사용.
