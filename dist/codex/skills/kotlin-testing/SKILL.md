---
name: kotlin-testing
description: Kotlin/Spring Boot 코드의 테스트를 작성하거나 리뷰할 때 사용하는 가이드. MockK, 코루틴 테스트, 레이어별 전략을 포함한다.
---

# Kotlin/Spring Boot Testing Guide

## Test Stack

- 기본 스택은 JUnit 5, MockK, Spring Boot Test를 사용한다.
- 코루틴 테스트에는 `runTest`를 사용한다.

## Layer Strategy

- Domain: 순수 단위 테스트로 검증한다.
- Application: `@ExtendWith(MockKExtension::class)` 기반 테스트를 사용하고 outbound port만 mock 처리한다.
- Presentation: `@WebMvcTest`와 `@MockkBean`으로 웹 계층 계약을 검증한다.
- Infrastructure: 필요한 범위의 통합 테스트로 실제 저장소 동작을 검증한다.

## MockK Rule

- 기본 스텁은 `every` / `verify`, suspend 함수는 `coEvery` / `coVerify`를 사용한다.
- `relaxed = true`는 검증 누락 위험이 있을 때 피한다.
- Mockito와 MockK를 같은 테스트에서 섞지 않는다.

## Test Design

- 백틱 기반 테스트 이름으로 시나리오를 드러낸다.
- Given-When-Then 구조를 유지한다.
- 코루틴 경계와 예외 흐름 테스트를 함께 확인한다.
