# R7 — 오케스트레이터

## 누가

- 메인 Claude Code 세션이 `CLAUDE.md`를 읽고 오케스트레이터를 맡는다. 별도 에이전트 없음.
  (서브에이전트는 다른 서브에이전트를 호출할 수 없기 때문)

## 한 단계 실행 순서

1. `state.json` 읽기 → 현재 단계 확인
2. 단계 에이전트 호출 (S1 `ref-collector` / S2 `ref-analyst` / S3 `spec-writer`)
3. `gate-judge` 호출 → `judge.py` 결과 JSON 수신
4. 통과 → `state.json` 기록, 다음 단계
5. 실패 → `rules.json.on_fail`로 복귀, `attempts` +1
6. `attempts` > 2 → `blocked`, 멈추고 사람에게 묻기
7. G2 통과 → 멈추고 사람에게 S4 넘김 ("Figma 작업 차례예요")

판정 결과를 해석하거나 뒤집지 않는다. `pass: false`면 무조건 실패.

## `state.json`

```json
{
  "screen": "skill-library",
  "stage": "S3",
  "gates": {
    "G1": { "status": "pass", "attempts": 1, "failed_rules": [] },
    "G2": { "status": "fail", "attempts": 1, "failed_rules": ["G2-private-default"] }
  },
  "updated_at": "2026-09-29T21:00:00"
}
```

- `status` ∈ `pending` / `pass` / `fail` / `blocked`

## `CLAUDE.md` 작성 원칙

- 80줄 이내. 역할 · 순서 · 트리거 · 금지 사항만. 수치는 `rules.json`을 가리킨다.
- 금지: 판정 결과 해석·번복 / `docs/` 수정 / `04-approval.md` 대리 작성
