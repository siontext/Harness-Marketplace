# Java/Spring Boot 코드의 테스트를 작성하거나 리뷰할 때 사용하는 가이드. 레이어별 테스트 전략, 어노테이션, Mock 규칙을 포함한다.

# Java/Spring Boot Testing Guide

## Test Stack

- 기본 스택은 JUnit 5, Mockito, Spring Boot Test를 사용한다.
- 단언은 AssertJ를 우선 사용한다.

## Layer Strategy

- Domain: 순수 단위 테스트로 검증한다.
- Application: `@ExtendWith(MockitoExtension.class)` 기반 단위 테스트를 사용하고 outbound port만 mock 처리한다.
- Presentation: `@WebMvcTest`로 HTTP 요청/응답 계약을 검증한다.
- Infrastructure: `@DataJpaTest` 또는 필요한 범위의 통합 테스트로 검증한다.

## Mock Rule

- DB, 외부 API, 메시지 브로커 같은 outbound dependency만 mock 한다.
- 도메인 객체와 값 객체는 mock 하지 않는다.
- `given` / `then` 기반 BDD 스타일을 우선 사용한다.

## Test Design

- 테스트 이름은 한글로 작성하며, 행위와 기대 결과가 드러나도록 작성한다.
- Given-When-Then 구조를 유지한다.
- 한 테스트는 하나의 행위만 검증한다.
- 생산 코드 변경 시 핵심 흐름과 실패 경로 테스트가 존재하는지 함께 확인한다.
