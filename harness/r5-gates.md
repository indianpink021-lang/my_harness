# R5 — 게이트

규칙의 수치는 `harness/rules.json`(SSOT)에 있다. 이 문서는 결정 기록이다.

## 게이트 요약

| 게이트 | 위치 | 판정 | 실패 시 복귀 |
|---|---|---|---|
| G1 | S2 → S3 | 기계 | S2 (레퍼런스 부족이면 S1) |
| G2 | S3 → S4 | 기계 | S3 |
| G3 | S4 협의 확정 | **사람** (유일한 사람 승인 지점) | S4 |
| S5 | 검토 | 기계 | design 위반 → S4 / story-service 위반 → S3 |

같은 단계 재시도 2회 초과 시 멈추고 사람에게 묻는다.

## G1 (S2 → S3)

- `01-references.json` 항목 수 ≥ 5, 모든 항목에 `ui_url`
- `02-analysis.md` 섹션 3개 존재: 반영할 것 / 반영하지 않을 것 / 근거
- "반영할 것" 항목 수 ≥ 3
- "반영할 것"의 모든 `ui_url`이 `01-references.json`에 존재 (지어낸 링크 0건)

## G2 (S3 → S4)

- `03-screen-spec.md` 섹션 5개 존재: 목적 / 사용자 / 구성 요소 / 상태 / 권한
- "권한"에 역할(`guest`/`free`/`paid`/`seller`/`admin`) ≥ 1
- "구성 요소" 항목 수 ≥ 1
- ★ story-service ①: 대상이 `my-assets`/`asset-detail`/`submission`이면 "권한"에 `default_visibility: private` 필수, `sale_requested` 선택 가능 역할 = `seller`만

## G3 (사람)

- `s4/04-approval.md` 맨 위 `approved: yes` / `approver:` / `date: YYYY-MM-DD` / `figma_url:` (R8에서 추가)

## S5 (검토 · `s5/05-figma-export.json`)

design.md:
- 허용 목록 밖 색 = 0 (`on-primary` = `#ffffff`로 확정)
- accent `#0066ff` 프레임당 ≤ 2, `button-primary`에 0
- radius ∈ {0, 16, 24, 9999}, 예외 `app-icon-squircle`(30%)
- shadow = 0, 예외 `segmented-control-active`
- font family = Pretendard, weight ∈ {300, 400, 600, 700}
- font size ∈ {32, 28, 24, 20, 18, 17, 15, 13, 12}
- letterSpacing = 0, textCase UPPER = 0
- spacing ∈ {4, 8, 12, 16, 24, 32, 48, 64}
- frame 390×844, 컬럼 ≤ 2
- 입력칸 평소 상태 테두리 = 0

★ story-service:
- ① 공개 범위 선택 컴포넌트 기본 선택값 = 비공개
- ② 모든 텍스트 레이어에서 개인정보 패턴(이메일·전화번호·주민번호) 검출 = 0 (더미 텍스트 포함)
