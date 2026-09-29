# R4 — 산출물

## 단계별 파일

실행 1회 = 대상 화면 폴더 1개: `runs/<screen>/`

> R6에서 단계별 하위 폴더 구조로 변경됨.

| 단계 | 파일 | 작성자 |
|---|---|---|
| S1 | `s1/01-references.json` | `ref-collector` |
| S2 | `s2/02-analysis.md` | `ref-analyst` |
| S3 | `s3/03-screen-spec.md` | `spec-writer` |
| S4 | `s4/04-approval.md` | 사람 |
| S5 | `s5/05-figma-export.json` (Figma MCP 변환), `s5/05-review.json` (위반 목록), `s5/05-review.md` (요약) | 오케스트레이터 |

> R8에서 변경: Figma JSON은 사람이 아니라 오케스트레이터가 `figma_url`로 Figma MCP(읽기 전용)를 호출해 만든다.
| 공통 | `state.json` (현재 단계, 재시도 횟수) | 오케스트레이터 |

- 파일명 규칙: `^0[1-5]-[a-z-]+\.(json|md)$` (재작성 백업 `*.v<n>.*` 제외)

## 화면 폴더명

| 화면 | 폴더 |
|---|---|
| 홈 | `home` |
| 무료 학습자료 | `free-content` |
| 유료 멤버 자료실 | `member-library` |
| 스킬 라이브러리 | `skill-library` |
| 미션 상세 | `mission-detail` |
| 제출 화면 | `submission` |
| 내 학습 | `my-learning` |
| 내 자산 | `my-assets` |
| 자산 상세 | `asset-detail` |
| 운영자 검수 화면 | `admin-review` |

## 규칙 SSOT

- `harness/rules.json` 1개. 판정 스크립트는 이 파일만 읽는다.
- `design.md`·`story-service.md`·R0~R3의 셀 수 있는 규칙을 모으고, 규칙마다 `source`(원문 출처)를 적는다.
- 원문(`design.md` 등)은 수정하지 않는다. `rules.json`은 R5 이후 생성.

## 재개

- 재시작 시 `state.json`을 읽고, 없거나 실패한 첫 단계부터 이어간다.
- 통과한 단계 파일은 덮어쓰지 않는다. 재작성 시 이전 파일을 `02-analysis.v1.md`처럼 보존한다 (git 없음).

## `04-approval.md` 형식

파일 맨 위에 네 줄 모두 필수. `approved: yes`가 없으면 S5 시작 거부.

```
approved: yes
approver: <이름>
date: YYYY-MM-DD
figma_url: https://www.figma.com/...
```
