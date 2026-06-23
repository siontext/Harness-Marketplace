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
## 주석 및 Javadoc

### Javadoc 필수 대상

- **Port 인터페이스** (Inbound/Outbound): 모든 메서드에 @param, @return, @throws 명시.
- **UseCase 인터페이스**: 모든 메서드에 @param, @return, @throws 명시.
- **Domain 클래스**: 클래스 레벨 설명 필수. 팩토리 메서드에는 비즈니스 규칙과 제약 조건 명시.
- **VO (Value Object)**: 클래스 레벨 설명 필수. 생성 제약이 있으면 팩토리 메서드에도 명시.
- **Command / Result DTO**: 클래스 레벨 설명 + @param으로 모든 필드 설명.
- **Entity (JPA)**: 클래스 레벨 설명 필수. toDomain/fromDomain 메서드에 @param, @return 명시.
- **Adapter/Repository 구현체**: 클래스 레벨에 어떤 Port를 구현하는지 간단히 명시.
- **Controller 메서드**: 요청/응답 명세. @param, @return 명시.

```java
/**
 * 주문을 저장하고 ID가 할당된 주문을 반환한다.
 *
 * @param order ID가 없는 신규 주문
 * @return ID가 할당된 저장된 주문
 * @throws IllegalArgumentException order가 null이거나 유효하지 않은 경우
 */
Order save(Order order);
```

### Javadoc 작성 스타일

- **첫 문장에 책임을 적는다.** 처음 보는 사람이 첫 줄만 읽고 "이게 뭘 하는 애인지" 알 수 있어야 한다.
  - 형식: `~을 ~로부터 ~하는 포트/VO` 처럼 대상·동작이 첫 문장에 드러나게.
- **HTML 포맷 태그 금지.** `<p>`, `<b>`, `<ul>`, `<li>` 등으로 꾸미지 않는다. 평문으로 쓰고 문단은 빈 줄로 나눈다.
- **`{@code}`, `{@link}` 남발 금지.** 꼭 필요한 식별자 강조가 아니면 그냥 평문으로 쓴다. 주렁주렁 달지 않는다.
- **한 문장은 짧게.** 여러 줄에 걸쳐 이어지는 run-on 한 문장 금지. 한 줄에 한 개념.
- **구현 세부는 본문에서 덜어낸다.** 매퍼 namespace, 내부 검증기 클래스명 등은 책임 설명에 불필요하면 생략한다.
- **메서드가 여러 개면 첫 문장으로 역할 차이가 구분되게.** (예: 첫 호출 vs 실패 후 재호출)

```java
// 좋음 — 첫 문장에 책임, 평문, 짧음
/**
 * 사용자 질문을 Agent A 에 보내 실행할 SELECT SQL 을 받아오는 포트.
 *
 * Application 계층이 외부 의존에 직접 닿지 않도록 격리한다.
 */

// 나쁨 — HTML 태그 주렁주렁, run-on, 책임이 안 보임
/**
 * Text-to-SQL Agent A 호출 포트.
 * <p>구현체는 Infrastructure 의 Adapter 이며 멀티턴 컨텍스트는 send 흐름은 최근 N건을,
 * retry 흐름은 직전 이력을 시간 오름차순으로 전달하고 {@code cn} 만 추출해...</p>
 */
```

### Javadoc 불필요 대상

- 구현 클래스의 Override 메서드 (인터페이스에 이미 있음)
- getter/setter, 자명한 메서드
- Request DTO — @Schema(Swagger)로 대체

### 구현 주석 규칙

- 코드가 "뭘 하는지"는 주석 불필요 — 코드 자체가 설명해야 함.
- **"왜 이렇게 하는지"**만 주석으로 남긴다 (비즈니스 규칙, 우회 사유, 제약 조건).

```java
// 좋음 — "왜"를 설명
// PG사 정산 주기가 월 1회라 취소는 30일 이내만 가능
if (order.getCreatedAt().isBefore(now().minusDays(30))) {
    throw new CancellationExpiredException();
}

// 나쁨 — 코드를 반복
// 30일 이전인지 확인한다
if (order.getCreatedAt().isBefore(now().minusDays(30))) {
```
