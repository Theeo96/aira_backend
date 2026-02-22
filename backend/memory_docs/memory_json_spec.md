# 그래프 + 대화전문 통합 JSON 스펙 (단일 고정안)

이 문서는 실제 DB/API 연동 시 사용할 **단일 수신 JSON 형식 1개**를 정의합니다.  
즉, 한 번에 이 구조만 받으면:

1. 그래프 렌더링(`graph_with_ts.json` 역할)
2. 히스토리 목록/상세(`historyFromGraph.json` 역할)
3. 대화 전문 분석 + 턴(메모리) 단위 감정 분석
   을 모두 처리할 수 있습니다.

---

## 1) 결론

앞으로는 아래 **통합 구조 1개만** 사용합니다.

- 파일/응답 이름 예시: `history_graph_bundle.json`
- 루트: `conversations[]`
- 각 conversation 안에 `messages`, `memories`, `graph`를 같이 포함
- 프론트는 추가 조합 없이 이 데이터로 그래프와 대화내역을 모두 렌더

---

## 2) 필수 필드 (요약)

### 공통 식별자

- `conversation_id`: 대화 전문 단위 ID (예: `BE22015060`)
- `utterance_id`: 턴 단위 ID (예: `BE22015060_00000`)
- `memory_key`: 그래프 memory 노드 키 (예: `mem:BE22015060_00000`)

### 대화 전문(Conversation) 필수

- `conversation_id`, `user_id`, `started_at`, `ended_at`
- `summary.context_summary`, `summary.sentiment`

### 메시지(Messages) 필수

- `message_id`, `conversation_id`, `seq`, `speaker_type`, `text`, `created_at`
- `speaker_type = "ai"`일 때 `ai_persona` 필수 (`rumi` 또는 `lami`)

### 메모리(Memories: 턴 분석) 필수

- `memory_key`, `conversation_id`, `utterance_id`, `turn_index`
- `user_message_id`, `ai_message_ids`(rumi/lami 중 존재하는 것)
- `emotion.id`, `emotion.code`, `emotion.label_ko`, `emotion.family_7`
- `sentiment`, `relation`, `ts`, `full_text`

### 그래프(Graph) 필수

- `nodes[]`, `edges[]`
- memory 노드의 `key`는 반드시 `memory_key`와 동일

### 역할 구분 (중요)

- `messages`: 대화 **전문 전체 원문**입니다. 프론트 상세 화면은 이 값을 순서대로 그대로 보여줍니다.
- `memories`: `messages`를 턴(사용자 1발화 + AI 응답들) 단위로 분석한 결과입니다.  
  한 대화(`conversation_id`) 안에 `memories`가 여러 개 생기는 것이 정상입니다.
- `graph`: `memories`를 시각화하기 위한 파생 데이터(`nodes/edges`)입니다.  
  즉, 원본은 `messages`이고, `memories`/`graph`는 분석/시각화 계층입니다.
- 실무에서는 보통 `messages`는 길고(전문 전체), `memories`는 그중 **핵심 턴 일부만 추출**됩니다.

---

## 3) 단일 통합 스키마 (고정)

아래는 **필수 필드만 남긴 축약 예시 1개**입니다.
- 실제 응답에서는 `conversations[]`에 여러 대화를 같은 구조로 반복해서 담으면 됩니다.

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-02-22T00:00:00.000Z",
  "conversations": [
    {
      "conversation_id": "BE22015060",
      "user_id": "user_001",
      "started_at": "2025-09-01T09:00:00.000Z",
      "ended_at": "2025-09-01T09:12:20.000Z",
      "summary": {
        "context_summary": "합격 소식 이후 기쁨과 긴장이 함께 나타난 대화.",
        "sentiment": "positive"
      },
      "messages": [
        {
          "message_id": "msg_BE22015060_000",
          "conversation_id": "BE22015060",
          "seq": 0,
          "speaker_type": "user",
          "ai_persona": null,
          "text": "오늘 합격 연락 받았어. 너무 기뻐.",
          "created_at": "2025-09-01T09:00:10.000Z"
        },
        {
          "message_id": "msg_BE22015060_001",
          "conversation_id": "BE22015060",
          "seq": 1,
          "speaker_type": "ai",
          "ai_persona": "rumi",
          "text": "정말 축하해. 그동안의 노력이 느껴져.",
          "created_at": "2025-09-01T09:00:20.000Z"
        },
        {
          "message_id": "msg_BE22015060_002",
          "conversation_id": "BE22015060",
          "seq": 2,
          "speaker_type": "ai",
          "ai_persona": "lami",
          "text": "합격 메일과 제출 서류를 먼저 백업하자.",
          "created_at": "2025-09-01T09:00:30.000Z"
        },
        {
          "message_id": "msg_BE22015060_003",
          "conversation_id": "BE22015060",
          "seq": 3,
          "speaker_type": "user",
          "ai_persona": null,
          "text": "근데 첫 출근 생각하니까 부담도 커.",
          "created_at": "2025-09-01T09:06:00.000Z"
        },
        {
          "message_id": "msg_BE22015060_004",
          "conversation_id": "BE22015060",
          "seq": 4,
          "speaker_type": "ai",
          "ai_persona": "rumi",
          "text": "기쁜데도 긴장되는 마음, 충분히 자연스러워.",
          "created_at": "2025-09-01T09:06:12.000Z"
        },
        {
          "message_id": "msg_BE22015060_005",
          "conversation_id": "BE22015060",
          "seq": 5,
          "speaker_type": "ai",
          "ai_persona": "lami",
          "text": "첫 주 체크리스트 5개만 만들자.",
          "created_at": "2025-09-01T09:06:24.000Z"
        },
        {
          "message_id": "msg_BE22015060_006",
          "conversation_id": "BE22015060",
          "seq": 6,
          "speaker_type": "user",
          "ai_persona": null,
          "text": "리스트 써보니까 마음이 좀 정리됐어.",
          "created_at": "2025-09-01T09:12:00.000Z"
        },
        {
          "message_id": "msg_BE22015060_007",
          "conversation_id": "BE22015060",
          "seq": 7,
          "speaker_type": "ai",
          "ai_persona": "rumi",
          "text": "좋아, 지금 페이스를 잘 찾고 있어.",
          "created_at": "2025-09-01T09:12:10.000Z"
        },
        {
          "message_id": "msg_BE22015060_008",
          "conversation_id": "BE22015060",
          "seq": 8,
          "speaker_type": "ai",
          "ai_persona": "lami",
          "text": "내일 아침엔 체크리스트만 한 번 더 확인하자.",
          "created_at": "2025-09-01T09:12:20.000Z"
        }
      ],
      "memories": [
        {
          "memory_key": "mem:BE22015060_00000",
          "conversation_id": "BE22015060",
          "utterance_id": "BE22015060_00000",
          "turn_index": 0,
          "user_message_id": "msg_BE22015060_000",
          "ai_message_ids": ["msg_BE22015060_001", "msg_BE22015060_002"],
          "emotion": {
            "id": "E01",
            "code": "E01_JOY",
            "label_ko": "기쁨",
            "family_7": "JOY"
          },
          "sentiment": "positive",
          "relation": "친구",
          "full_text": "합격 소식에 대한 고양감이 크게 나타난 턴.",
          "ts": "2025-09-01T09:00:30.000Z"
        },
        {
          "memory_key": "mem:BE22015060_00001",
          "conversation_id": "BE22015060",
          "utterance_id": "BE22015060_00001",
          "turn_index": 1,
          "user_message_id": "msg_BE22015060_003",
          "ai_message_ids": ["msg_BE22015060_004", "msg_BE22015060_005"],
          "emotion": {
            "id": "E25",
            "code": "E25_PRESSURE",
            "label_ko": "부담",
            "family_7": "ANXIETY_FEAR"
          },
          "sentiment": "negative",
          "relation": "친구",
          "full_text": "첫 출근을 떠올리며 부담이 상승한 턴.",
          "ts": "2025-09-01T09:06:24.000Z"
        },
        {
          "memory_key": "mem:BE22015060_00002",
          "conversation_id": "BE22015060",
          "utterance_id": "BE22015060_00002",
          "turn_index": 2,
          "user_message_id": "msg_BE22015060_006",
          "ai_message_ids": ["msg_BE22015060_007", "msg_BE22015060_008"],
          "emotion": {
            "id": "E32",
            "code": "E32_NEUTRAL",
            "label_ko": "중립",
            "family_7": "NEUTRAL"
          },
          "sentiment": "neutral",
          "relation": "친구",
          "full_text": "체크리스트 작성 후 정서가 안정된 턴.",
          "ts": "2025-09-01T09:12:20.000Z"
        }
      ],
      "graph": {
        "nodes": [
          {
            "key": "emo:E01_JOY",
            "type": "emotion",
            "label": "기쁨 (E01_JOY)",
            "group": "JOY",
            "size": 8
          },
          {
            "key": "emo:E25_PRESSURE",
            "type": "emotion",
            "label": "부담 (E25_PRESSURE)",
            "group": "ANXIETY_FEAR",
            "size": 8
          },
          {
            "key": "emo:E32_NEUTRAL",
            "type": "emotion",
            "label": "중립 (E32_NEUTRAL)",
            "group": "NEUTRAL",
            "size": 8
          },
          {
            "key": "rel:친구",
            "type": "relation",
            "label": "친구",
            "size": 7
          },
          {
            "key": "mem:BE22015060_00000",
            "type": "memory",
            "label": "합격 직후 고양감",
            "emotion": "기쁨 (E01_JOY)",
            "relation": "친구",
            "full_text": "합격 소식에 대한 고양감이 크게 나타난 턴.",
            "ts": "2025-09-01 09:00:30",
            "emotion_score": 0.92
          },
          {
            "key": "mem:BE22015060_00001",
            "type": "memory",
            "label": "첫 출근 부담 상승",
            "emotion": "부담 (E25_PRESSURE)",
            "relation": "친구",
            "full_text": "첫 출근을 떠올리며 부담이 상승한 턴.",
            "ts": "2025-09-01 09:06:24",
            "emotion_score": 0.81
          },
          {
            "key": "mem:BE22015060_00002",
            "type": "memory",
            "label": "체크리스트 후 정서 안정",
            "emotion": "중립 (E32_NEUTRAL)",
            "relation": "친구",
            "full_text": "체크리스트 작성 후 정서가 안정된 턴.",
            "ts": "2025-09-01 09:12:20",
            "emotion_score": 0.74
          }
        ],
        "edges": [
          {
            "source": "mem:BE22015060_00000",
            "target": "emo:E01_JOY",
            "type": "memory_emotion",
            "weight": 1
          },
          {
            "source": "mem:BE22015060_00000",
            "target": "rel:친구",
            "type": "memory_relation",
            "weight": 1
          },
          {
            "source": "mem:BE22015060_00001",
            "target": "emo:E25_PRESSURE",
            "type": "memory_emotion",
            "weight": 1
          },
          {
            "source": "mem:BE22015060_00001",
            "target": "rel:친구",
            "type": "memory_relation",
            "weight": 1
          },
          {
            "source": "mem:BE22015060_00002",
            "target": "emo:E32_NEUTRAL",
            "type": "memory_emotion",
            "weight": 1
          },
          {
            "source": "mem:BE22015060_00002",
            "target": "rel:친구",
            "type": "memory_relation",
            "weight": 1
          }
        ]
      }
    }
  ]
}
```

---
## 4) A/B 기능이 이 스키마에서 어떻게 나오는지

### 그래프(A) 생성

- 사용 필드: `conversation.graph.nodes[]`, `conversation.graph.edges[]`
- 규칙: `memory` 노드 `key`는 `mem:*` 형식이고 `memories[].memory_key`와 1:1 동일

### 대화내역(B) 생성

- 목록 카드:
  - `id` <- `conversation_id`
  - `date` <- `started_at`
  - `summary.context_summary` / `summary.sentiment`
- 상세 전문:
  - `messages[]` 순서(`seq`)대로 렌더
  - `speaker_type=ai` + `ai_persona`로 Rumi/Lami 스타일 구분
- 노드 클릭 연결:
  - `memory_key`로 `memories[]` 찾기
  - 찾은 memory의 `conversation_id`로 해당 전문 상세 진입

---

## 5) 감정 체계 (대분류 7 / 소분류 32)

### 7개 상위 감정군(`family_7`)

- `JOY`, `HURT`, `SADNESS`, `ANGER`, `ANXIETY_FEAR`, `SURPRISE_CONFUSION`, `NEUTRAL`

### 32개 소분류 코드 저장 규칙

- 필수 저장: `emotion.id` + `emotion.code` + `emotion.label_ko`
- 예:
  - `E01_JOY`(기쁨)
  - `E18_IRRITATION`(짜증)
  - `E25_PRESSURE`(부담)
  - `E29_DISAPPOINTED`(실망)
  - `E32_NEUTRAL`(중립)

그래프 집계는 `family_7` 기준으로 하고, 상세/분석은 `id+code` 기준으로 사용합니다.

---

## 6) 구현 체크리스트 (이 스키마 준수 확인)

1. 모든 memory에 `memory_key`, `utterance_id`, `conversation_id`가 있는가
2. `memory_key == graph.nodes[].key(type=memory)` 1:1 매칭되는가
3. 모든 메시지에 `created_at`이 있고 대화 시간축이 정렬되는가
4. AI 메시지에 `ai_persona`(`rumi`/`lami`)가 명시되는가
5. 모든 memory에 감정 32코드(`emotion.id/code`)와 `family_7`가 함께 있는가
6. 카드/전문/그래프 진입 시 동일 `conversation_id`로 연결되는가

---

## 참고 코드 위치

- 그래프 렌더/상호작용: `src/components/HistoryGraphMvp.jsx`
- 히스토리 목록/상세/매핑: `src/pages/HistoryPage.tsx`