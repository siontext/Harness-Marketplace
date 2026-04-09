---
id: spring-boot-conventions
description: Spring Boot 코드를 작성하거나 리뷰할 때 사용 — DI, 어노테이션, 설정 관리, 예외 처리 규칙 적용.
section: "프레임워크"
order: 1
---

# Spring Boot Conventions

레이어 구조, 패키지 배치, 의존 방향 규칙은 `layered-architecture` 스킬을 참조. 이 스킬은 Spring Boot 고유 규칙만 다룬다.

## DI (의존성 주입)

- 생성자 주입 필수. `@Autowired` 필드 주입 금지.
- 생성자가 하나면 `@Autowired` 생략 가능 (Spring 4.3+).
- Lombok `@RequiredArgsConstructor` + `private final` 필드 조합 권장.
- Service는 Port(인터페이스)에 의존. 구체적인 Adapter에 직접 의존 금지.

```java
@Service
@RequiredArgsConstructor
public class CreateOrderService implements CreateOrderUseCase {
    private final OrderPort orderPort;       // Outbound Port에 의존
    private final PaymentPort paymentPort;   // 구현체가 아닌 Port에 의존
}
```

## 어노테이션 사용

| 레이어 | 어노테이션 |
|--------|-----------|
| Presentation | `@RestController`, `@RequestMapping` |
| Application | `@Service`, `@Transactional` |
| Domain | Spring 어노테이션 금지 (순수 Java) |
| Infrastructure | `@Repository`, `@Component`, `@Configuration` |

- `@Transactional`: Application 레이어에서만 사용. 읽기 전용은 `@Transactional(readOnly = true)`.
- `@Valid`: Presentation 레이어의 Controller 파라미터 검증에 사용.
- Domain 레이어에 `@Entity`, `@Autowired`, `@Service` 등 Spring 어노테이션 금지.

## 설정 관리

- `application.yml` 사용 (properties 대신).
- 환경별 프로파일 분리: `application-dev.yml`, `application-prod.yml`.
- 커스텀 설정은 `@ConfigurationProperties`로 타입 안전하게 바인딩.
- 비밀 값(API key, DB password)은 설정 파일에 직접 넣지 않고 환경변수 또는 시크릿 매니저 사용.

## 예외 처리

- `@RestControllerAdvice` + `@ExceptionHandler`로 글로벌 처리.
- 커스텀 예외 계층 구성:

```java
public abstract class BusinessException extends RuntimeException {
    private final ErrorCode errorCode;

    protected BusinessException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.errorCode = errorCode;
    }
}

public class OrderNotFoundException extends BusinessException {
    public OrderNotFoundException(Long id) {
        super(ErrorCode.ORDER_NOT_FOUND);
    }
}
```

- ErrorCode는 enum으로 관리. HTTP 상태 코드와 메시지 매핑.

## DTO

- 요청/응답 DTO 분리. 도메인 모델을 직접 반환하지 않는다.
- DTO는 레이어마다 분리. Presentation DTO와 Application DTO를 공유하지 않는다.
- `record` 사용 권장 (Java 16+).

```java
// Presentation DTO
public record OrderCreateRequest(
    @NotBlank String productName,
    @Positive int quantity
) {}

// Application DTO
public record OrderResponse(
    Long id,
    String productName,
    int quantity,
    String status
) {}
```

## 도메인 모델 ↔ JPA Entity 변환

- 도메인 모델은 순수 Java 객체. JPA Entity는 Infrastructure에 위치.
- `from()`/`toDomain()`으로 변환.

```java
// Infrastructure - JPA Entity
@Entity
@Table(name = "orders")
public class OrderEntity {
    @Id @GeneratedValue
    private Long id;
    private String productName;

    public static OrderEntity from(Order order) {
        // 도메인 모델 → JPA Entity
    }

    public Order toDomain() {
        // JPA Entity → 도메인 모델
    }
}
```
