# R6 — 역할

## 에이전트별 편집 폴더

| 에이전트 | 단계 | 편집 가능 (여기만) | 도구 |
|---|---|---|---|
| `ref-collector` | S1 | `runs/<screen>/s1/` | uibowl MCP, Write |
| `ref-analyst` | S2 | `runs/<screen>/s2/` | Read, Write |
| `spec-writer` | S3 | `runs/<screen>/s3/` | Read, Write |
| (사람) | S4 | `runs/<screen>/s4/` | Figma |
| 오케스트레이터 | 전체 | `runs/<screen>/state.json`, `runs/<screen>/s5/` | 판정 결과 저장, 요약 작성, Figma MCP(읽기 전용)로 `s5/05-figma-export.json` 생성 (R8에서 추가) |

## 읽기전용 판정자

- `harness/judge.py`: `rules.json`을 읽고 결과 JSON을 stdout으로만 출력. 파일 쓰기 없음.
- `gate-judge` 에이전트: 도구는 `Read`, `Bash(python3 harness/judge.py *)`뿐. Write/Edit 없음.
- 판정 결과는 오케스트레이터가 `state.json`(G1·G2·G3)과 `s5/`(S5)에 저장.

## 자연어 트리거

| 말 | 동작 |
|---|---|
| "〈화면명〉 시작해줘" | 새 실행 생성, S1부터. 화면명이 `rules.json.screens`에 없으면 거부 |
| "이어서 해줘" | `state.json` 읽고 멈춘 단계부터 |
| "검토해줘" | S5 시작. `s4/`에 파일 2개 없으면 거부 |
| "상태 알려줘" | 현재 단계 · 게이트 결과 · 재시도 횟수 표시 |

## 강제 방법

- `PreToolUse` hook이 Write/Edit 경로 검사 → 허용 폴더 밖이면 차단.
- `docs/`, `harness/rules.json`, `harness/judge.py`는 모든 에이전트 읽기 전용.
