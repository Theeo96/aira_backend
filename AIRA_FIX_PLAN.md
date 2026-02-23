# AIRA 장애 수정 플랜

## 대상 이슈
1. 열차 도착정보 미응답
2. 집정보(귀가 목적지) 수정 미반영

## 1) 원인 요약

## 1.1 열차 도착정보
- ETA는 ODSay가 아니라 서울 실시간 API(`realtimeStationArrival`) 경로에서 계산됨
- 실패 요인:
  - 네트워크 연결 실패(`WinError 10061` 계열)
  - 도착 질의 분류 실패(`is_arrival_eta_query(...)`)
  - 역명 추출 실패(조회 역이 비어 있거나 잘못됨)
  - 환경변수 키 충돌(`SEOUL_API_KEY` vs `Seoul_API`)

## 1.2 집정보 수정
- 실패 요인:
  - 집 변경 의도 탐지 실패(`is_home_update_utterance(...)`)
  - 목적지 추출 실패(`extract_destination_from_text(...)`)
  - Cosmos DB 미연결(`container is None`)로 upsert 미실행

## 2) 수정 계획

## Phase 1: 텍스트 룰 안정화 (최우선)
- 대상:
  - `backend/modules/route_text_utils.py`
  - `backend/modules/conversation_text_utils.py`
  - `backend/modules/fast_intent_router.py`
  - `backend/modules/intent_router.py`
- 작업:
  - 키워드/정규식 룰 정상화
  - 도착질의/집수정 발화 케이스 테스트 추가

## Phase 2: 열차 도착정보 경로 강화
- 정책:
  - ETA는 서울 실시간 API 우선
  - 경로(TMAP/ODSay)와 ETA를 분리 처리
- 작업:
  - 역명 우선순위 확정: 사용자 발화 역명 > 경로 출발역 > 근처역
  - row 수/선택된 역명/first-next ETA 로그 추가
  - 실패 시 fail-closed 응답:
    - `"현재 열차 도착 정보를 받을 수 없습니다."`

## Phase 3: 집정보 수정 신뢰성 개선
- 작업:
  - 집 변경 명시 발화 패턴 보강
  - 추출 실패 시 1회 확인 질문
  - 저장 성공/실패를 사용자 응답 + 서버 로그에 모두 표시
  - DB 미연결 시 세션 임시 반영 + 경고 로그

## Phase 4: 운영 환경 정리
- ENV 키 단일화:
  - `SEOUL_API_KEY`만 사용, `Seoul_API` 제거 권장
- 네트워크:
  - 서울 API 도메인 outbound 허용(방화벽/프록시/사내망 정책 확인)
- 회귀 테스트:
  1. 도착정보 질의 5종
  2. 집정보 수정 질의 5종
  3. 재접속 후 프로필 재로딩 확인

## 3) 즉시 체크리스트
- [ ] `SEOUL_API_KEY` 단일 키 정리
- [ ] 도착질의 분류 로그 확인
- [ ] 서울 API row 수 로그 확인
- [ ] `home_update` 저장 성공 로그 확인
- [ ] Cosmos DB 연결 상태 점검
