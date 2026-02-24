# 프로젝트 통합 및 수정 진행 상황 요약
이 문서는 대화 내역 초기화 및 새로운 세션(채팅창)으로 컨텍스트를 이전하기 위해 작성된 요약본입니다. 이전 세션에서 진행된 작업들을 갈무리하고, 앞으로 테스트/수정해야 할 내용들이 담겨 있습니다.

## 1. 지금까지 작업 완료된 사항 (Completed Work)

### 듀얼 페르소나 (Lumi & Rami) 아키텍처 통합
- `temp_front` 및 `reference_dual` 코드를 기반으로 `server.py`의 메인 웹소켓 환경을 듀얼 페르소나 구조로 변경 (`LumiRamiManager` 클래스 이식).
- 루미/라미 키워드로 페르소나가 스위칭되며 사용자 입력에 대해 두 개의 AI에게 Context가 모두 주입되어 대화 흐름 공유.

### Google OAuth 로그인 및 보조 정보 연동
- 프론트엔드 React의 Google 자동 로그인 루틴을 백엔드 통합 (`login_back/main.py` 병합).
- FastAPI `SessionMiddleware` 충돌 버그 해결 (`WebSocketFriendlySessionMiddleware` 적용).
- ngrok 환방형 터널링에서 발생하는 `redirect_uri_mismatch` 문제를 백엔드에서 헤더 조작 방식으로 해결.
- 로그인된 Google Token을 기반으로 Calendar(일정) 및 Gmail(메일) 요약본을 동적으로 추출하여 AI 프롬프트에 실시간 주입.

### 메모리 DB JSON 고도화 및 그래프 추출 
- 대화 내용을 단순 문자열 배열이 아니라 `{seq, speaker_type, ai_persona, text, created_at}` 객체 배열 형태로 `server.py`에서 파싱하여 누적 후 DB에 저장하도록 전면 개편.
- `memory.py`에서 전체 대화를 분석하여 감정(32개 감정 코드), 관계 파악 후 Graph용 Node/Edge JSON을 동적으로 제작하는 `analyze_unified_memory()` 도입.

### History MVP 시각화 그래프 복구
- 렌더링 되지 않던 `HistoryGraphMvp.jsx`의 내부 버그(원격 Mock 데이터 로드용 특정 ngrok url 하드코딩) 제거 및 동적 감지 로직 적용.
- 백엔드(`server.py`)에 Cosmos DB를 직통으로 거쳐 Graph Data를 내려주는 `/api/memory` 엔드포인트 신설.

### 카메라/화면공유 시각 인지 무시 버그 해결
- 프론트엔드의 `useAiraMedia.ts` 메모리 누수 문제 제거 (Persistent Video Element 방식 전환).
- 페이로드 전달 인자를 통일(`camera_snapshot_base64`)하고, Gemini Live SDK의 파라미터 타겟 오차를 수정하여 (`video=` 인자에서 올바른 `image=` 인자로 수정), AI가 사용자 카메라 속 객체를 인식할 수 있도록 구현 완료.

### 부가적인 버그 및 안정성 (Fallback) 대응
- ODSay / TMAP 대중교통 경로 안내 시 정규식 패턴 누락 해결 (첫 번째 전역, 도착예정, ETA 등).
- 날씨 뉴스와 일반 날씨 정보를 분리 매핑하고 최신 뉴스가 올바른 순서를 기준으로 가져오도록 `news_agent.py` 수정 (pubDate 인젝션).
- 공공데이터포털 서버 불안정 시 발생하는 `SSL: UNEXPECTED_EOF_WHILE_READING` 방어 처리 (`CERT_NONE` + Retry 로직 적용).

---

## 2. 앞으로 진행해야 할 사항 & 테스트 시나리오 (To-Do & Validation)

### A. 구동 및 버그 재발 테스트
새 채팅창에서 가장 먼저 다음 것들이 문제없이 돌아가는지 확인해야 합니다.
1. `c:\workspace\aira_backend` 에서 서버를 구동했을 때 구글 리다이렉트 로그인(Ngrok)이 오류 없이 동작하는지?
2. 로그인 후 구글 일정이나 메일과 관련된 질문을 "루미야" 혹은 "라미야" 에게 던졌을 때 정상적으로 대답이 나오는지?

### B. 시각 인지(Vision) 피드백 테스트
1. 브라우저에서 화면(카메라)을 켜고, AI에게 손가락 갯수를 보여주거나 화면 공유로 문서 하나를 띄운 뒤 "몇 개야?", "무슨 내용이야?" 질문하기. 정상적으로 대답이 이어진다면 수정된 `image=` 인자가 잘 작동하는 것입니다.

### C. 메모리 그래프 (History MVP) 실 데이터 테스트
1. "History MVP (Memory)" 탭으로 이동. 
2. 우측 상단 '임시데이터' 토글을 껐을 때, Cosmos DB에 방금 전까지 이야기한 사용자의 대화 흐름이 올바른 3D/2D 그래프로 예쁘게 시각화되는지 렌더링 확인 (백엔드 `/api/memory` 기능 점검).

### D. 추가 고도화 방향성 건의
위 사항들이 모두 정상 동작한다면, 아래 항목들을 우선적으로 논의할 수 있습니다.
- Google Calendar에 일정을 직접 "추가"하거나 메일을 "요약해서 읽기" 기능 등.
- 듀얼 페르소나끼리 잡담하거나 끼어드는 "다이나믹 턴 매니저" 구조 설계 수정.
- 대중 교통 길찾기 Fallback 정규식 추가 확장 등.

---

> **새 채팅창 오픈 시 유의사항**
새로운 채팅 프롬프트 시작하실 때, **"이전 대화에서 이러이러한 변경으로 버그를 고쳤어. 앞으로 진행할 거는 project_status_summary.md 참고해 줘."** 라고 말씀해 주시면, 제가 시작하자마자 이 파일을 읽고 완벽하게 맥락을 캐치하겠습니다.
