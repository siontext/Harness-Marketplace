---
name: team-workflow
description: 하네스 에이전트(designer, 구현 에이전트, 리뷰 에이전트, pr-docs)에게 설계·구현·리뷰·PR 작업을 맡기는 순서와 서브에이전트 실행·정리 방식. 설계 문서 작성, 기능 구현, 코드 리뷰, PR 준비를 시작하거나 하네스 에이전트를 호출하기 전에 참조.
---

# 하네스 작업 흐름

## 맡기는 순서

| 단계 | 에이전트 | 플러그인 |
|---|---|---|
| 설계 | `designer` | core |
| 구현 | `backend-dev` (Java/Kotlin) | java |
| 리뷰·커밋 | `java-reviewer` (Java/Kotlin) | java |
| PR·문서 | `pr-docs` | core |

- 브레인스토밍·설계 단계에서는 `oop-principles`와 프로젝트 언어의 아키텍처 스킬(예: `java:layered-architecture`)을 참조한다.
- 설계 방향이 정해지면 문서 작성은 `designer`에게 맡긴다.
- 코드 검증·리뷰는 프로젝트 언어의 리뷰 에이전트에게 맡긴다.
- 에이전트 정의 파일(`plugins/<플러그인>/agents/<이름>.md`)에 적힌 사용자 질의 브리지 형식을 따른다. 서브에이전트는 `AskUserQuestion`을 직접 띄울 수 없어서 메인이 중계한다.

## 서브에이전트 실행·정리

- 서브에이전트는 background(`run_in_background`)로 띄우지 않고 **`name`을 붙여 포그라운드 teammate로** 띄운다. tmux pane에 진행 상황이 보여야 한다.
- 서브에이전트가 작업을 마치고 idle 알림을 보내면 결과를 회수한 뒤 바로 정리한다. idle 상태로 두지 않는다.
- 이유: "완료 시 자동 정리" 설정이 없다. background는 pane이 안 떠서 진행이 안 보이고, 포그라운드는 끝나도 idle로 대기한다.

## 금지 명령

`core` 플러그인의 PreToolUse 훅(`hooks/deny-guard.py`)이 `hooks/deny-rules.json`에 적힌 명령을 실행 전에 차단한다. 차단되면 메시지에 나온 대체 방법을 쓰거나 사용자에게 직접 실행을 요청한다.
