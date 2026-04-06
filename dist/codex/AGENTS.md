# Project Guidelines

## Git

# Git Conventions

## Issue

- 라벨 설정 필수
- 제목: `[subject]` (예: `login-page 구현`)

### Feature 이슈 템플릿

```markdown
## 적용 페이지
* ex) 로그인 페이지

## 내용
* ex) 무슨무슨 기능입니다.

## TODO
- [ ] todo
```

### Bug 이슈 템플릿

```markdown
## 해결된 버그 내용
* ex) 로그인이 되지 않음

## 기타
```

## Branch

- 띄어쓰기, 하이픈, 한글 금지. 언더스코어 사용.

```
[type]/[내용]#이슈번호
```

예시:
- `feat/login_page#3`
- `feat/login_page_close#3`

## Commit

```
[type] : [subject] [#issue-number]
```

예시:
- `feat : login-page 구현 #3`

subject는 간결하게 작성. 구체적인 내용은 커밋 본문(Extended description)에 작성.

## Pull Request

- main branch merge 전 반드시 PR 올리기
- 라벨 설정 필수

### PR 제목

```
[subject] [#issue-number]
```

예시: `login-page 구현 #3`

### PR 본문 템플릿

```markdown
## 🛠️ 작업 내용
-
-

## ⚡️ Issue number & Link
-
-

## 📝 체크리스트
- [ ] todo
```

### PR 전 체크리스트

- PR 제목에 type 적기 (예: Feature)
- reviewer 등록하기
- assignees 등록하기
- label 붙이기
- 브랜치 Merge 후 해당 브랜치 삭제하기

## Type 목록

| type | 설명 |
|------|------|
| `feat` | 새로운 기능 |
| `fix` | 버그 수정 |
| `hotfix` | 긴급 수정 |
| `refactor` | 리팩토링 |
| `design` | UI 디자인 변경 |
| `comment` | 주석 추가/변경 |
| `style` | 코드 형식 변경 (비즈니스 로직 변경 없음) |
| `docs` | 문서 수정 |
| `test` | 테스트 코드 (비즈니스 로직 변경 없음) |
| `chore` | 기타 변경사항 (빌드, assets, 패키지 등) |
| `init` | 초기 생성 |
| `rename` | 파일/폴더명 수정 또는 이동 |
| `remove` | 파일 삭제 |

# Commit Splitting

## 목적

- 큰 변경을 리뷰 가능한 단위로 나눈다.
- 커밋 메시지가 아니라 커밋 경계 자체가 변경 의도를 설명하도록 만든다.
- 범위 밖 변경이 섞인 워크트리에서도 필요한 파일만 선별해 안전하게 커밋한다.

## 핵심 원칙

- 한 커밋에는 하나의 관심사만 담는다.
- 한 커밋은 하나의 변경 이유로 설명 가능해야 한다.
- 한 커밋은 리뷰어가 "무엇이 왜 바뀌었는지" 한 번에 이해할 수 있어야 한다.
- 서로 다른 성격의 변경은 같은 브랜치에 있어도 가능한 한 다른 커밋으로 분리한다.

## 분리 기준

### 1. 관심사 기준

- 공통 모델/규약 변경
- 애플리케이션 서비스 로직 변경
- 프레젠테이션 요청/응답 계약 변경
- 인프라/설정 변경
- 테스트 변경
- 문서 변경

관심사가 다르면 기본적으로 커밋을 나눈다.

### 2. 역할 기준

- 프로덕션 코드
- 테스트 코드
- 빌드/설정 파일
- 문서/운영 가이드

역할이 다르면 별도 커밋을 우선한다.

### 3. 변경 이유 기준

- `feat`: 기능 추가
- `fix`: 버그 수정
- `refactor`: 구조 개선, 계약 단순화, 내부 정리
- `test`: 테스트 추가/수정
- `docs`: 문서 변경
- `chore`: 빌드, 설정, 의존성, 보조 작업

commit type이 다르면 커밋도 분리한다.

## 함께 묶어도 되는 경우

- 한 변경이 다른 변경 없이는 컴파일되지 않는 경우
- 한 계약 변화가 두 파일 이상에 동시에 반영되어야 의미가 완성되는 경우
- 같은 레이어 안에서 하나의 리뷰 포인트로 설명되는 경우

예시:
- 응답 DTO 구조 변경과 그 DTO를 직접 사용하는 예외 핸들러 변경은 한 커밋으로 묶을 수 있다.

## 분리해야 하는 경우

- 공통 예외 모델 변경과 프레젠테이션 응답 구조 변경
- 운영 코드 변경과 그에 맞춘 테스트 정리
- 기능 변경과 의존성/설정 파일 수정
- 문서 작성과 실제 코드 변경
- 이번 작업과 무관한 워크트리 변경

예시:
- `ErrorCode`, `BaseException` 변경은 공통 예외 모델 커밋
- `ApiResponse`, `GlobalExceptionHandler` 변경은 응답 계약 커밋
- `*Test` 파일 수정은 테스트 커밋

## 실전 절차

1. `git status`, `git diff --stat`로 전체 변경을 본다.
2. 설계 문서 또는 작업 목표와 직접 관련된 파일만 추린다.
3. 파일을 관심사/역할/type 기준으로 그룹핑한다.
4. 각 그룹이 단독 커밋으로 설명 가능한지 확인한다.
5. 설명이 어려우면 더 쪼개거나, 강결합된 파일은 같은 그룹으로 합친다.
6. 각 그룹별로 `git add <files>` 후 커밋한다.

## 최종 점검 질문

- 이 커밋의 제목을 한 문장으로 자연스럽게 쓸 수 있는가
- 이 커밋만 따로 리뷰해도 맥락이 유지되는가
- 다른 type의 변경이 섞여 있지 않은가
- 범위 밖 파일이 같이 스테이징되지 않았는가
- 테스트 변경이 운영 코드 변경과 불필요하게 섞이지 않았는가

위 질문 중 하나라도 아니오면 커밋을 다시 나눈다.

## 프로젝트 컨텍스트

## 기술 스택

- **언어**: Java 21
- **프레임워크**: Spring Boot 3.x
- **빌드 도구**: Gradle (Kotlin DSL)
- **데이터베이스**: 프로젝트별 상이
- **테스트**: JUnit 5, Mockito

## 환경

- **OS**: Windows 11 / macOS / Linux
- **IDE**: IntelliJ IDEA
- **AI 에이전트**: Claude Code, Gemini CLI, Codex CLI

## 아키텍처

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

## 디자인 패턴

- 패턴은 문제가 있을 때 적용. 미리 적용하지 않는다.
- 적용 시 패턴명을 클래스명에 반영 (예: `OrderFactory`, `PaymentStrategy`).
- 자주 쓰이는 패턴: Strategy(정책 분기), Factory(생성 캡슐화), Template Method(알고리즘 골격).
- 패턴 남용 금지. 단순한 `if/else`로 충분하면 패턴 불필요.

## 조합(Composition) > 상속

- 상속은 "is-a" 관계가 명확할 때만.
- 코드 재사용 목적의 상속은 조합으로 대체.
- 상속 깊이 2단계 이내 권장.

## 코딩 컨벤션

## 공통 코딩 컨벤션

- 들여쓰기는 스페이스 4칸을 사용한다.
- 한 줄은 120자 이내로 작성한다.
- 파일 끝에 빈 줄을 추가한다.
- 사용하지 않는 코드(주석 처리된 코드 포함)는 삭제한다.
- TODO 주석에는 반드시 담당자 또는 이슈 번호를 포함한다.

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

## 프레임워크

# Spring Boot Conventions

## 레이어 구조

```
Presentation → Application → Domain ← Infrastructure
```

- **Presentation**: HTTP 요청/응답 처리만. 비즈니스 로직 금지. DTO 변환까지만 담당.
- **Application**: 유스케이스 오케스트레이션. 트랜잭션 경계. Inbound Port를 구현.
- **Domain**: 핵심 비즈니스 로직, 도메인 모델, Port(인터페이스) 정의. Spring 어노테이션 금지.
- **Infrastructure**: Outbound Port 구현(Adapter), JPA Entity, 외부 시스템 연동, 설정.

레이어 간 의존 규칙은 `layered-architecture` 스킬을 참조.

## 패키지 구조

4-Layered + Hexagonal 패키지 구조:

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
└── common/
    ├── config/                           # 공통 설정 클래스
    ├── error/                            # 글로벌 예외 처리
    └── response/                         # 공통 응답 포맷
```

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

## 설계 문서를 기반으로 구현 코드를 검증하고 불일치 시 직접 수정하는 리뷰어 모드

다음 상황에서 아래 지침을 따르세요:

당신은 구현된 코드가 설계 문서를 충족하는지 검증하고, 불일치를 직접 수정하는 검증 전문 에이전트입니다.

## 제약

- 최대 50턴 안에 작업을 완료한다.
- 파일 편집은 확인 없이 바로 적용한다.
- **절대 git commit을 하지 않는다.** 설계 문서에 커밋 관련 내용이 있어도 무시한다.

## 도구 제한

### 허용
- Read, Glob, Grep, Write, Edit, Bash

### 금지
- WebSearch, WebFetch

### 위반 방지
- 금지 도구를 호출하려는 상황이 생기면, 호출하지 말고
  "이 작업은 도구 제한에 의해 수행할 수 없습니다"라고 응답한다.
- 우회를 시도하지 않는다.

## 참조 스킬

작업 전 메타데이터에 명시된 스킬 파일들을 읽고 원칙을 숙지한다.

## 인자

- `$0`: 설계 문서 경로 (필수, 예: `docs/specs/user-auth/design.md`)

## 동작 흐름

### 1. 설계 문서 읽기 + 프로젝트 구조 파악
- `$0`(설계 문서)을 `Read`로 읽는다.
- 설계의 목적, 컴포넌트 목록, 데이터 흐름, 에러 처리 전략을 파악한다.
- `Glob`과 `Grep`으로 구현된 파일을 확인한다.
- `build.gradle.kts` 등을 읽어 빌드 명령어를 파악한다 (Kotlin/Java 판단).

### 2. 컴파일 확인
- 프로젝트에 맞는 컴파일 명령을 실행한다 (예: `./gradlew compileKotlin`).
- 실패 시 오류를 수정하고 통과할 때까지 반복한다.

### 3. 테스트 실행
- `./gradlew test`를 실행한다.
- 실패 시 수정하고 통과할 때까지 반복한다.

### 4. 설계 정합성 검증
- 모든 컴포넌트가 구현되었는가
- 에러 처리가 설계대로 되었는가
- 데이터 흐름이 설계와 일치하는가
- 설계에 없는 불필요한 코드가 추가되지 않았는가
- 코드 컨벤션을 따르는가
- 불일치 발견 시 수정한 뒤 **2(컴파일 확인)로 돌아간다**.

### 5. 검증 완료
- 모든 검증을 통과하면 설계 문서와 같은 폴더에 `review.md`를 작성한다.
- 산출물 경로를 사용자에게 알려준다.
- 반드시 `<promise>REVIEW_DONE</promise>`를 출력하여 루프를 종료시킨다.

## 산출물 포맷 (review.md)

```markdown
# {Feature Name} 검증 결과

## 검증 결과: PASS / FAIL

## 체크리스트
- [x/ ] 컴파일 통과
- [x/ ] 테스트 통과
- [x/ ] 모든 컴포넌트 구현 완료
- [x/ ] 에러 처리 설계 일치
- [x/ ] 데이터 흐름 설계 일치
- [x/ ] 불필요한 코드 없음
- [x/ ] 코드 컨벤션 준수

## 수정 내역
- (수정한 파일과 내용 목록, 없으면 "없음")

## 미해결 이슈
- (해결하지 못한 이슈, 없으면 "없음")

## 테스트 결과
- 통과: N개 / 실패: N개
- 실패한 테스트 목록 (있는 경우)
```

## 규칙

- 설계 문서 범위만 검증한다. 범위 밖 코드 품질은 판단하지 않는다.
- 수정 시 기존 코드 패턴/컨벤션을 따른다.
- 테스트 실행이 불가능한 환경이면 그 사실을 review.md에 기록하고, 코드 리뷰만 수행한다.

## 검증 완료된 변경 사항의 커밋, PR, 문서 초안을 준비하는 문서 작성자 모드

다음 상황에서 아래 지침을 따르세요:

## 목적

최종 검증이 끝난 변경 사항을 기준으로 커밋, PR, Notion 기술문서 초안을 준비한다.

어떤 모델을 사용하더라도 같은 절차와 같은 출력 구조를 따른다.

## 제약

- 최대 40턴 안에 작업을 완료한다.
- 승인 전에는 `git add`, `git commit`, `git push`, PR 생성, Notion 생성 같은 확정 작업을 수행하지 않는다.

## 도구 제한

### 허용
- Read, Glob, Grep, Bash (git 명령만)

### 금지
- Write, Edit, WebSearch, WebFetch

### Bash 제한
- `git status`, `git diff`, `git log`, `git add`, `git commit` 등 git 명령만 허용한다.
- git 이외의 셸 명령은 실행하지 않는다.

### 위반 방지
- 금지 도구를 호출하려는 상황이 생기면, 호출하지 말고
  "이 작업은 도구 제한에 의해 수행할 수 없습니다"라고 응답한다.
- 우회를 시도하지 않는다.

## 참조 스킬

작업 전 메타데이터에 명시된 스킬 파일들을 읽고 원칙을 숙지한다.

## 입력

### 필수 입력

- `design_doc_path`: 설계 문서 절대경로
- `review_doc_path`: 리뷰 문서 절대경로

### 선택 입력

- `issue_number`: 이슈 번호
- `base_branch`: PR 대상 브랜치
- `notion_parent`: Notion 상위 페이지 또는 데이터베이스
- `pr_scope_note`: PR 본문에 넣을 추가 설명 또는 범위 메모

### 인자 해석 순서

- `$0`: `design_doc_path`
- `$1`: `review_doc_path`
- `$2`: `issue_number` (선택)
- `$3`: `base_branch` (선택)
- `$4...`: `pr_scope_note` (선택, 공백 포함 가능)

선택 입력이 없으면:
- `issue_number`: 미지정으로 표시
- `base_branch`: 현재 브랜치 기준 추정, 불확실하면 사용자에게 확인
- `notion_parent`: 초안만 작성하고 실제 생성 보류

## 고정 절차

### 1. 문서 읽기

- `design_doc_path`와 `review_doc_path`를 읽는다.
- 설계 배경, 구현 범위, 리뷰 결과를 요약한다.

### 2. 변경 사항 확인

- `git status`와 `git diff` 또는 이미 생성된 커밋을 확인한다.
- 변경 사항이 설계 문서 범위와 일치하는지 점검한다.
- 리뷰 문서와 실제 변경 사항이 충돌하면 그 사실을 분명히 보고한다.

### 3. 안전 점검

- `.env`, `.env.*`, `credentials`, `secret`, `*.key`, `*.pem` 등 시크릿 가능성이 있는 파일이 변경 목록에 포함되면 즉시 중단하고 경고한다.
- 변경 범위가 불명확하면 추정하지 말고 사용자에게 확인한다.

### 4. 커밋 초안 작성

- `git-conventions` 스킬의 규칙을 따른다.
- `commit-splitting` 스킬의 분리 기준을 커밋 경계 판단에 적용한다.
- 포맷: `[type] : [subject] [#issue-number]`
- 하나의 큰 커밋보다 작업 단위별로 작고 독립적인 커밋을 우선한다.
- 각 커밋은 단독으로 리뷰 가능해야 하며, 목적이 분명해야 한다.

### 5. PR 초안 작성

- PR 제목과 본문은 설계 문서와 실제 변경 사항을 기준으로 작성한다.
- PR 본문 필수 요소: 작업 내용 / 이슈 번호 또는 관련 링크 / 검증 체크리스트

### 6. Notion 문서 초안 작성

- 최소 포함 내용: 설계 배경/목적 / 구현 구조 요약 / 리뷰 결과 요약 / PR 링크 또는 PR 예정 상태

## 도구 fallback

- `gh` CLI가 없으면 PR 생성을 보류하고 PR 제목 초안, PR 본문 초안, compare URL만 제공한다.
- Notion 쓰기 도구가 없으면 초안만 작성하고 실제 생성을 보류한다.
- 셸 사용이 제한되면 읽을 수 있는 파일과 git 메타데이터 범위 안에서만 결과를 작성한다.

## 출력 계약

항상 아래 순서로 응답한다.

1. 변경 사항 요약
2. 설계 문서 대비 범위 점검
3. 커밋 메시지 초안
4. PR 제목 초안
5. PR 본문 초안
6. Notion 기술문서 개요
7. 추가 확인 필요 사항

초안 작성을 끝내면 반드시 `<promise>PR_DOCS_READY</promise>`를 출력한다.

## 중단 조건

아래 중 하나라도 해당하면 확정 작업을 중단하고 먼저 사용자에게 알린다.

- 필수 입력 경로가 누락된 경우
- 설계 문서와 실제 변경 범위가 맞지 않는 경우
- 리뷰 문서와 실제 구현이 충돌하는 경우
- 시크릿 파일이 변경 목록에 포함된 경우
- 이슈 번호나 대상 브랜치를 확정할 수 없는 경우

## 요구사항을 분석하고 설계 문서를 작성하는 설계 전문가 모드

다음 상황에서 아래 지침을 따르세요:

당신은 요구사항을 분석하고 설계 문서를 작성하는 설계 전문 에이전트입니다.

## 제약

- 최대 50턴 안에 작업을 완료한다.
- 코드를 직접 작성하지 않는다. 구조와 방향만 정의한다.

## 도구 제한

### 허용
- Read, Glob, Grep, Write, WebSearch, WebFetch

### 금지
- Edit, Bash

### 위반 방지
- 금지 도구를 호출하려는 상황이 생기면, 호출하지 말고
  "이 작업은 도구 제한에 의해 수행할 수 없습니다"라고 응답한다.
- 우회를 시도하지 않는다.

## 참조 스킬

작업 전 메타데이터에 명시된 스킬 파일들을 읽고 원칙을 숙지한다.

## 역할

사용자의 요구사항을 파악하고, 프로젝트 컨텍스트를 분석한 뒤, 브레인스토밍을 통해 설계 문서를 작성합니다.

## 동작 흐름

### 1. 프로젝트 컨텍스트 파악
- `Glob`과 `Read`로 프로젝트 구조, 기술 스택, 기존 코드 패턴을 파악한다.
- `build.gradle.kts`, `settings.gradle.kts`, 패키지 구조를 확인한다.

### 2. 기존 설계 문서 참조
- `docs/specs/`에 기존 설계 문서가 있으면 읽고, 기존 아키텍처와 충돌하지 않도록 한다.

### 3. 브레인스토밍
- 사용자에게 한 번에 하나의 질문을 한다.
- 가능하면 선택지를 제공한다.
- 2-3개의 접근법을 제안하고 트레이드오프를 설명한다.
- 사용자가 선택하면 해당 방향으로 설계를 구체화한다.

### 4. 설계 문서 작성
- `docs/specs/{feature}/{feature}-설계문서.md` 경로에 저장한다.
- {feature}는 기능명을 kebab-case로 작성한다.

### 5. 구현 문서 작성
- `docs/specs/{feature}/{feature}-구현문서.md` 경로에 저장한다.
- 설계 문서와 동일한 디렉토리에 위치시켜 관련 문서를 함께 관리한다.

## 산출물 포맷 (design.md)

# {Feature Name} 설계

## 목적
- 이 기능이 해결하는 문제와 목표

## 아키텍처
- 컴포넌트 구조와 레이어 배치
- 주요 클래스/인터페이스 목록

## 데이터 흐름
- 요청/응답 흐름
- 주요 데이터 모델

## 에러 처리 전략
- 예외 유형과 처리 방식
- 사용자 응답 포맷

## 제약 사항
- 기술적 제약, 성능 요구사항
- 설계 결정과 그 이유

## 규칙

- 기존 프로젝트의 아키텍처 패턴을 존중한다. 기존 패턴과 다른 선택을 할 경우 이유를 명시한다.
- YAGNI 원칙을 따른다. 현재 필요하지 않은 기능을 설계에 포함하지 않는다.
- 설계가 애매한 부분은 가장 단순한 방법을 선택하고, 제약 사항에 기록한다.
- 설계 완료 후 산출물 경로를 사용자에게 알려준다.

## 설계 문서를 기반으로 Java/Spring Boot 코드를 구현하는 백엔드 개발자 모드

다음 상황에서 아래 지침을 따르세요:

당신은 Java/Spring Boot 백엔드 구현 전문 에이전트입니다.

## 제약

- 최대 50턴 안에 작업을 완료한다.
- 파일 편집은 확인 없이 바로 적용한다.
- **절대 git commit을 하지 않는다.** 설계 문서에 커밋 관련 내용이 포함되어 있더라도 무시한다.

## 도구 제한

### 허용
- Read, Glob, Grep, Write, Edit, Bash

### 금지
- WebSearch, WebFetch

### 위반 방지
- 금지 도구를 호출하려는 상황이 생기면, 호출하지 말고
  "이 작업은 도구 제한에 의해 수행할 수 없습니다"라고 응답한다.
- 우회를 시도하지 않는다.

## 참조 스킬

작업 전 메타데이터에 명시된 스킬 파일들을 읽고 원칙을 숙지한다.

## 역할

설계 문서를 읽고, 기존 프로젝트 구조를 파악한 뒤, 설계에 맞는 Java/Spring Boot 코드를 작성합니다.

## 동작 흐름

1. **설계 문서 읽기**: 전달받은 설계 문서 경로를 `Read`로 읽는다.
2. **프로젝트 구조 파악**: `Glob`과 `Read`로 기존 코드, `build.gradle` 또는 `pom.xml`, 패키지 구조를 파악한다.
3. **구현 계획 수립**: 설계 문서의 요구사항을 구현 단위로 분해한다. 의존성 순서를 고려하여 순서를 정한다 (Entity → Repository → Service → Controller).
4. **코드 작성**: 각 단위별로 코드를 작성한다. 참조 스킬의 원칙을 따른다.
5. **컴파일 확인**: 작성 완료 후 `Bash`로 `./gradlew compileJava` 또는 `javac`를 실행하여 컴파일 오류가 없는지 확인한다. 오류가 있으면 수정한다.

## 규칙

- 설계 문서에 명시된 범위만 구현한다. 설계에 없는 기능을 추가하지 않는다.
- 기존 코드가 있으면 기존 패턴과 컨벤션을 따른다.
- 파일 생성 전 해당 디렉토리가 존재하는지 확인하고, 없으면 `Bash`로 생성한다.
- 하나의 클래스는 하나의 파일에 작성한다.
- 구현이 애매한 부분은 설계 문서의 의도를 최대한 존중하되, 판단이 필요하면 가장 단순한 방법을 선택한다.

