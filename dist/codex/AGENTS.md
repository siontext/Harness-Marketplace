# Project Guidelines

## 핵심 원칙

- **아키텍처**: `layered-architecture`, `oop-principles`, `design-doc`, `awx-agent-design-doc`, `implementation-checkpoint`
- **코딩 컨벤션**: `general-style`, `java-style`, `kotlin-style`
- **테스트**: `java-testing`, `kotlin-testing`, `api-verification`
- **프레임워크**: `spring-boot-conventions`
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
- `design-doc` — 설계 문서 작성 가이드 — 그림·표 중심 8개 섹션과 구현 페이즈 분해. 설계 문서를 작성하거나 리뷰할 때 참조.
- `awx-agent-design-doc` — AWX(Agentic Works) 에이전트 설계 문서 작성 가이드 — 그림·표 중심 12개 섹션과 구현·이관 페이즈 분해. AWX·AgentWorks 위에서 에이전트, 챗봇, RAG, 도구 호출 기능을 설계하거나 그 설계 문서를 리뷰할 때 참조한다. 사용자가 "설계문서"라고 말하지 않아도 AWX 에이전트 설계라면 이 스킬을 따른다.
- `implementation-checkpoint` — 구현 페이즈 시작 시 대상 클래스를 제시하고, 완료 후 컴파일 확인과 사용자 승인을 받는 체크포인트 프로토콜. backend-dev 에이전트가 페이즈마다 사용.
### 코딩 컨벤션
- `general-style` — 언어에 무관한 공통 코딩 컨벤션을 적용할 때 사용.
- `java-style` — Java 코드 스타일 가이드라인 — 네이밍, 포맷, import, 예외 처리 규칙. Java 코드를 작성하거나 리뷰할 때 참조.
- `kotlin-style` — Kotlin 코드를 작성하거나 리뷰할 때 사용하는 스타일 가이드. null safety, 이디엄, 스코프 함수, KDoc 규칙을 포함한다.
### 테스트
- `java-testing` — Java/Spring Boot 코드의 테스트를 작성하거나 리뷰할 때 사용하는 가이드. 레이어별 테스트 전략, 어노테이션, Mock 규칙을 포함한다.
- `kotlin-testing` — Kotlin/Spring Boot 코드의 테스트를 작성하거나 리뷰할 때 사용하는 가이드. MockK, 코루틴 테스트, 레이어별 전략을 포함한다.
- `api-verification` — 구현 코드 검증 중 전체 API 동작을 확인해야 할 때 사용 — 애플리케이션을 실제로 기동하고 모든 엔드포인트를 curl로 호출하여 설계 스펙과 대조한다.
### 프레임워크
- `spring-boot-conventions` — Spring Boot 코드를 작성하거나 리뷰할 때 사용 — DI, 어노테이션, 설정 관리, 예외 처리 규칙 적용.
### Git
- `git-conventions` — 브랜치 네이밍, 커밋 메시지, PR 템플릿, 이슈 관리 규칙. 커밋/PR 작성 시 참조.
- `commit-splitting` — 커밋을 관심사, 역할, 변경 이유 기준으로 분리하는 규칙. 커밋 전략 수립, 스테이징 범위 결정, PR 전 커밋 정리에 사용.
