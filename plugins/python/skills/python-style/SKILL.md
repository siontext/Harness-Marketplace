---
name: python-style
description: Python 코드 스타일 가이드 — 클래스가 기본(모듈 함수는 프레임워크가 요구하는 곳만), 이름 규칙(생성 메서드 이름 포함), import, 메서드, 타입 표시, 데이터 모델(pydantic·TypedDict·frozen dataclass), 예외, 비동기, 로그, 한국어 Google 독스트링(도구 메서드는 LLM용 설명). Python 코드를 작성하거나 리뷰할 때 참조.
---

# Python Code Style Guide

Python 3.11 기준이다. 포맷과 import 정리는 Ruff가 맡는다 (`python-project`의 설정).

## 클래스가 기본

**기능은 책임을 가진 클래스로 만든다. 모듈에 함수를 두는 것은 프레임워크가 함수를 요구하는 곳뿐이다.** Python은 절차지향(함수)과 객체지향(클래스)을 섞어 쓸 수 있어서, 기준이 없으면 같은 종류의 일을 어떤 곳은 함수로, 어떤 곳은 클래스로 짜게 된다. 이 하네스는 Java·Kotlin 하네스와 같이 클래스로 통일한다.

| 함수로 두는 곳 (예외) | 이유 |
|---|---|
| FastAPI 엔드포인트(`@router.get` 등), `main.py`의 `lifespan` | FastAPI가 함수를 받는다 |
| `tests/`의 테스트·픽스처, 가짜를 만드는 도우미(`fake_llm`, `fake_platform` 등) | pytest 방식이다 |

- 그 밖의 코드는 모두 클래스의 메서드다. 도우미도 그것을 쓰는 클래스의 비공개 메서드(`_` 접두사)로 둔다. `self`를 쓰지 않으면 `@staticmethod`로 둔다.
- 다른 것으로부터 만드는 일은 `from_<원본>` `@classmethod`로 둔다 (`Settings.from_env()`, `Platform.from_settings()`). 조립은 `Container` 클래스가 한다 (`agent-architecture`의 "조립").
- 도구는 `<기능>Tools` 클래스의 메서드, LangChain 미들웨어는 `AgentMiddleware`를 물려받은 클래스, `StateGraph` 노드는 어댑터의 메서드다 (`langgraph-conventions`). 함수에 붙이는 데코레이터(`@tool`, `@wrap_model_call`)로 만들지 않는다.
- 클래스가 의존하는 동작을 함수로 넘기지 않는다 (`now: Callable[[], datetime]` ✕). 포트(`Clock`)로 받는다. 서버가 꺼질 때 부를 닫기 메서드(`Platform.closers`에 넣는 `client.aclose`)와 프레임워크에 넘기는 메서드(`tool(self.get_product)`)만 값으로 넘긴다.
- **클래스가 쓰는 다른 객체는 생성자로 받는다.** 설정 값도 바꿔 끼울 구현도 없는 도우미(`SentenceSplitter`, `ErrorRuleBook`)만 생성자 안에서 만든다.
- 정적 메서드만 모은 클래스(`class Utils:`에 `@staticmethod`만)는 만들지 않는다. 이름만 클래스인 함수 묶음이다. 메서드는 인스턴스를 만들어 부른다.
- 모듈 수준에 둘 수 있는 것: 상수, `logger`, 프레임워크 객체(`app`, `router`), 모듈이 내놓는 인스턴스(`local.py`의 `factory`).

## 이름 규칙

- 메서드·함수·변수·모듈 파일: `snake_case` (예: `get_balance`, `order_tools.py`)
- 클래스: `PascalCase` (예: `OrderService`, `LlmProvider`)
- 상수: `UPPER_SNAKE_CASE` (예: `MAX_RETRY_COUNT`)
- 모듈 밖에서 쓰지 않는 것: 앞에 `_` (예: `_parse_response`)
- 참/거짓 값·메서드: `is_`, `has_`, `can_` 접두사 (예: `is_active`, `has_permission`)
- 메서드 이름은 동사로 시작한다 (예: `create`, `find`, `update`, `delete`).

### 생성·변환 메서드 이름

이름만 읽어도 "무엇으로부터 무엇을 만드는지" 알 수 있어야 한다.

| 뜻 | Java/Kotlin | Python | 예 |
|---|---|---|---|
| 값을 넣어서 만들기 | `Money.of(1000, "KRW")` | 생성자 그대로 | `Money(1000, "KRW")` |
| 다른 것**으로부터** 만들기 | `OrderResponse.from(order)` | `from_<원본>` `@classmethod` | `OrderResponse.from_order(order)` |
| 새로 만들기 / 되살리기 | `create()`, `restore()` | 같음 (`@classmethod`) | `Order.create(...)`, `Order.restore(...)` |
| 다른 것**으로** 바꾸기 | `order.toResponse()` | `to_<대상>` | `order.to_response()` |

- Python은 같은 이름의 메서드를 여러 개 만들 수 없다(오버로딩 없음). 그래서 `from` 뒤에 원본 이름을 붙여 구분한다: `from_order`, `from_row`, `from_request`.
- `create()`·`restore()`는 **만드는 상황에 따라 채우는 값이 다를 때만** 만든다 (예: 새 주문은 id 없음·상태 "접수됨", 되살린 주문은 저장된 id·상태). 만드는 방법이 하나면 생성자를 바로 쓴다.
- pydantic 모델은 pydantic 이름을 쓴다: 딕셔너리로부터 `model_validate(...)`, 딕셔너리로 `model_dump()`.
- 명사만 쓴 이름(`OrderResponse.order`)은 "가지고 있는 값"으로 읽힌다. 만드는 메서드에 쓰지 않는다.

## Import

- `*` import 금지. 쓰지 않는 import 제거.
- 순서: 표준 라이브러리 → 외부 패키지 → 내 프로젝트(`app`). 그룹 사이 빈 줄. Ruff(`I` 규칙)가 정리한다.
- 내 프로젝트는 절대 경로로 가져온다 (`from app.infrastructure.tools.product_tools import ProductTools`). 상대 경로(`from ..tools`) 금지.

## 메서드

- 한 메서드 30줄 이내 권장. 넘으면 분리 검토.
- 인자 3개 이내 권장(`self` 제외). 넘으면 데이터 모델로 묶는다.
- 하나의 메서드는 하나의 책임만 수행.
- **한 메서드 안의 문장은 같은 높이로 적는다 (추상화 수준 통일, SLAP).** 업무 단계(검사한다, 저장한다)와 기술 세부(`asyncio` 사용법, 정규식 반복, 재시도 반복)를 한 메서드에 섞지 않는다. 기술 세부는 이름 붙은 메서드나 도우미 클래스(`TimeLimit`)로 빼고 그 이름으로 부른다.
- **기본값에 리스트·딕셔너리 같은 변하는 값 금지.** `def f(items: list[str] = [])` ✕ → `items: list[str] | None = None` 후 안에서 만든다.

## 타입 표시

- **모든 메서드·함수**의 인자와 반환값에 타입을 적는다. 반환이 없으면 `-> None`.
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
- 예외 클래스를 두는 곳은 `agent-architecture`의 "예외 위치"를 따른다 (공통 예외는 `app/common/errors.py`).
- `except:`(아무것도 안 적음) 금지. 구체적인 예외 타입을 잡는다.
- `except Exception`은 아래 두 곳에서만 쓰고, 그 줄 위에 이유를 주석으로 적는다. 그 밖의 곳에서는 쓰지 않는다.
  - LLM 호출을 감싸 `UpstreamError`로 바꾸는 곳 (`langgraph-conventions`). LLM 구현마다 던지는 예외가 다르다.
  - `SseResponse`가 `error` 이벤트로 바꾸는 곳 (`fastapi-conventions`). 스트리밍이 시작된 뒤에는 전역 핸들러가 잡지 못해 여기가 마지막 경계다.
- 예외를 바꿔 던질 때는 원인을 잇는다: `raise ProductLookupError(...) from e`.
- 예외 메시지에 맥락을 넣는다 (예: `"상품을 찾을 수 없다: product_id=P001"`). 키·개인정보는 넣지 않는다.
- **업무 예외는 대상 값을 생성자로 받아 메시지를 스스로 만든다.** 던지는 쪽은 `raise ProductNotFoundError(product_id)`처럼 값만 넘긴다. 문구를 던지는 곳마다 적지 않는다 (`agent-architecture`의 "예외 위치").

```python
class ProductNotFoundError(AppError):
    """상품 번호에 해당하는 상품이 없을 때.

    Attributes:
        product_id: 찾지 못한 상품 번호.
    """

    def __init__(self, product_id: str) -> None:
        super().__init__(f"상품을 찾을 수 없다: product_id={product_id}")
        self.product_id = product_id
```

- 도구의 예외 처리는 `langgraph-conventions`를 따른다 (LLM이 읽을 문장으로 돌려준다).

## 비동기

- FastAPI 엔드포인트와 LangGraph 노드를 `async def`로 쓸 때, 그 안에서 오래 기다리는 동기 함수(`requests.get`, `time.sleep`, 동기 DB 드라이버)를 부르지 않는다.
- 동기 라이브러리밖에 없으면 `anyio.to_thread.run_sync(...)`로 감싼다.
- 비동기 메서드는 `await` 없이 부르지 않는다.

## 로그

- `print` 금지. `logging.getLogger(__name__)`을 쓴다.
- **API 키, 개인정보, 프롬프트 전문은 로그에 남기지 않는다.** 질문·답이 필요하면 길이나 요청 id만 남긴다.
- 로그 메시지는 `%` 인자 방식: `logger.info("도구 호출: %s", tool_name)`. 로그에서는 f-string을 쓰지 않는다 (로그 수준이 꺼져 있어도 문자열이 만들어진다).

## 기타

- 매직 넘버 금지. 상수로 뺀다.
- 문자열 조립은 f-string (로그 제외).
- 파일 경로는 `pathlib.Path`. `os.path` 금지.
- 환경 변수는 `app/infrastructure/`의 설정 모듈에서만 읽는다 (`agent-architecture`). 다른 곳에서 `os.environ` 금지.

## 독스트링과 주석

**독스트링과 주석은 모두 한국어로 쓴다.** 도구 설명도 한국어다 (평가 결과를 보고 바꿀 수 있다).

### 독스트링 대상

| 대상 | 수준 |
|---|---|
| 클래스, 모듈 밖에서 쓰는 메서드, API 엔드포인트 | Google 스타일로 자세히 (`Args:`, `Returns:`, `Raises:`) |
| 도구 메서드 (`<기능>Tools`) | LLM이 읽는 설명서 — 아래 규칙 |
| Protocol 메서드 | 자세히 (구현이 지켜야 할 계약) |
| 비공개 메서드 (`_` 접두사) | 한 줄 |
| 자명한 메서드, Protocol 구현 메서드 | 생략 |

- **첫 문장에 책임을 적는다.** 첫 줄만 읽고 무엇을 하는지 알 수 있어야 한다.
- 한 문장은 짧게. 한 줄에 한 개념.

```python
async def find_product(self, product_id: str) -> Product:
    """상품 id로 상품 정보를 조회한다.

    Args:
        product_id: 조회할 상품 id.

    Returns:
        조회한 상품.

    Raises:
        ProductNotFoundError: 상품이 없을 때.
    """
```

### 도구 메서드 독스트링 — LLM용 설명서

LLM은 이 독스트링을 읽고 도구를 쓸지 정한다. 사람용 설명이 아니다.

- 도구는 `<기능>Tools`의 메서드를 `tool(self.<메서드>, parse_docstring=True)`로 감싸 만든다 (`langgraph-conventions`의 "도구 만들기"). 본문은 도구 설명으로, `Args:`는 인자 설명 칸으로 LLM에게 간다.
- 첫 문장: 무엇을 하는 도구인지.
- **언제 쓰는지, 언제 쓰면 안 되는지**를 적는다.
- 돌려주는 내용을 본문에 적는다. `Returns:`는 LLM에게 가지 않으므로 쓰지 않는다.
- `Args:`에 각 인자의 뜻과 형식(예: "8자리 숫자")을 적는다. 인자 이름과 맞지 않으면 도구를 만들 때 오류가 난다.

```python
class ProductTools:
    """상품 유스케이스를 부르는 도구 묶음. 공개 메서드 하나가 도구 하나다."""

    def __init__(self, products: ProductUseCase) -> None:
        self._products = products

    def build(self) -> list[BaseTool]:
        """에이전트에 넘길 도구 목록을 만든다."""
        return [tool(self.get_product, parse_docstring=True)]

    async def get_product(self, product_id: str) -> str:
        """상품 번호로 상품 이름과 가격을 조회한다.

        사용자가 특정 상품의 가격을 물을 때 쓴다.
        상품 번호를 모르면 쓰지 말고 사용자에게 번호를 먼저 묻는다.
        상품 정보 문장을 돌려준다. 상품이 없으면 없다는 안내 문장을 돌려준다.

        Args:
            product_id: 상품 번호. 영문 대문자 P와 숫자 3자리 (예: P001).
        """
        ...
```

### 구현 주석

- 코드가 "무엇을 하는지"는 주석으로 쓰지 않는다. 코드가 설명해야 한다.
- **"왜 이렇게 하는지"만** 남긴다 (업무 규칙, 우회 사유, 제약 조건).
