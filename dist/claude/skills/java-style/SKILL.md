---
name: java-style
description: Java 코드 스타일 가이드라인 — 네이밍, 포맷, import, 예외 처리 규칙. Java 코드를 작성하거나 리뷰할 때 참조.
---

# Java Code Style Guide

## 네이밍 규칙

- 클래스/인터페이스: `PascalCase` (예: `OrderService`, `PaymentPort`)
- 메서드/변수: `camelCase` (예: `findById`, `totalPrice`)
- 상수: `UPPER_SNAKE_CASE` (예: `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`)
- 패키지: 소문자만 (예: `com.example.order`)
- Boolean 변수/메서드: `is`, `has`, `can` 접두사 (예: `isActive`, `hasPermission`)

## Import

- 와일드카드(`*`) import 금지. 명시적으로 클래스 지정.
- 사용하지 않는 import 제거.
- import 순서: java → javax → org → com → 프로젝트 패키지. 그룹 사이 빈 줄.

## 메서드

- 한 메서드 30줄 이내 권장. 초과 시 분리 검토.
- 파라미터 3개 이내 권장. 초과 시 객체로 묶기.
- 메서드명은 동사로 시작 (예: `create`, `find`, `update`, `delete`).
- 하나의 메서드는 하나의 책임만 수행.

## 예외 처리

- checked exception 최소화. 비즈니스 예외는 `RuntimeException` 상속.
- 의미 있는 커스텀 예외 사용 (예: `OrderNotFoundException`).
- `catch (Exception e)` 남용 금지. 구체적인 예외 타입 지정.
- 예외 메시지에 맥락 포함 (예: `"Order not found: id=" + orderId`).

## 기타

- 매직 넘버 금지. 상수로 추출.
- `Optional` 반환은 허용, 파라미터로 전달은 금지.
- `var` 사용은 타입이 명확한 경우에만 (예: `var list = new ArrayList<String>()`).
- 주석: 코드로 설명 가능하면 생략. Javadoc은 public API에만.
