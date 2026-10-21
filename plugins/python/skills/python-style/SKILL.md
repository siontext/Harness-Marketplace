---
name: python-style
description: Python 코드 스타일 가이드 — 이름 규칙(생성 함수 이름 포함), import, 함수, 타입 표시, 데이터 모델(pydantic·TypedDict·frozen dataclass), 예외, 비동기, 로그, 한국어 Google 독스트링(도구 함수는 LLM용 설명). Python 코드를 작성하거나 리뷰할 때 참조.
---

# Python Code Style Guide

Python 3.11 기준이다. 포맷과 import 정리는 Ruff가 맡는다 (`python-project`의 설정).

## 이름 규칙

- 함수·변수·모듈 파일: `snake_case` (예: `get_balance`, `order_service.py`)
- 클래스: `PascalCase` (예: `OrderService`, `LlmProvider`)
- 상수: `UPPER_SNAKE_CASE` (예: `MAX_RETRY_COUNT`)
- 모듈 밖에서 쓰지 않는 것: 앞에 `_` (예: `_parse_response`)
- 참/거짓 값·함수: `is_`, `has_`, `can_` 접두사 (예: `is_active`, `has_permission`)
- 함수 이름은 동사로 시작한다 (예: `create`, `find`, `update`, `delete`).

### 생성·변환 함수 이름

이름만 읽어도 "무엇으로부터 무엇을 만드는지" 알 수 있어야 한다.

| 뜻 | Java/Kotlin | Python | 예 |
|---|---|---|---|
| 값을 넣어서 만들기 | `Money.of(1000, "KRW")` | 생성자 그대로 | `Money(1000, "KRW")` |
| 다른 것**으로부터** 만들기 | `OrderResponse.from(order)` | `from_<원본>` `@classmethod` | `OrderResponse.from_order(order)` |
| 새로 만들기 / 되살리기 | `create()`, `restore()` | 같음 (`@classmethod`) | `Order.create(...)`, `Order.restore(...)` |
| 다른 것**으로** 바꾸기 | `order.toResponse()` | `to_<대상>` | `order.to_response()` |

- Python은 같은 이름의 함수를 여러 개 만들 수 없다(오버로딩 없음). 그래서 `from` 뒤에 원본 이름을 붙여 구분한다: `from_order`, `from_row`, `from_request`.
- `create()`·`restore()`는 **만드는 상황에 따라 채우는 값이 다를 때만** 만든다 (예: 새 주문은 id 없음·상태 "접수됨", 되살린 주문은 저장된 id·상태). 만드는 방법이 하나면 생성자를 바로 쓴다.
- pydantic 모델은 pydantic 이름을 쓴다: 딕셔너리로부터 `model_validate(...)`, 딕셔너리로 `model_dump()`.
- 명사만 쓴 이름(`OrderResponse.order`)은 "가지고 있는 값"으로 읽힌다. 만드는 함수에 쓰지 않는다.

## Import

- `*` import 금지. 쓰지 않는 import 제거.
- 순서: 표준 라이브러리 → 외부 패키지 → 내 프로젝트(`app`). 그룹 사이 빈 줄. Ruff(`I` 규칙)가 정리한다.
- 내 프로젝트는 절대 경로로 가져온다 (`from app.tools.product import get_product`). 상대 경로(`from ..tools`) 금지.

## 함수

- 한 함수 30줄 이내 권장. 넘으면 분리 검토.
- 인자 3개 이내 권장. 넘으면 데이터 모델로 묶는다.
- 하나의 함수는 하나의 책임만 수행.
- **기본값에 리스트·딕셔너리 같은 변하는 값 금지.** `def f(items: list[str] = [])` ✕ → `items: list[str] | None = None` 후 안에서 만든다.

## 타입 표시

- **모든 함수**의 인자와 반환값에 타입을 적는다. 반환이 없으면 `-> None`.
- 3.11 문법: `list[str]`, `dict[str, int]`, `str | None`. `List`, `Optional` 같은 `typing` 옛 이름 금지.
- `Any` 피하기. 모양이 정해진 딕셔너리는 TypedDict나 pydantic 모델로.
- 인터페이스는 `typing.Protocol`로 정한다 (`agent-architecture`).
- 타입 검사는 Pyrefly가 맡는다.

## 데이터 모델

용도에 따라 세 가지를 나눠 쓴다.

| 용도 | 쓰는 것 | 이유 |
|---|---|---|
| 바깥과 주고받는 데이터 (API 요청·응답, LLM 구조화 출력, 설정) | pydantic `BaseModel` | 들어올 때 형식을 검사한다 |
| LangGraph 상태 | `TypedDict` | LangGraph 공식 방식 |
| 내부 값 묶음 | `@dataclass(frozen=True)` | Java record와 같다. 값 비교·변경 불가 |

- 내부 값 묶음은 반드시 `frozen=True`. 안 붙이면 값을 바꿀 수 있는 일반 클래스가 된다.
- 만들 때 검증은 `__post_init__`에서 한다. 어떤 경로로 만들든 잘못된 객체가 생기지 않는다.

```python
@dataclass(frozen=True)
class Money:
    amount: int
    currency: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise InvalidMoneyError(f"금액은 0 이상이어야 한다: amount={self.amount}")
```

## 예외 처리

- 의미 있는 예외 클래스를 만든다 (예: `ProductNotFoundError`). 이름은 `Error`로 끝낸다.
- `except:`(아무것도 안 적음) 금지. `except Exception` 남용 금지. 구체적인 예외 타입을 잡는다.
- 예외를 바꿔 던질 때는 원인을 잇는다: `raise ProductLookupError(...) from e`.
- 예외 메시지에 맥락을 넣는다 (예: `f"상품을 찾을 수 없다: product_id={product_id}"`). 키·개인정보는 넣지 않는다.
- 도구 함수의 예외 처리는 `langgraph-conventions`를 따른다 (LLM이 읽을 문장으로 돌려준다).

## 비동기

- FastAPI 엔드포인트와 LangGraph 노드를 `async def`로 쓸 때, 그 안에서 오래 기다리는 동기 함수(`requests.get`, `time.sleep`, 동기 DB 드라이버)를 부르지 않는다.
- 동기 라이브러리밖에 없으면 `anyio.to_thread.run_sync(...)`로 감싼다.
- 비동기 함수는 `await` 없이 부르지 않는다.

## 로그

- `print` 금지. `logging.getLogger(__name__)`을 쓴다.
- **API 키, 개인정보, 프롬프트 전문은 로그에 남기지 않는다.** 질문·답이 필요하면 길이나 요청 id만 남긴다.
- 로그 메시지는 `%` 인자 방식: `logger.info("도구 호출: %s", tool_name)`. 로그에서는 f-string을 쓰지 않는다 (로그 수준이 꺼져 있어도 문자열이 만들어진다).

## 기타

- 매직 넘버 금지. 상수로 뺀다.
- 문자열 조립은 f-string (로그 제외).
- 파일 경로는 `pathlib.Path`. `os.path` 금지.
- 환경 변수는 `app/platform/`의 설정 모듈에서만 읽는다 (`agent-architecture`). 다른 곳에서 `os.environ` 금지.

## 독스트링과 주석

**독스트링과 주석은 모두 한국어로 쓴다.** 도구 설명도 한국어다 (평가 결과를 보고 바꿀 수 있다).

### 독스트링 대상

| 대상 | 수준 |
|---|---|
| 모듈 밖에서 쓰는 함수·클래스, API 엔드포인트 | Google 스타일로 자세히 (`Args:`, `Returns:`, `Raises:`) |
| 도구 함수 (`@tool`) | LLM이 읽는 설명서 — 아래 규칙 |
| Protocol 메서드 | 자세히 (구현이 지켜야 할 계약) |
| 그 밖의 내부 함수 | 한 줄 |
| 자명한 함수, Protocol 구현 메서드 | 생략 |

- **첫 문장에 책임을 적는다.** 첫 줄만 읽고 무엇을 하는지 알 수 있어야 한다.
- 한 문장은 짧게. 한 줄에 한 개념.

```python
def find_product(product_id: str) -> Product:
    """상품 id로 상품 정보를 조회한다.

    Args:
        product_id: 조회할 상품 id.

    Returns:
        조회한 상품.

    Raises:
        ProductNotFoundError: 상품이 없을 때.
    """
```

### 도구 함수 독스트링 — LLM용 설명서

LLM은 이 독스트링을 읽고 도구를 쓸지 정한다. 사람용 설명이 아니다.

- 첫 문장: 무엇을 하는 도구인지.
- **언제 쓰는지, 언제 쓰면 안 되는지**를 적는다.
- `Args:`에 각 인자의 뜻과 형식(예: "8자리 숫자")을 적는다.
- 반환 형식을 적는다.

```python
@tool
def get_product(product_id: str) -> str:
    """상품 id로 상품 이름, 가격, 재고를 조회한다.

    사용자가 특정 상품의 조건을 물을 때 쓴다.
    상품 id를 모르면 쓰지 말고 search_products로 먼저 찾는다.

    Args:
        product_id: 상품 id. 영문 대문자와 숫자 8자리.

    Returns:
        상품 정보 문장. 상품이 없으면 없다는 안내 문장.
    """
```

### 구현 주석

- 코드가 "무엇을 하는지"는 주석으로 쓰지 않는다. 코드가 설명해야 한다.
- **"왜 이렇게 하는지"만** 남긴다 (업무 규칙, 우회 사유, 제약 조건).
