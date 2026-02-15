# server_main_ref.py 대비 server.py 차이 요약

## 한줄 요약
- 현재 `backend/server.py`는 `backend/server_main_ref.py` 대비 **기능 확장 + 모듈 분리 구조**로 크게 확장된 상태입니다.

## 변경 규모(파일 간 직접 diff 기준)
- 비교 대상: `backend/server_main_ref.py` -> `backend/server.py`
- 통계: **1 file changed, 1442 insertions(+), 18 deletions(-)**

## 큰 차이점
1. 실시간 대화 오케스트레이션 확장
- 단순 STT/TTS 중계 중심(`server_main_ref.py`)에서
- 의도 라우팅, 실시간 컨텍스트 주입, 응답 가드, 중복 발화 방지 로직이 추가됨.

2. Seoul/교통/환경 데이터 기능 추가
- ODSay 기반 경로/역/도착정보 처리
- Open-Meteo 기반 날씨/대기질 처리
- `/api/seoul-info/live`, `/api/seoul-info/normalize` 엔드포인트 사용/확장

3. 뉴스/메일 프로액티브 기능 추가
- Naver 뉴스 조회(`NewsAgent`) 연동
- Gmail 긴급 메일 감지 및 프로액티브 발화 루프 연동

4. 비전(카메라/스냅샷) 기능 추가
- 카메라 on/off, 프레임/스냅샷 수신
- Gemini Live로 비전 프레임 전달 및 턴 컨텍스트 반영

5. 설정/환경변수 확장
- Azure OpenAI 라우터, Gmail, 카메라, 캐시 TTL 등 운영용 env가 대폭 추가됨.

## 구조적 차이(정리 완료된 모듈 분리)
- `IntentRouter` 분리: `backend/modules/intent_router.py`
- Seoul 라이브 의도 실행 분리: `backend/modules/seoul_live_service.py`
- Gmail 알림 루프 분리: `backend/modules/gmail_alert_runner.py`
- Vision 런타임 처리 분리: `backend/modules/vision_service.py`

## 병합 관점 메모
- 현재 `server.py`는 핵심 로직이 모듈로 분리되어 있어, 향후 `main` 병합 시 충돌면적이 기존보다 작아진 상태입니다.
