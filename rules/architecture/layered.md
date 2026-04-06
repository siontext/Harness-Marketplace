---
id: layered-architecture
description: 4-Layered + Hexagonal(Port/Adapter) 아키텍처 규칙. 레이어 간 의존 방향, 패키지 배치, Port/Adapter 구현 기준. 코드 구현 및 리뷰 시 참조.
section: "아키텍처"
order: 1
---

# Layered + Hexagonal Architecture Guide

## 4-Layered Architecture

```
Presentation → Application → Domain ← Infrastructure
```

### 레이어 책임

| 레이어 | 책임 | 포함 요소 |
|--------|------|----------|
| **Presentation** | HTTP 요청/응답, 입력 검증, DTO 변환 | Controller, DTO, Validator |
| **Application** | 유스케이스 오케스트레이션, 트랜잭션 경계 | Service(UseCase), Command/Query |
| **Domain** | 핵심 비즈니스 로직, 규칙, 상태 | 도메인 모델, Value Object, Domain Service, Port(port/in, port/out) |
| **Infrastructure** | 외부 시스템 연동, 기술 구현 | Port Adapter 구현, API Client, Config |

### 의존 방향 규칙

- **Presentation → Application**: 허용. Controller가 Service를 호출.
- **Application → Domain**: 허용. Service가 도메인 모델과 Port를 사용.
- **Infrastructure → Domain**: 허용. Adapter가 Port를 구현.
- **Domain → 다른 레이어**: 금지. Domain은 어떤 레이어에도 의존하지 않는다.
- **Presentation → Domain 직접 접근**: 금지. 반드시 Application을 거친다.
- **Presentation → Infrastructure**: 금지.
- **Application → Infrastructure**: 금지. Port를 통해서만 접근.

## Hexagonal (Port & Adapter)

### Port (Domain 레이어에 위치)

Port는 **인터페이스**다. Domain이 외부에 의존하지 않기 위해 정의한다.

- **Inbound Port**: Application 레이어가 Domain에 진입하는 인터페이스.
  - 예: `CreateOrderUseCase`, `FindOrderQuery`
- **Outbound Port**: Domain이 외부 시스템에 요청하는 인터페이스.
  - 예: `OrderPort`, `PaymentPort`, `NotificationPort`

```java
// Domain 레이어 - Outbound Port
public interface OrderPort {
    Order save(Order order);
    Optional<Order> findById(Long id);
}

// Domain 레이어 - Inbound Port
public interface CreateOrderUseCase {
    OrderResponse execute(CreateOrderCommand command);
}
```

### Adapter (Infrastructure 레이어에 위치)

Adapter는 Port의 **구현체**다.

- **Inbound Adapter**: 외부 요청을 받아 Inbound Port를 호출.
  - 예: Controller, Message Listener, Scheduler
- **Outbound Adapter**: Outbound Port를 구현하여 외부 시스템에 접근.
  - 예: Port Adapter (JPA), REST Client, Kafka Producer

```java
// Infrastructure 레이어 - Outbound Adapter
@Repository
@RequiredArgsConstructor
public class OrderPortAdapter implements OrderPort {
    private final OrderJpaRepository jpaRepository;

    @Override
    public Order save(Order order) {
        OrderEntity entity = OrderEntity.from(order);
        return jpaRepository.save(entity).toDomain();
    }
}
```

## 패키지 구조

```
com.example.project
├── domain/
│   ├── order/
│   │   ├── Order.java                    # 도메인 모델
│   │   ├── OrderStatus.java              # Value Object / Enum
│   │   ├── OrderDomainService.java       # Domain Service (선택)
│   │   └── port/
│   │       ├── in/
│   │       │   └── CreateOrderUseCase.java   # Inbound Port (interface)
│   │       └── out/
│   │           └── OrderPort.java            # Outbound Port (interface)
│   └── payment/
│       └── ...
├── application/
│   ├── order/
│   │   ├── CreateOrderService.java       # Inbound Port 구현 (UseCase)
│   │   ├── CreateOrderCommand.java       # Command
│   │   └── OrderResponse.java            # Application DTO
│   └── ...
├── presentation/
│   ├── order/
│   │   ├── OrderController.java          # Inbound Adapter
│   │   ├── OrderCreateRequest.java       # Request DTO
│   │   └── OrderApiResponse.java         # Response DTO
│   └── ...
├── infrastructure/
│   ├── order/
│   │   ├── OrderPortAdapter.java         # Outbound Adapter
│   │   ├── OrderJpaRepository.java       # Spring Data JPA
│   │   └── OrderEntity.java              # JPA Entity (DB 매핑)
│   └── config/
│       └── JpaConfig.java
```

## 핵심 규칙 요약

1. **도메인 모델 ≠ JPA Entity**. 도메인 모델은 순수 Java 객체. JPA Entity는 Infrastructure에 위치하며 `from()`/`toDomain()`으로 변환.
2. **Port 네이밍**: Outbound Port는 도메인명 + `Port` (예: `OrderPort`, `PaymentPort`). Inbound Port는 유스케이스명 (예: `CreateOrderUseCase`).
3. **Adapter 네이밍**: Port명 + `Adapter` (예: `OrderPortAdapter`, `PaymentPortAdapter`).
4. **DTO는 레이어마다 분리**. Presentation DTO와 Application DTO를 공유하지 않는다.
5. **Domain 레이어에 Spring 어노테이션 금지**. `@Entity`, `@Autowired` 등은 Infrastructure에서만.
