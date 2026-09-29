# 화면 설계: my-assets (selftest 픽스처)

## 목적
- 멤버가 자신이 만든 자산을 목록으로 보고 새 자산을 등록한다.

## 사용자
- 유료 회원, 판매 승인 회원

## 구성 요소
- 자산 카드 목록
- 공개 범위 선택
- 새 자산 등록 버튼

## 상태
- 임시저장 / 검수 대기 / 수정 요청 / 승인됨 / 반려

## 권한
- 열람: paid, seller
- default_visibility: private
- sale_requested: seller
