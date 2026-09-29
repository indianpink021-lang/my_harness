# R0 — 준비물 확인

## 컨텍스트 문서

| 문서 | 상태 | 역할 |
|---|---|---|
| `docs/prd.md` | 있음 | 서비스 원문 (story-service.md 에는 `docs/PRD.MD` 로 표기 — 실제 파일명은 소문자) |
| `docs/design.md` | 있음 | 디자인 규칙 원문 (판정 기준) |
| `docs/story-service.md` | 있음 | R1-A · 무엇을 위한 일인지 · 어기면 안 되는 것 2개 (판정 기준) |
| `docs/story-workflow.md` | 있음 | R1-B · 실제 작업 흐름 7단계 · 게이트 G1~G3 |
| `CLAUDE.md` / `.claude/` | 없음 | R7에서 생성 |
| git 저장소 | 아님 | R4(재개 방식)에서 다룸 |

> R1-A(story-service)는 R1-B(story-workflow)의 재료가 아니라 판정 기준이다. 섞지 않는다.

## 결정 사항

| # | 항목 | 결정 |
|---|---|---|
| Q1 | 하네스 | Claude Code (`CLAUDE.md` + `.claude/agents/`) |
| Q2 | design.md 충돌 해석 | Don'ts 우선 |
| Q3 | Figma 판정 입력 | 토큰·컴포넌트 JSON 내보내기 파일을 로컬 스크립트가 읽음 |
| Q4 | 레퍼런스 수집 | uibowl MCP 사용 |

## design.md 충돌 → 셀 수 있는 규칙

| 충돌 | 규칙 |
|---|---|
| 그림자 (Don't vs `ex-modal-card`·`ex-toast`) | shadow 개수 = 0, 예외는 `segmented-control-active` 1개만 |
| 대문자 (Don't vs `ex-data-table-cell` mono-caps) | `textCase = UPPER` 개수 = 0 |
| 레이아웃 (390×844 vs testimonial 4컬럼) | 폭 390 프레임에서 컬럼 수 ≤ 2 |

## 레퍼런스 수집 규칙 (uibowl)

- 레퍼런스 개수 ≥ 5
- 모든 항목에 `ui_url` 존재
