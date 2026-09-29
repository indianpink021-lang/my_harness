# R8 — 검증과 리뷰

## Q1. Figma JSON 생성

- 사람은 `s4/04-approval.md`에 `figma_url:` 한 줄 추가.
- 오케스트레이터가 Figma MCP(읽기 전용)로 변환해 `s5/05-figma-export.json` 저장.
- 반영: r3 · r4 · r5 · r6 문서, `rules.json`(G3 `figma_url`, `S5_input`, 단계 하위 폴더 경로).

형식 (고정):

```json
{ "frames": [ { "name": "", "width": 390, "height": 844, "columns": 1,
  "nodes": [ { "name": "", "component": "", "fills": ["#hex"], "strokes": [],
               "radius": 0, "shadows": [], "gap": 0, "padding": 0,
               "text": "", "font": { "family": "", "weight": 400, "size": 15,
                                     "letterSpacing": 0, "textCase": "ORIGINAL" },
               "default_value": null } ] } ] }
```

## Q2. 판정기 selftest

- `harness/tests/fixtures/`: 통과 샘플 1세트 + 규칙별 실패 샘플.
- `python3 harness/judge.py --selftest`
  - 통과 샘플 → 27개 규칙 전부 pass
  - 실패 샘플 → 의도한 규칙 정확히 1개만 fail
  - `severity: story-service` 규칙 4개는 실패 샘플 필수
- `judge.py`·`rules.json` 수정 시 selftest 재실행. 실패 시 사용 금지.

## Q3. hook 검증

| 시도 | 기대 |
|---|---|
| `spec-writer` → `s3/` 쓰기 | 허용 |
| `spec-writer` → `s2/` 쓰기 | 차단 |
| 에이전트 → `docs/design.md` 또는 `rules.json` 수정 | 차단 |

## Q4. 드라이런과 리뷰

- `my-assets` 화면으로 S1~S3, G1·G2까지 실행.
- 사람이 판정 결과를 리뷰. 틀렸으면 `rules.json` 수정 → selftest 재실행.
