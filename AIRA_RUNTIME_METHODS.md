# AIRA 런타임 메서드/함수 정리

## 1) 서버 진입점
- 파일: `backend/server.py`
- 핵심:
  - `audio_websocket(ws)`: 음성/STT/의도 라우팅/컨텍스트 주입/응답 전송 메인 루프
  - `create_api_router(...)`: HTTP API 라우터 연결

## 2) 의도 라우팅
- 빠른 라우팅: `backend/modules/fast_intent_router.py`
  - `fast_route_intent(...)`
- LLM 라우팅: `backend/modules/intent_router.py`
  - `IntentRouter.route(...)`
  - `IntentRouter._fallback(...)`
- 텍스트 룰: `backend/modules/route_text_utils.py`
  - `extract_destination_from_text(...)`
  - `is_schedule_query(...)`
  - `is_arrival_eta_query(...)`
- 대화 보조 룰: `backend/modules/conversation_text_utils.py`
  - `is_home_update_utterance(...)`

## 3) 실시간 교통/도시 요약
- 오케스트레이션: `backend/modules/seoul_live_service.py`
  - `SeoulLiveService.execute_tools_for_intent(...)`
- 요약 생성: `backend/modules/live_seoul_summary_service.py`
  - `LiveSeoulSummaryService.build_summary(...)`
  - 내부에서 경로/날씨/대기질/혼잡/도착예정 조합

## 4) 교통 API 래퍼
- TMAP: `backend/modules/tmap_service.py`
  - `get_transit_route(...)`
  - `get_subway_car_congestion(...)`
  - `get_poi_congestion(...)`
- ODSay + 서울 실시간 도착: `backend/modules/transit_runtime_service.py`
  - `get_odsay_path(...)`
  - `parse_odsay_strategy(...)`
  - `parse_tmap_strategy(...)`
  - `get_subway_arrival(station_name)`  # 서울 실시간 열차 도착
  - `extract_arrival_minutes(row, allow_zero)`

## 5) 집정보(귀가 목적지) 저장 경로
- `backend/server.py`
  - `_save_home_destination(new_home_destination)`
  - `routed_home_update` 또는 `_is_home_update_utterance(text)` 충족 시 저장 시도
  - `destination_state["name"]` 갱신
- `backend/modules/cosmos_db.py`
  - `get_user_profile(user_id)`
  - `upsert_user_profile(user_id, {"home_destination": ...})`

## 6) 현재 도착정보 계산 경로
- `arrival_query`로 분류되면 `LiveSeoulSummaryService.build_summary(...)`에서 도착정보 처리
- 실제 ETA(몇 분)는 `TransitRuntimeService.get_subway_arrival(...)` + `extract_arrival_minutes(...)`로 계산
- 경로 정보와 ETA 소스는 분리됨
