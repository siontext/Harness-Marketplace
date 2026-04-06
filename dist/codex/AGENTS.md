# Project Guidelines

## 핵심 원칙

- **아키텍처**: `layered-architecture`, `oop-principles`
- **코딩 컨벤션**: `general-style`, `java-style`
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
### 코딩 컨벤션
- `general-style` — 공통 코딩 컨벤션
- `java-style` — Java 코드 스타일 가이드라인 — 네이밍, 포맷, import, 예외 처리 규칙. Java 코드를 작성하거나 리뷰할 때 참조.
### 프레임워크
- `spring-boot-conventions` — Spring Boot + 4-Layered + Hexagonal 아키텍처 기반 DI, 어노테이션, 설정 관리, 예외 처리 규칙. Spring Boot 코드 작성 및 리뷰 시 참조.
### 프로젝트 컨텍스트
- `project-context` — 프로젝트 기술 스택 및 환경
### Git
- `git-conventions` — 브랜치 네이밍, 커밋 메시지, PR 템플릿, 이슈 관리 규칙. 커밋/PR 작성 시 참조.
- `commit-splitting` — 커밋을 관심사, 역할, 변경 이유 기준으로 분리하는 규칙. 커밋 전략 수립, 스테이징 범위 결정, PR 전 커밋 정리에 사용.
