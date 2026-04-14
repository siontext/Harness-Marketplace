---
name: kotlin-style
description: Kotlin 코드를 작성하거나 리뷰할 때 사용하는 스타일 가이드. null safety, 이디엄, 스코프 함수, KDoc 규칙을 포함한다.
---

# Kotlin Code Style Guide

## 기본 규칙

- 클래스와 인터페이스는 `PascalCase`, 함수와 변수는 `camelCase`, 상수는 `UPPER_SNAKE_CASE`를 사용한다.
- `Optional` 대신 nullable 타입을 사용한다.
- `!!` 사용은 금지하고 `?:`, `?.let`, `requireNotNull`로 null 처리를 명시한다.
- DTO와 Value Object는 `data class`를 우선 사용한다.
- 도메인 엔티티는 상태와 행위를 함께 가지는 일반 `class`로 작성한다.

## Kotlin Idiom

- 단순 변환과 null 처리에는 스코프 함수를 사용하되 중첩 사용은 피한다.
- `let`, `apply`, `also`, `run`, `with`는 용도가 분명할 때만 사용한다.
- 유틸리티 성격의 변환은 extension function으로 분리한다.
- 비즈니스 로직은 extension function이 아니라 타입의 멤버 함수에 둔다.

## Null Safety

- 반환값이 없을 수 있으면 nullable 타입으로 표현한다.
- `if (x != null)`보다 Elvis 연산자와 safe call을 우선 고려한다.
- 컬렉션 필터링은 `filterNotNull()` 같은 표준 함수를 우선 사용한다.

## Spring + Kotlin

- 의존성 주입은 primary constructor로 처리한다.
- 설정값 바인딩은 `data class` 기반 `@ConfigurationProperties`를 우선 사용한다.
- 코루틴을 사용하는 함수는 `suspend` 여부가 드러나도록 API 경계를 명확하게 유지한다.

## Documentation

### KDoc 필수 대상

- **Port 인터페이스** (Inbound/Outbound): 모든 메서드에 @param, @return, @throws 명시.
- **UseCase 인터페이스**: 모든 메서드에 @param, @return, @throws 명시.
- **Domain 클래스**: 클래스 레벨 설명 필수. 팩토리 메서드(companion object)에는 비즈니스 규칙과 제약 조건 명시.
- **VO (Value Object)**: 클래스 레벨 설명 필수. 생성 제약이 있으면 팩토리 메서드에도 명시.
- **Command / Result DTO**: 클래스 레벨 설명 + @property로 모든 필드 설명.
- **Entity (JPA)**: 클래스 레벨 설명 필수. toDomain/fromDomain 메서드에 @param, @return 명시.
- **Adapter/Repository 구현체**: 클래스 레벨에 어떤 Port를 구현하는지 간단히 명시.
- **Controller 메서드**: 요청/응답 명세. @param, @return 명시.

### KDoc 불필요 대상

- 구현 클래스의 override 메서드 (인터페이스에 이미 있음)
- 자명한 getter, 자명한 메서드
- Request DTO — @Schema(Swagger)로 대체
