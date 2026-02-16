# Aira 백엔드 통합 총정리

## 상단 요약
- 실시간 음성 대화: WebSocket + Gemini Live + Azure STT
- 의도 라우팅: Azure OpenAI 기반 Intent Router
- 교통 안내: ODSay + 서울시/지하철 도착정보 조합
- 환경 안내: Open-Meteo(날씨/대기질) 캐시 기반
- 비전 대화: 카메라/화면 프레임을 Gemini Live에 직접 입력
- 뉴스: Naver 뉴스 검색 + 키워드 기반 상세/후속 질문
- Gmail 알림: 접속 전/중 메일 감시 후 긴급 메일만 능동 발화
- 타이머: “N분 뒤에 말 걸어줘” 의도 분류 + 만료 시 능동 발화
- 사용자 메모리/프로필: Cosmos DB 저장/복원
- 응답 안정화: 선발화/중복발화 방지 가드

---

## 1. 전체 런타임 흐름
1. 클라이언트가 `/ws/audio`로 연결 (`user_id`, `lat`, `lng` 포함 가능).
2. 서버가 사용자 메모리/프로필을 로딩하고 Gemini Live 세션 생성.
3. 음성 입력은 Gemini Live와 Azure STT에 동시에 처리됨.
4. STT 텍스트가 나오면 Intent Router가 의도 분류.
5. 의도에 따라 필요한 API 호출(교통/날씨/대기질/뉴스 등) 수행.
6. 결과를 `[INTENT]/[CONTEXT]/[ACTION]` 형태 컨텍스트로 Gemini에 주입.
7. Gemini가 음성으로 최종 응답.
8. 세션 종료 시 요약을 생성해 메모리 DB에 저장.

---

## 2. 핵심 모듈 구조

### 2.1 서버 오케스트레이터
- `backend/server.py`
  - WebSocket 입출력 루프
  - STT 이벤트 처리
  - Intent 분기
  - 도구 실행 트리거
  - 세션/메모리 저장

### 2.2 의도/응답 제어
- `backend/modules/intent_router.py`
  - 의도 분류: `subway_route`, `bus_route`, `weather`, `air_quality`, `news`, `commute_overview`, `general`, `timer`, `timer_cancel`
- `backend/modules/ws_orchestrator_service.py`
  - 응답 게이트/우선순위/액션 지시문 조립
- `backend/modules/proactive_service.py`
  - 능동 발화(알림/타이머 만료 등)와 응답 가드 리셋

### 2.3 교통/환경
- `backend/modules/seoul_live_service.py`
  - 의도별 live 데이터 실행/요약
- `backend/modules/seoul_info_module.py`
  - `/api/seoul-info/normalize`용 정규화 패킷/요약

### 2.4 뉴스
- `backend/modules/news_agent.py`
  - Naver API 호출
- `backend/modules/news_context_service.py`
  - 뉴스 토픽 추출
  - 상세/후속 질의 판단
  - 키워드 기반 기사 선택
  - “전문 낭독 금지” 요약 생성 지원

### 2.5 메일/타이머/비전
- `backend/modules/gmail_alert_module.py`
  - Gmail(IMAP) 조회, 긴급성 판단
- `backend/modules/gmail_alert_runner.py`
  - 세션 중 루프/IDLE 기반 알림 실행
- `backend/modules/timer_service.py`
  - 타이머 등록/취소/만료 콜백
- `backend/modules/vision_service.py`
  - 카메라 상태/프레임/스냅샷 관리 및 Gemini 입력

### 2.6 데이터 계층
- `backend/modules/cosmos_db.py`
  - 사용자 메모리/프로필 저장
- `backend/modules/memory.py`
  - 세션 대화 요약

---

## 3. 기능별 동작 프로세스

### 3.1 교통(지하철/버스/퇴근길)
1. 사용자 발화 -> Intent Router 분류.
2. 좌표/목적지 기반으로 ODSay + 실시간 도착정보 호출.
3. `speechSummary` 생성.
4. Gemini에 컨텍스트 주입 후 최종 발화.

### 3.2 날씨/대기질
1. 접속 시점에 환경 데이터 캐시 선적재.
2. 질의 시 캐시 우선 응답, 필요 시 갱신 호출.
3. “데이터 없음”은 실제 없을 때만 응답하도록 가이드 적용.

### 3.3 뉴스
1. 뉴스 의도 -> 주제 추출 후 Naver 뉴스 3건 조회.
2. 헤드라인 응답.
3. 후속 질문(번호/키워드/맥락) 시 해당 기사 선택.
4. 기사 전문 낭독 없이 핵심 요약으로 답변.

### 3.4 Gmail 긴급 알림
1. 접속 시: 이전 종료 이후~현재까지 메일 확인.
2. 접속 중: IDLE/폴백 루프로 새 메일 감시.
3. 긴급 판단 시 능동 발화.
4. 톤(긴급/중립/공감/축하) 가이드 반영 가능.

### 3.5 타이머
1. “N초/분 뒤에 말해줘” -> `timer` intent + 초 단위 추출.
2. 타이머 등록.
3. 만료 시 능동 발화.
4. 활성 타이머 중 “지금 말해줘/바로” -> `timer_cancel`로 취소.

### 3.6 비전
1. 카메라/화면 공유 프레임 수신.
2. 주기 제어 후 Gemini Live `media` 입력.
3. 비전 관련 질문 시 최근 스냅샷 재참조.
4. 현재는 과거 다중 프레임 검색 기능은 없음(최신 스냅샷 중심).

---

## 4. 응답 안정화(선발화/중복 방지)
- `response_guard`: 컨텍스트 주입 전 조기 오디오 차단
- `transit_turn_gate`: 교통/도구 응답 우선 처리
- `speech_capture_gate`: 사용자 발화 중 모델 오디오 억제
- STT 중복 텍스트 디듀프
- 타이머 중복 설정 디듀프

---

## 5. 주요 엔드포인트
- `GET /` : 프론트 정적 페이지(빌드 존재 시)
- `WebSocket /ws/audio` : 실시간 음성/비전 대화
- `POST /api/seoul-info/normalize` : 정규화 패킷/요약
- `GET /api/seoul-info/live` : 실시간 교통/환경 조회

---

## 6. 주요 환경변수(핵심)
- Gemini: `GEMINI_API_KEY`
- Azure STT: `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`
- Azure OpenAI Router: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_DEPLOYMENT_NAME`(또는 `INTENT_ROUTER_MODEL`)
- 교통: `ODSAY_API_KEY`, `SEOUL_API_KEY`
- 뉴스: `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`
- Gmail: `GMAIL_IMAP_HOST`, `GMAIL_IMAP_PORT`, `GMAIL_EMAIL`, `GMAIL_APP_PASSWORD` (및 관련 임계값 변수)
- 기타: `COMMUTE_DEFAULT_DESTINATION`, `HOME_LAT`, `HOME_LNG`

---

## 7. 현재 한계/주의사항
- 비전은 최신 스냅샷 기반이며, 과거 프레임 검색/재매칭은 미구현.
- 뉴스 상세는 기사 원문 전문 제공이 아니라 요약 중심.
- 외부 API 키/권한/화이트리스트 상태에 따라 일부 기능 실패 가능.
- 실시간 음성 구조 특성상 네트워크 지연/브라우저 권한 상태가 체감 성능에 영향.

---

## 8. 운영 체크리스트(간단)
1. `/ws/audio` 연결 후 STT/음성 왕복 정상.
2. 날씨/미세먼지 질문 시 선발화(“모름”) 없이 데이터 응답.
3. 타이머 설정/취소/만료 능동 발화 정상.
4. 뉴스 3건 -> 키워드 상세 -> 후속 질문 연계 정상.
5. Gmail 긴급 메일 능동 알림 후 일반 대화 지속 가능.

---

## 9. main(server_main_ref.py) 대비 현재 server.py 차이
아래는 `backend/server_main_ref.py`(main 기준 참조본)와 현재 `backend/server.py`의 핵심 차이입니다.

1. 의도 라우팅/도구 실행 추가
- main 참조본: 단순 음성 중계 중심.
- 현재: `IntentRouter`로 의도 분류 후 교통/날씨/대기질/뉴스/타이머/Gmail 흐름 분기.

2. 선발화/중복발화 방지 가드 추가
- `response_guard`, `transit_turn_gate`, `speech_capture_gate` 도입.
- 컨텍스트 주입 전 조기 오디오를 억제하고, 중복/경합 응답을 줄이도록 구성.

3. 라이브 컨텍스트 주입 구조 추가
- `[LIVE_CONTEXT_UPDATE]` 기반으로 Gemini에 매 턴 동적 컨텍스트 주입.
- 위치/시간/도구 결과를 즉시 반영해 응답 정확도 개선.

4. 기능 모듈 확장
- 추가/연결 모듈:
  - `modules/seoul_live_service.py`
  - `modules/news_context_service.py`
  - `modules/timer_service.py`
  - `modules/proactive_service.py`
  - `modules/ws_orchestrator_service.py`
  - `modules/gmail_alert_module.py`, `modules/gmail_alert_runner.py`
  - `modules/vision_service.py`
- main 참조본에는 위 기능 모듈 연동이 없음.

5. 뉴스 기능 확장
- main 참조본: 뉴스 흐름 없음.
- 현재: Naver 뉴스 헤드라인 + 키워드 기반 상세/후속 질의 대응(전문 낭독 금지, 요약 중심).

6. 타이머/능동발화 추가
- main 참조본: 타이머/능동 알림 없음.
- 현재: “N분 뒤에 말해줘” 처리, 취소 의도 처리, 만료 시 능동 발화.

7. Gmail 긴급 메일 알림 추가
- main 참조본: Gmail 알림 없음.
- 현재: 접속 전/중 메일 감시, 긴급 메일만 선별해 능동 음성 알림.

8. 비전 기능 확장
- main 참조본: 비전 입력 경로 없음.
- 현재: 카메라/스크린 프레임을 Gemini Live media로 전달, 비전 질의 대응.

9. 엔드포인트/데이터 경로 확장
- `/api/seoul-info/live`, `/api/seoul-info/normalize` 경로와 정규화/요약 처리 추가.
- 위치 업데이트(`location_update`)를 세션 중 반영하는 실시간 처리 포함.

---

이 문서는 기존 `FEATURE_OVERVIEW.md`, `RUNTIME_API_TIMING.md`, `SERVER_CHANGES.md`(이력), `SERVER_REF_DIFF_SUMMARY.md`의 내용을 실행 관점으로 통합 정리한 최신 개요 문서입니다.
