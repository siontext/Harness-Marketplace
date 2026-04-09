---
name: git-conventions
description: 브랜치 네이밍, 커밋 메시지, PR 템플릿, 이슈 관리 규칙. 커밋/PR 작성 시 참조.
---

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
[type] : [subject]
```

예시:
- `feat : login-page 구현`
- `fix : 인증 토큰 만료 처리 수정`
- `refactor : 공통 예외 모델 분리`

subject는 명사형 종결로 작성한다. (`~~ 추가`, `~~ 수정`, `~~ 생성`, `~~ 분리` 등)
구체적인 내용은 커밋 본문(Extended description)에 작성.

## Pull Request

- main branch merge 전 반드시 PR 올리기
- 라벨 설정 필수

### PR 제목

```
[subject]
```

예시: `login-page 구현`

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
