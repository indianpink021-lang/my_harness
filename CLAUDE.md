# 허들링 화면 설계 하네스

대상 화면 1개에 대해 레퍼런스 수집 → 분석 → 화면 설계 → (사람) Figma 제작 → 검토를 돌린다.
너(메인 세션)는 오케스트레이터다. 직접 산출물을 쓰지 말고 단계 에이전트를 호출하고, 판정은 gate-judge에 맡긴다.

## 기준 문서 (읽기 전용 — 절대 수정 금지)
- 서비스 목적·어기면 안 되는 것: docs/story-service.md
- 디자인 원문: docs/design.md · 서비스 원문: docs/prd.md
- 규칙 SSOT: harness/rules.json — 수치는 여기에만 있다. 이 문서에 수치를 옮겨 적지 않는다.
- 설계 기록: harness/r0-context.md ~ r8-verification.md

## 트리거
| 말 | 동작 |
|---|---|
| "〈화면명〉 시작해줘" | rules.json.screens에 있는 이름만 허용. runs/<screen>/ 생성, state.json 초기화, S1부터 |
| "이어서 해줘" | runs/<screen>/state.json 읽고 pending/fail인 첫 단계부터 |
| "검토해줘" | G3 통과 확인 → S5. 미통과면 거부 |
| "상태 알려줘" | stage · 게이트 status · attempts · failed_rules 표시 |

## 파이프라인
| 단계 | 담당 | 출력 | 게이트 |
|---|---|---|---|
| S1 수집 | ref-collector | s1/01-references.json | — |
| S2 분석 | ref-analyst | s2/02-analysis.md | G1 |
| S3 설계 | spec-writer | s3/03-screen-spec.md | G2 |
| S4 제작 | 사람 | s4/04-approval.md | G3 (사람 승인) |
| S5 검토 | 오케스트레이터 + gate-judge | s5/05-figma-export.json, 05-review.json, 05-review.md | S5 |

## 한 단계 실행 순서
1. state.json 읽기 → 현재 단계 확인
2. 단계 에이전트 호출 (결과 파일은 그 에이전트 폴더에만). 재작성이면 직전 failed_rules 를 함께 넘긴다
3. gate-judge 호출 → judge.py 결과 JSON 수신
4. pass → state.json 기록 후 다음 단계
5. fail → rules.json.on_fail 로 복귀, attempts +1
6. attempts > 2 → status: blocked, 멈추고 사람에게 묻기
7. G2 pass → 멈추고 "Figma 작업 차례예요. 끝나면 s4/04-approval.md 를 채우고 '검토해줘'라고 말해주세요" 안내

## S5 순서
1. s4/04-approval.md 의 figma_url 로 Figma MCP(읽기 전용) 호출
2. harness/r8-verification.md 의 고정 형식으로 변환 → s5/05-figma-export.json
3. gate-judge 호출 → 결과를 s5/05-review.json 에 그대로 저장, 사람용 요약 05-review.md 작성
4. 위반 severity 가 story-service 면 S3 로, 그 외면 S4 로 복귀 (judge 결과의 on_fail 을 따른다)

## state.json
{ "screen", "stage", "gates": { "<G>": { "status", "attempts", "failed_rules" } }, "updated_at" }
status ∈ pending / pass / fail / blocked

## 금지
- 판정 결과를 해석·완화·번복하지 않는다. pass:false 면 무조건 실패.
- docs/, harness/rules.json, harness/judge.py 를 수정하지 않는다.
- s4/04-approval.md 를 대신 쓰지 않는다. 사람 승인은 G3 한 곳뿐이다.
- 통과한 단계 파일을 덮어쓰지 않는다. 재작성 시 단계 에이전트가 이전 파일을 *.v<n>.* 로 보존한다 (s5/ 는 오케스트레이터가 보존).
- Figma 파일을 수정하지 않는다 (읽기만).

## 판정기 변경 시
judge.py 또는 rules.json 을 바꾸면 `python3 harness/judge.py --selftest` 통과 전까지 사용 금지.
