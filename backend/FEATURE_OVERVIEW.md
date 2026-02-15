# Aira 기능 요약

## 상단 요약 (기능 목록)

- 실시간 음성 대화 (Gemini Live + WebSocket)
- 의도 라우팅 (Azure OpenAI 기반 intent 분류)
- 교통 안내 (지하철/버스/퇴근길, ODSay + 서울시 지하철 실시간)
- 날씨/대기질 안내 (Open-Meteo 기반, 접속 시 캐시 선적재)
- 비전 기반 대화 (카메라/화면 프레임을 Gemini Live에 직접 입력 - 기존 vlm 방식에서 교체)
- 뉴스 안내 (네이버 뉴스 API)
- Gmail 프로액티브 알림 (긴급 메일 선제 안내, 톤 가변)
- 사용자 메모리/프로필 저장 (Cosmos DB)
- 실시간 위치 업데이트 반영
- 응답 안정화 가드(선발화/중복 응답/턴 충돌 완화)

---

## 1. 실시간 음성 대화

- 사용 API/툴:
  - Gemini Live API (`gemini-2.5-flash-native-audio-preview-12-2025`)
  - WebSocket (`/ws/audio`)
  - Azure Speech SDK (STT 로그/보조 처리)
- 동작 프로세스:
  1. 프론트에서 마이크 오디오를 `/ws/audio`로 전송
  2. 서버가 Gemini Live 세션으로 오디오 전달
  3. Gemini 응답 오디오를 다시 프론트로 스트리밍
  4. STT 텍스트를 로그/의도 라우팅/디버깅에 활용

## 2. 의도 라우팅

- 사용 API/툴:
  - Azure OpenAI (기본 `gpt-4o-mini` 계열 배포)
- 동작 프로세스:
  1. 사용자 발화를 intent로 분류
  2. `destination`, `home_update` 등을 JSON으로 추출
  3. 실패 시 키워드 fallback 라우팅
- 주요 intent:
  - `subway_route`, `bus_route`, `weather`, `air_quality`, `news`, `commute_overview`, `general`

## 3. 교통 안내 (지하철/버스/퇴근길)

- 사용 API/툴:
  - ODSay API (경로/근처 역·정류장)
  - 서울시 지하철 실시간 도착 API
- 동작 프로세스:
  1. 현재 좌표(lat/lng) 기반 인근 역/정류장 탐색
  2. 목적지(집 또는 사용자 지정)까지 경로 계산
  3. 지하철: 방면, 도보시간, 도착예정, 탑승 가능성 판단
  4. 버스: 버스번호/정류장/도보시간 안내
  5. 요약을 Gemini 라이브 컨텍스트에 주입해 자연 발화

## 4. 날씨/대기질 안내

- 사용 API/툴:
  - Open-Meteo Forecast API
  - Open-Meteo Air Quality API
- 동작 프로세스:
  1. 접속 직후 환경 데이터 캐시 선적재
  2. TTL/이동거리 기준으로 캐시 갱신
  3. 질의 시 캐시 우선 응답 (지연 최소화)
- 저장 상세:
  - 날씨: 현재기온, 최고/최저, 강수량, 강수확률, 구름량, 하늘상태
  - 대기질: US AQI, PM10, PM2.5, 등급

## 5. 비전 기반 대화

- 사용 API/툴:
  - 프론트 카메라/스크린 프레임
  - Gemini Live `media` 입력
- 동작 프로세스:
  1. 카메라/화면 프레임을 서버로 전송
  2. 서버가 같은 Gemini Live 세션으로 media 입력
  3. 시각 질의 시 최신 프레임/스냅샷을 반영해 응답
- 참고:
  - 비전은 별도 모델이 아니라 같은 Live 세션에서 처리

## 6. 뉴스 안내

- 사용 API/툴:
  - Naver Search News OpenAPI (`backend/modules/news_agent.py`)
- 동작 프로세스:
  1. `news` intent 감지
  2. 발화에서 뉴스 토픽 추출
  3. 네이버 뉴스 조회 후 헤드라인 요약 발화
- 필요 env:
  - `NAVER_CLIENT_ID`
  - `NAVER_CLIENT_SECRET`

## 7. Gmail 프로액티브 알림

- 사용 API/툴:
  - Gmail IMAP (`imap.gmail.com:993`)
  - Azure OpenAI LLM (긴급도 + 톤 판정)
- 동작 프로세스:
  1. 접속 시작: 이전 종료~현재 접속 사이 메일 백로그 확인
  2. 접속 중: IDLE 이벤트 기반 감지 + fallback 조회
  3. 긴급 메일만 선제 음성 안내
  4. 메일 성격에 따라 tone 반영
- tone 예시:
  - `urgent`, `celebratory`, `empathetic`, `neutral`

## 8. 사용자 메모리/프로필

- 사용 API/툴:
  - Cosmos DB (`modules/cosmos_db.py`)
  - Memory 요약 서비스 (`modules/memory.py`)
- 동작 프로세스:
  1. 접속 시 과거 대화 요약 로드
  2. 종료 시 세션 대화 요약 후 저장
  3. 사용자 홈 목적지 저장/업데이트

## 9. 실시간 위치 업데이트

- 사용 API/툴:
  - 프론트 `location_update` 이벤트
- 동작 프로세스:
  1. 접속 후 좌표 업데이트 수신
  2. 의미 있는 이동 시 내부 상태/캐시 갱신
  3. 교통/날씨 계산에 즉시 반영

## 10. 응답 안정화 가드

- 사용 API/툴:
  - 서버 내부 게이트 상태(`response_guard`, `transit_turn_gate`)
- 동작 프로세스:
  1. 컨텍스트 주입 전 조기 오디오 억제
  2. 중복 STT 턴 스킵
  3. 턴 완료 시 가드 해제
  4. 프로액티브 알림 전/후 가드 리셋

---

## 운영 엔드포인트

- `/ws/audio`: 실시간 음성/비전 대화 WebSocket
- `/api/seoul-info/live`: 실시간 교통/환경 정보 조회
- `/api/seoul-info/normalize`: 서울 정보 패킷 정규화
