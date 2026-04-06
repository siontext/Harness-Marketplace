# Project Guidelines

## 핵심 원칙

- **아키텍처**: `rules/layered-architecture.md`, `rules/oop-principles.md`
- **코딩 컨벤션**: `rules/general-style.md`, `rules/java-style.md`
- **프레임워크**: `rules/spring-boot-conventions.md`
- **프로젝트 컨텍스트**: `rules/project-context.md`
- **Git**: `rules/git-conventions.md`, `rules/commit-splitting.md`

## 작업 프로토콜

작업을 받으면 다음 절차를 따르세요:

1. **역할 파일 읽기**: 아래 역할 중 적절한 것을 선택하고, 해당 파일을 읽는다.
2. **규칙 파일 읽기**: 역할 파일의 `rules:` 메타데이터에 명시된 규칙 파일을 모두 읽는다.
3. **도구 제한 준수**: 역할 파일의 "허용/금지" 도구 목록을 따른다.
4. **동작 흐름 실행**: 역할 파일에 정의된 절차대로 작업한다.

역할이 명시되지 않은 일반 작업은 관련 규칙 파일만 읽고 작업하세요.

## 사용 가능한 역할

- **설계 문서를 기반으로 구현 코드를 검증하고 불일치 시 직접 수정하는 리뷰어**: `roles/reviewer.md`
- **검증 완료된 변경 사항의 커밋, PR, 문서 초안을 준비하는 문서 작성자**: `roles/pr-docs.md`
- **요구사항을 분석하고 설계 문서를 작성하는 설계 전문가**: `roles/designer.md`
- **설계 문서를 기반으로 Java/Spring Boot 코드를 구현하는 백엔드 개발자**: `roles/backend-dev.md`

## 사용 가능한 규칙

### 아키텍처
- `rules/layered-architecture.md` — 4-Layered + Hexagonal(Port/Adapter) 아키텍처 규칙. 레이어 간 의존 방향, 패키지 배치, Port/Adapter 구현 기준. 코드 구현 및 리뷰 시 참조.
- `rules/oop-principles.md` — 객체지향 설계 원칙 — SOLID, 캡슐화, 다형성, 디자인패턴 적용 가이드. 코드 설계 및 리뷰 시 참조.
### 코딩 컨벤션
- `rules/general-style.md` — 공통 코딩 컨벤션
- `rules/java-style.md` — Java 코드 스타일 가이드라인 — 네이밍, 포맷, import, 예외 처리 규칙. Java 코드를 작성하거나 리뷰할 때 참조.
### 프레임워크
- `rules/spring-boot-conventions.md` — Spring Boot + 4-Layered + Hexagonal 아키텍처 기반 DI, 어노테이션, 설정 관리, 예외 처리 규칙. Spring Boot 코드 작성 및 리뷰 시 참조.
### 프로젝트 컨텍스트
- `rules/project-context.md` — 프로젝트 기술 스택 및 환경
### Git
- `rules/git-conventions.md` — 브랜치 네이밍, 커밋 메시지, PR 템플릿, 이슈 관리 규칙. 커밋/PR 작성 시 참조.
- `rules/commit-splitting.md` — 커밋을 관심사, 역할, 변경 이유 기준으로 분리하는 규칙. 커밋 전략 수립, 스테이징 범위 결정, PR 전 커밋 정리에 사용.
