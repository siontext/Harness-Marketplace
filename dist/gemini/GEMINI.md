# Project Guidelines

## 핵심 원칙

- **아키텍처**: `skills/layered-architecture.md`, `skills/oop-principles.md`
- **코딩 컨벤션**: `skills/general-style.md`, `skills/java-style.md`, `skills/kotlin-style.md`
- **테스트**: `skills/java-testing.md`, `skills/kotlin-testing.md`
- **프레임워크**: `skills/spring-boot-conventions.md`
- **프로젝트 컨텍스트**: `skills/project-context.md`
- **Git**: `skills/git-conventions.md`, `skills/commit-splitting.md`

## 작업 프로토콜

작업을 받으면 다음 절차를 따르세요:

1. **에이전트 파일 읽기**: 아래 에이전트 중 적절한 것을 선택하고, 해당 파일을 읽는다.
2. **스킬 파일 읽기**: 에이전트 파일의 `skills:` 메타데이터에 명시된 스킬 파일을 모두 읽는다.
3. **도구 제한 준수**: 에이전트 파일의 "허용/금지" 도구 목록을 따른다.
4. **동작 흐름 실행**: 에이전트 파일에 정의된 절차대로 작업한다.

에이전트가 명시되지 않은 일반 작업은 관련 스킬 파일만 읽고 작업하세요.

## 사용 가능한 에이전트

- **설계 문서를 기반으로 구현 코드를 검증하고 불일치 시 직접 수정하는 리뷰어**: `agents/reviewer.md`
- **검증 완료된 변경 사항의 커밋, PR, 문서 초안을 준비하는 문서 작성자**: `agents/pr-docs.md`
- **요구사항을 분석하고 설계 문서를 작성하는 설계 전문가**: `agents/designer.md`
- **설계 문서를 기반으로 Java/Spring Boot 코드를 구현하는 백엔드 개발자**: `agents/backend-dev.md`

## 사용 가능한 스킬

### 아키텍처
- `skills/layered-architecture.md` — 4-Layered + Hexagonal(Port/Adapter) 아키텍처 규칙. 레이어 간 의존 방향, 패키지 배치, Port/Adapter 구현 기준. 코드 구현 및 리뷰 시 참조.
- `skills/oop-principles.md` — 객체지향 설계 원칙 — SOLID, 캡슐화, 다형성, 디자인패턴 적용 가이드. 코드 설계 및 리뷰 시 참조.
### 코딩 컨벤션
- `skills/general-style.md` — 공통 코딩 컨벤션
- `skills/java-style.md` — Java 코드 스타일 가이드라인 — 네이밍, 포맷, import, 예외 처리 규칙. Java 코드를 작성하거나 리뷰할 때 참조.
- `skills/kotlin-style.md` — Kotlin 코드를 작성하거나 리뷰할 때 사용하는 스타일 가이드. null safety, 이디엄, 스코프 함수, KDoc 규칙을 포함한다.
### 테스트
- `skills/java-testing.md` — Java/Spring Boot 코드의 테스트를 작성하거나 리뷰할 때 사용하는 가이드. 레이어별 테스트 전략, 어노테이션, Mock 규칙을 포함한다.
- `skills/kotlin-testing.md` — Kotlin/Spring Boot 코드의 테스트를 작성하거나 리뷰할 때 사용하는 가이드. MockK, 코루틴 테스트, 레이어별 전략을 포함한다.
### 프레임워크
- `skills/spring-boot-conventions.md` — Spring Boot + 4-Layered + Hexagonal 아키텍처 기반 DI, 어노테이션, 설정 관리, 예외 처리 규칙. Spring Boot 코드 작성 및 리뷰 시 참조.
### 프로젝트 컨텍스트
- `skills/project-context.md` — 프로젝트 기술 스택 및 환경
### Git
- `skills/git-conventions.md` — 브랜치 네이밍, 커밋 메시지, PR 템플릿, 이슈 관리 규칙. 커밋/PR 작성 시 참조.
- `skills/commit-splitting.md` — 커밋을 관심사, 역할, 변경 이유 기준으로 분리하는 규칙. 커밋 전략 수립, 스테이징 범위 결정, PR 전 커밋 정리에 사용.
