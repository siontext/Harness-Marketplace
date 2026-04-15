---
name: oop-principles
description: 객체지향 설계 원칙 — SOLID, 캡슐화, 다형성, 디자인패턴 적용 가이드. 코드 설계 및 리뷰 시 참조.
---

# 객체지향 설계 원칙

## SOLID

### SRP (Single Responsibility Principle)
- 클래스는 변경의 이유가 하나만 있어야 한다.
- "이 클래스는 무엇을 하는가?"에 한 문장으로 답할 수 없으면 분리.
- Service 클래스가 비즈니스 로직 + 이메일 발송을 함께 하면 위반.

### OCP (Open/Closed Principle)
- 확장에는 열려 있고, 수정에는 닫혀 있어야 한다.
- 새로운 동작 추가 시 기존 코드를 수정하지 않고 인터페이스 구현체를 추가.
- `if/else` 또는 `switch`로 타입 분기하는 코드는 다형성으로 대체 검토.

### LSP (Liskov Substitution Principle)
- 하위 타입은 상위 타입을 대체할 수 있어야 한다.
- 하위 클래스가 상위 클래스의 계약(사전조건, 사후조건)을 위반하면 안 된다.
- `UnsupportedOperationException`을 던지는 메서드가 있으면 LSP 위반 의심.

### ISP (Interface Segregation Principle)
- 클라이언트가 사용하지 않는 메서드에 의존하면 안 된다.
- 인터페이스가 5개 이상의 메서드를 가지면 분리 검토.
- 역할별로 인터페이스를 나누고, 필요한 것만 구현.

### DIP (Dependency Inversion Principle)
- 상위 모듈이 하위 모듈에 직접 의존하지 않는다. 둘 다 추상화에 의존.
- `new`로 직접 생성하지 말고 생성자 주입 사용.
- Service가 구체적인 Adapter 구현체가 아닌 Port(인터페이스)에 의존.

## 캡슐화

- 모든 필드는 `private`. getter/setter는 필요한 것만 노출.
- 불변 객체 선호: `final` 필드 + 생성자 초기화.
- 컬렉션 반환 시 `Collections.unmodifiableList()` 또는 복사본 반환.
- 내부 상태 변경은 의미 있는 메서드명으로 (예: `activate()` not `setActive(true)`).

## 다형성

- 인터페이스 추출 기준: 구현체가 2개 이상이거나, 테스트에서 모킹이 필요할 때.
- 추상 클래스 vs 인터페이스: 공통 상태/로직이 있으면 추상 클래스, 순수 계약이면 인터페이스.
- `instanceof` 체크가 반복되면 다형성으로 대체.

## 객체 생성 — 정적 팩토리 메서드

- 객체는 자기 자신을 생성할 책임을 가진다. 생성자를 `private`으로 닫고 정적 팩토리 메서드로 생성한다.
- 팩토리 메서드는 **생성 의도를 이름으로 표현**한다 (예: `create()`, `restore()`, `of()`).
- 유효성 검증을 팩토리 메서드 안에서 수행하여, 객체가 존재하는 순간 유효함을 보장한다.
- DB 복원용 `restore()` 팩토리 메서드를 반드시 함께 정의한다 (Infrastructure → Domain 변환에 필요).
- Command, Result 등 값 객체도 동일하게 `private constructor` + `companion object of()` 패턴을 적용한다.

## 디자인 패턴

- 패턴은 문제가 있을 때 적용. 미리 적용하지 않는다.
- 적용 시 패턴명을 클래스명에 반영 (예: `OrderFactory`, `PaymentStrategy`).
- 자주 쓰이는 패턴: Strategy(정책 분기), Factory(생성 캡슐화), Template Method(알고리즘 골격).
- 패턴 남용 금지. 단순한 `if/else`로 충분하면 패턴 불필요.

## 조합(Composition) > 상속

- 상속은 "is-a" 관계가 명확할 때만.
- 코드 재사용 목적의 상속은 조합으로 대체.
- 상속 깊이 2단계 이내 권장.
