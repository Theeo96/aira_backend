# server.py / run_server.py Change Log

ì´ ë¬¸ì„œëŠ” `backend/server.py`, `backend/run_server.py` ë³€ê²½ ì‹œì ë§ˆë‹¤
"ì–´ëŠ ë¶€ë¶„ì„ ì™œ, ì–´ë–¤ ê¸°ëŠ¥ì„ ìœ„í•´ ìˆ˜ì •í–ˆëŠ”ì§€"ë¥¼ ê¸°ë¡í•©ë‹ˆë‹¤.

## 2026-02-13

### ëŒ€ìƒ íŒŒì¼
- `backend/run_server.py`

### ë³€ê²½ ì´ìœ 
- Windows í™˜ê²½ì—ì„œ ë©€í‹° ì›Œì»¤ ì‹¤í–‰ ì‹œ `WinError 5`ë¡œ ì„œë²„ê°€ ë°”ë¡œ ì¢…ë£Œë˜ëŠ” ë¬¸ì œë¥¼ ì™„í™”í•˜ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- ê¸°ë³¸ ì›Œì»¤ ìˆ˜ ê²°ì • ë¡œì§ ìˆ˜ì •:
  - Windows(`os.name == "nt"`)ì—ì„œëŠ” ê¸°ë³¸ê°’ `workers=1`
  - ê·¸ ì™¸ OSì—ì„œëŠ” `cpu_count()` ê¸°ë°˜
- `UVICORN_WORKERS` í™˜ê²½ë³€ìˆ˜ë¡œ ì›Œì»¤ ìˆ˜ ì˜¤ë²„ë¼ì´ë“œ ê°€ëŠ¥í•˜ë„ë¡ ì¶”ê°€
- `--reload` ëª¨ë“œì¼ ë•ŒëŠ” ê¸°ì¡´ì²˜ëŸ¼ `workers=1` ê°•ì œ ìœ ì§€

### ê¸°ëŠ¥ ëª©ì 
- `http://localhost:8000` ë°±ì—”ë“œ ê¸°ë™ ì•ˆì •ì„± í™•ë³´
- ìš´ì˜/ê°œë°œ í™˜ê²½ë³„ ì›Œì»¤ ì œì–´ ìœ ì—°ì„± í™•ë³´

## 2026-02-13 (Seoul module ë°˜ì˜ ìž‘ì—…)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`
- `backend/run_server.py`

### ë³€ê²½ ì—¬ë¶€
- ì—†ìŒ

### ë©”ëª¨
- `seoul_info_module`ëŠ” `backend/modules/seoul_info_module.py`ë¡œ ë…ë¦½ ì¶”ê°€í•¨.
- í•µì‹¬ ì„œë²„ ì—”íŠ¸ë¦¬(`server.py`, `run_server.py`) ìˆ˜ì •ì€ í†µí•© ì‹œì ê¹Œì§€ ë³´ë¥˜.

## 2026-02-13 (Seoul module ì‹¤ì œ ì—°ê²°)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ê¸°ì¡´ `/ws/audio` ì‹¤ì‹œê°„ ìŒì„± ë£¨í”„ë¥¼ ê±´ë“œë¦¬ì§€ ì•Šê³ , `seoul_info_module` ê¸°ëŠ¥ì„ ì¦‰ì‹œ ì‚¬ìš©í•  ìˆ˜ ìžˆëŠ” ìµœì†Œ í†µí•© ì§€ì ì„ ë§Œë“¤ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- import ì¶”ê°€:
  - `Body` from `fastapi`
  - `build_seoul_info_packet`, `build_speech_summary` from `modules.seoul_info_module`
- ì‹ ê·œ ì—”ë“œí¬ì¸íŠ¸ ì¶”ê°€:
  - `POST /api/seoul-info/normalize`
  - ìš”ì²­ ë°”ë””ì—ì„œ `voicePayload`, `odsayPayload`ë¥¼ ë°›ì•„ íŒ¨í‚· ì •ê·œí™” ë° ë°œí™” ìš”ì•½ ìƒì„± í›„ ë°˜í™˜
  - ì‘ë‹µ êµ¬ì¡°:
    - `packet`: ì •ê·œí™” ê²°ê³¼
    - `speechSummary`: ì‚¬ìš©ìž ë°œí™”ìš© ìš”ì•½ ë¬¸ìž¥

### ê¸°ëŠ¥ ëª©ì 
- ì™¸ë¶€/í”„ë¡ íŠ¸ì—ì„œ ìˆ˜ì§‘í•œ ì„œìš¸ ê´€ë ¨ raw payloadë¥¼ ì„œë²„ì—ì„œ ì¼ê´€ëœ ìŠ¤í‚¤ë§ˆë¡œ ì •ê·œí™”
- ì •ê·œí™” ê²°ê³¼ ê¸°ë°˜ TTS/ì‘ë‹µìš© ìš”ì•½ ë¬¸ìž¥ì„ ì¦‰ì‹œ ìƒì„± ê°€ëŠ¥í•˜ê²Œ í•¨

## 2026-02-13 (ìŒì„± ì‘ë‹µ ìŠ¤íƒ€ì¼ ì¡°ì •)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ìŒì„± ëª¨ë¸ì´ ì •ë³´ë¥¼ í•„ë“œ ë‚˜ì—´ ë°©ì‹ìœ¼ë¡œ ì½ì§€ ì•Šê³ , ì‚¬ìš©ìžì—ê²Œ ì¹œê·¼í•˜ê³  ìš”ì•½ëœ ë°©ì‹ìœ¼ë¡œ ì „ë‹¬ë˜ë„ë¡ ì‘ë‹µ ìŠ¤íƒ€ì¼ì„ ê°•ì œí•˜ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- `system_instruction` ê¸°ë³¸ ë¬¸êµ¬ë¥¼ í™•ìž¥:
  - raw ë°ì´í„°/í•„ë“œ ë¤í”„ ê¸ˆì§€
  - ìžì—°ìŠ¤ëŸ¬ìš´ í•œêµ­ì–´ êµ¬ì–´ì²´ ìš”ì•½
  - í•µì‹¬ ì •ë³´ ìš°ì„  ì „ë‹¬
  - ì •ë³´ê°€ ë§Žìœ¼ë©´ ì§§ì€ ê°œìš” + í›„ì† ì§ˆë¬¸ 1ê°œ

### ê¸°ëŠ¥ ëª©ì 
- ì‹¤ì œ ìŒì„± ì‘ë‹µ í’ˆì§ˆ ê°œì„  (ê°€ë…ì„±/ì²­ì·¨ì„±)
- ë™ì¼ ë°ì´í„°ë¼ë„ ì‚¬ìš©ìž ì¹œí™”ì ì¸ ì „ë‹¬ ë°©ì‹ìœ¼ë¡œ ì¼ê´€í™”

## 2026-02-13 (/ws/audio ì„œìš¸ ì»¨í…ìŠ¤íŠ¸ ì—°ê²°)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ì„œìš¸ ì •ë³´ ëª¨ë“ˆ ê²°ê³¼ë¥¼ ì‹¤ì œ ìŒì„± ëŒ€í™” ê²½ë¡œ(`/ws/audio`)ì—ë„ ë°˜ì˜í•˜ê¸° ìœ„í•´.
- ê¸°ì¡´ ì˜¤ë””ì˜¤ ìŠ¤íŠ¸ë¦¬ë° êµ¬ì¡°ë¥¼ ìœ ì§€í•˜ë©´ì„œ ìµœì†Œí•œì˜ ìž…ë ¥ í™•ìž¥ìœ¼ë¡œ ì—°ê²°í•˜ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- WebSocket ì¿¼ë¦¬ íŒŒë¼ë¯¸í„° `seoul_summary` ìˆ˜ì‹  ì¶”ê°€
- `system_instruction` ìƒì„± ì‹œ, `seoul_summary`ê°€ ìžˆìœ¼ë©´ ì»¨í…ìŠ¤íŠ¸ ë¸”ë¡ìœ¼ë¡œ ì£¼ìž…:
  - `[SEOUL SUMMARY CONTEXT] ...`
  - ìžì—°ìŠ¤ëŸ¬ìš´ ì„¤ëª… ìš°ì„  ì§€ì‹œ

### ê¸°ëŠ¥ ëª©ì 
- ìŒì„± ì‘ë‹µì´ ì„œìš¸ ì •ë³´ ë§¥ë½ì„ ë°˜ì˜í•˜ë„ë¡ ì—°ê²°
- `/api/seoul-info/normalize` ê²°ê³¼ë¥¼ `/ws/audio` ëŒ€í™” í’ˆì§ˆ í–¥ìƒì— ìž¬ì‚¬ìš© ê°€ëŠ¥í•˜ê²Œ í•¨

## 2026-02-13 (/ws/audio ì»¨í…ìŠ¤íŠ¸ ëˆ„ë½ ëŒ€ì‘ ê°•í™”)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- í”„ë¡ íŠ¸ì—ì„œ `seoul_summary`ë¥¼ ì „ë‹¬í•˜ì§€ ì•ŠëŠ” ê²½ìš° ëª¨ë¸ì´ ê¸°ëŠ¥ ë¶€ìž¬ì²˜ëŸ¼ ë‹µí•˜ëŠ” ë¬¸ì œë¥¼ ì¤„ì´ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- `seoul_summary` ì¿¼ë¦¬ê°’ì´ ì—†ìœ¼ë©´ `.env`ì˜ `SEOUL_SUMMARY`ë¥¼ fallbackìœ¼ë¡œ ì‚¬ìš©
- `system_instruction`ì— ê±°ì ˆí˜• ë‹µë³€ ì–µì œ ê·œì¹™ ì¶”ê°€:
  - "I cannot access that data"ë¥˜ ë¬¸êµ¬ ì§€ì–‘
  - ì»¨í…ìŠ¤íŠ¸ê°€ ë¶€ë¶„ì ì¼ ë•Œë„ ê°€ì • ê¸°ë°˜ìœ¼ë¡œ ë„ì›€ë˜ëŠ” ë‹µë³€ + í™•ì¸ ì§ˆë¬¸ 1ê°œ

### ê¸°ëŠ¥ ëª©ì 
- ì„œìš¸ ì •ë³´ ì»¨í…ìŠ¤íŠ¸ ëˆ„ë½ ìƒí™©ì—ì„œë„ ì‚¬ìš©ìž ì²´ê° ì‘ë‹µ í’ˆì§ˆ ìœ ì§€
- ìŒì„± ì‘ë‹µì´ "ëª»í•¨" ìœ„ì£¼ë¡œ ë¹ ì§€ëŠ” í˜„ìƒ ì™„í™”

## 2026-02-13 (ê¸°ë³¸ ì»¨í…ìŠ¤íŠ¸ fallback ì œê±°)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- í…ŒìŠ¤íŠ¸ ëª©í‘œê°€ "ì‚¬ìš©ìž ìŒì„± ê¸°ë°˜ ë™ìž‘ ê²€ì¦"ì´ë¯€ë¡œ, `.env` ê¸°ë³¸ ì»¨í…ìŠ¤íŠ¸ ì£¼ìž…ì´ ê²°ê³¼ë¥¼ ì˜¤ì—¼ì‹œí‚¤ì§€ ì•Šë„ë¡ ì œê±°.

### ë³€ê²½ ë‚´ìš©
- `/ws/audio`ì—ì„œ `seoul_summary` ë¯¸ì „ë‹¬ ì‹œ `.env`ì˜ `SEOUL_SUMMARY`ë¥¼ ì‚¬ìš©í•˜ëŠ” fallback ë¡œì§ ì‚­ì œ.
- ì´ì œ ì„œìš¸ ì»¨í…ìŠ¤íŠ¸ëŠ” í´ë¼ì´ì–¸íŠ¸ê°€ ëª…ì‹œì ìœ¼ë¡œ ì „ë‹¬í•œ ê²½ìš°ì—ë§Œ ì‚¬ìš©ë¨.

### ê¸°ëŠ¥ ëª©ì 
- ìŒì„± ìž…ë ¥ ê¸°ë°˜ í…ŒìŠ¤íŠ¸ì˜ ìˆœìˆ˜ì„± í™•ë³´
- ê¸°ë³¸ê°’ ì£¼ìž…ìœ¼ë¡œ ì¸í•œ ì˜¤íƒ/ê³¼ì í•© ì‘ë‹µ ë°©ì§€

## 2026-02-13 (ì¢Œí‘œ/ì—´ì°¨ ë„ì°©ì •ë³´ ì‹¤ì—°ë™)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`
- `temp_front/app/page.tsx`

### ë³€ê²½ ì´ìœ 
- ê¸°ì¡´ì—ëŠ” `seoul_info_module` ì •ê·œí™” ë¡œì§ë§Œ ìžˆê³ , ì‹¤ì œ ì¢Œí‘œ ìˆ˜ì§‘ ë° ì‹¤ì‹œê°„ ì—´ì°¨ ë„ì°© API í˜¸ì¶œ ê²½ë¡œê°€ ì—°ê²°ë˜ì§€ ì•Šì•„
  "í˜„ìž¬ ì¢Œí‘œ/ì—´ì°¨ ë„ì°©ì‹œê°„ì„ ëª» ë°›ëŠ”" ì¦ìƒì´ ë°œìƒí–ˆê¸° ë•Œë¬¸.

### ë³€ê²½ ë‚´ìš©
- `backend/server.py`
  - `GET /api/seoul-info/live` ì‹ ê·œ ì¶”ê°€
  - ìž…ë ¥: `lat`, `lng`, `station`(optional)
  - ì²˜ë¦¬:
    - ì¢Œí‘œê°€ ìžˆìœ¼ë©´ ODSAY `pointSearch`ë¡œ ì¸ê·¼ ì—­ ì¶”ì •
    - ì¶”ì •/ìž…ë ¥ëœ ì—­ëª…ìœ¼ë¡œ ì„œìš¸ì‹œ `realtimeStationArrival` í˜¸ì¶œ
    - ìŒì„± ì „ë‹¬ìš© ìš”ì•½(`speechSummary`) + ì›ë³¸ ë„ì°©ëª©ë¡(`arrivals`) ë°˜í™˜
- `temp_front/app/page.tsx`
  - Connect ì‹œ ë¸Œë¼ìš°ì € geolocationìœ¼ë¡œ í˜„ìž¬ ì¢Œí‘œ íšë“ ì‹œë„
  - `/api/seoul-info/live` í˜¸ì¶œí•´ `speechSummary`ë¥¼ ë°›ì•„ `/ws/audio` ì¿¼ë¦¬ì˜ `seoul_summary`ë¡œ ì£¼ìž…
  - geolocation/API ì‹¤íŒ¨ ì‹œ ê¸°ì¡´ì²˜ëŸ¼ ë¡œì»¬ ì €ìž¥ëœ `seoul_summary` fallback

### ê¸°ëŠ¥ ëª©ì 
- ì‚¬ìš©ìž ì‹¤ì œ í˜„ìž¬ ìœ„ì¹˜ ê¸°ë°˜ì˜ ì—­/ë„ì°©ì •ë³´ë¥¼ ìŒì„± ëª¨ë¸ ì»¨í…ìŠ¤íŠ¸ë¡œ ìžë™ ë°˜ì˜
- "ëª»í•œë‹¤" ì‘ë‹µ ëŒ€ì‹ , ì‹¤ì‹œê°„ ë°ì´í„° ê¸°ë°˜ ì•ˆë‚´ ê°€ëŠ¥ì„± í™•ë³´

## 2026-02-13 (ì‹¤ì‹œê°„ ì‘ë‹µ ì‹¤íŒ¨ ì™„í™”: ì¤‘ë³µ ì—°ê²°/ì»¨í…ìŠ¤íŠ¸ ìš°ì„ ìˆœìœ„ ê°•í™”)

### ëŒ€ìƒ íŒŒì¼
- `temp_front/app/page.tsx`
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ë¡œê·¸ìƒ `/ws/audio`ê°€ ì¤‘ë³µ ì—°ê²°ë˜ë©° ì—¬ëŸ¬ ì„¸ì…˜ì´ ë™ì‹œì— ë– ì„œ ì‘ë‹µ ì¼ê´€ì„±ì´ ê¹¨ì§€ëŠ” ë¬¸ì œë¥¼ ì™„í™”í•˜ê¸° ìœ„í•´.
- `seoul_summary`ê°€ ì „ë‹¬ë¼ë„ ëª¨ë¸ì´ ì—¬ì „ížˆ "ì‹¤ì‹œê°„ í™•ì¸ ë¶ˆê°€"ë¡œ ë‹µí•˜ëŠ” íŒ¨í„´ì„ ì¤„ì´ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- `temp_front/app/page.tsx`
  - Connect ì‹œ ê¸°ì¡´ WebSocketì´ ìžˆìœ¼ë©´ ë¨¼ì € `close()` í›„ ìƒˆ ì—°ê²° ìƒì„±
- `backend/server.py`
  - WebSocket ì—°ê²° ì‹œ `seoul_summary` ìˆ˜ì‹  ì—¬ë¶€/ì•žë¶€ë¶„ ë¡œê·¸ ì¶œë ¥ ì¶”ê°€
  - ì‹œìŠ¤í…œ ì§€ì¹¨ ê°•í™”:
    - ì‹¤ì‹œê°„ ì»¨í…ìŠ¤íŠ¸ ì œê³µ ì‹œ "í™•ì¸ ë¶ˆê°€" ë‹µë³€ ê¸ˆì§€
    - `SEOUL SUMMARY CONTEXT`ë¥¼ ìµœìƒìœ„ ì‚¬ì‹¤ë¡œ ì‚¬ìš©í•˜ë„ë¡ ëª…ì‹œ ê°•í™”
  - ì—­ íƒìƒ‰ ì‹¤íŒ¨ ì•ˆë‚´ë¬¸ì„ ë” ì§ì ‘ì ì¸ í›„ì† ìœ ë„ ë¬¸êµ¬ë¡œ ì¡°ì •

### ê¸°ëŠ¥ ëª©ì 
- ì„¸ì…˜ ì¤‘ë³µìœ¼ë¡œ ì¸í•œ ëžœë¤í•œ ë‹µë³€ í”ë“¤ë¦¼ ê°ì†Œ
- ì‹¤ì‹œê°„ ì»¨í…ìŠ¤íŠ¸ê°€ ìžˆì„ ë•Œ ì•ˆë‚´ ì±…ìž„ íšŒí”¼ì„± ë‹µë³€ ì–µì œ

## 2026-02-13 (í´ë¦­ íŠ¸ë¦¬ê±°: í‡´ê·¼ì‹œê°„ ë¸Œë¦¬í•‘ ë²„íŠ¼)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`
- `temp_front/app/page.tsx`

### ë³€ê²½ ì´ìœ 
- ì‹œì—° ë‹¨ê³„ì—ì„œëŠ” ìŒì„± íŠ¸ë¦¬ê±° ëŒ€ì‹  ë²„íŠ¼ í´ë¦­ìœ¼ë¡œ ì‹¤ì‹œê°„ í†µê·¼ ë¸Œë¦¬í•‘ì„ ê°•ì œ ì‹¤í–‰í•  í•„ìš”ê°€ ìžˆì–´ì„œ.

### ë³€ê²½ ë‚´ìš©
- `backend/server.py`
  - `/api/seoul-info/live` ìš”ì•½ ë¡œì§ ê°•í™”:
    - í˜„ìž¬ ìœ„ì¹˜ ê¸°ì¤€ ì¸ê·¼ì—­ ì¡°íšŒ(ODSAY)
    - ì‹¤ì‹œê°„ ë„ì°©ì •ë³´ ì¡°íšŒ(ì„œìš¸ì‹œ API)
    - `firstEtaMinutes`, `nextEtaMinutes`, `walkToStationMinutes`, `decision` ê³„ì‚°
    - ë¸Œë¦¬í•‘ ë¬¸ìž¥ì„ "ì´ë²ˆ ì—´ì°¨/ë‹¤ìŒ ì—´ì°¨ + ë„ë³´ ì‹œê°„ + íƒ‘ìŠ¹ íŒë‹¨" í˜•íƒœë¡œ ìƒì„±
- `temp_front/app/page.tsx`
  - `í‡´ê·¼ì‹œê°„ ë¸Œë¦¬í•‘` ë²„íŠ¼ ì¶”ê°€ (ë¹„ì—°ê²°/ì—°ê²° ìƒíƒœ ëª¨ë‘ í‘œì‹œ)
  - ë²„íŠ¼ í´ë¦­ ì‹œ geolocation + `/api/seoul-info/live` í˜¸ì¶œ
  - ìƒì„±ëœ `speechSummary`ë¥¼ `localStorage.seoul_summary`ì— ì €ìž¥ í›„ WS ìž¬ì—°ê²°
  - ë¸Œë¦¬í•‘ ë¬¸ìž¥ì„ ëŒ€í™”ì°½ì—ë„ í‘œì‹œí•´ ì¦‰ì‹œ í™•ì¸ ê°€ëŠ¥

### ê¸°ëŠ¥ ëª©ì 
- ë°ëª¨ ì¤‘ í•œ ë²ˆì˜ í´ë¦­ìœ¼ë¡œ ì‹¤ì‹œê°„ í†µê·¼ ë¸Œë¦¬í•‘ ì»¨í…ìŠ¤íŠ¸ ìƒì„±
- ìŒì„± ëª¨ë¸ì´ ìš”ì²­í•œ í˜•ì‹(ì´ë²ˆ/ë‹¤ìŒ ì—´ì°¨ íŒë‹¨)ìœ¼ë¡œ ë‹µë³€í•˜ë„ë¡ ì»¨í…ìŠ¤íŠ¸ í’ˆì§ˆ í–¥ìƒ

## 2026-02-13 (ê·¼ì²˜ ì—­ íƒìƒ‰ ì‹¤íŒ¨ ëŒ€ì‘ ê°•í™”)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ë¡œê·¸ì—ì„œ `/api/seoul-info/live`ëŠ” 200 ì‘ë‹µì´ì§€ë§Œ, ODSAY ê·¼ì²˜ ì—­ íƒìƒ‰ ì‹¤íŒ¨ë¡œ
  `seoul_summary`ê°€ "ì—­ì„ ì°¾ì§€ ëª»í–ˆì–´ìš”"ë¡œ ê³ ì •ë˜ëŠ” ë¬¸ì œê°€ ë°˜ë³µë˜ì–´ì„œ.

### ë³€ê²½ ë‚´ìš©
- ODSAY ì‘ë‹µ íŒŒì‹± ë¡œì§ í™•ìž¥:
  - `result.station` ì™¸ì— `stationInfo`, `stations` ë“± ë³€í˜• í‚¤ ëŒ€ì‘
  - ì—­ëª…/ì¢Œí‘œ í‚¤(`stationName`, `stationNm`, `x/y`, `gpsX/gpsY`) ìœ ì—° íŒŒì‹±
- ODSAY íƒìƒ‰ ì „ëžµ í™•ìž¥:
  - ë°˜ê²½ 800m -> 1500m -> 3000m ìˆœì°¨ ìž¬ì‹œë„
  - `stationClass=2` í¬í•¨/ë¯¸í¬í•¨ ëª¨ë‘ ì‹œë„
- ì‹¤íŒ¨ ì›ì¸ ì¶”ì ì„ ìœ„í•œ ì„œë²„ ë¡œê·¸ ê°•í™”:
  - ODSAY error/result error ì¶œë ¥
  - ìµœì¢… íƒìƒ‰ ì‹¤íŒ¨ ì‹œ ì¢Œí‘œ í¬í•¨ ë¡œê·¸ ì¶œë ¥

### ê¸°ëŠ¥ ëª©ì 
- ë™ì¼ ì¢Œí‘œì—ì„œ ì—­ íƒìƒ‰ ì„±ê³µë¥  í–¥ìƒ
- ì‹¤íŒ¨ ì‹œ ì›ì¸ íŒŒì•… ê°€ëŠ¥í•œ ë¡œê·¸ í™•ë³´ë¡œ ë””ë²„ê¹… ì‹œê°„ ë‹¨ì¶•

## 2026-02-13 (ë¸Œë¦¬í•‘ ë²„íŠ¼ í†µì‹  ì•ˆì •í™” + ETA ë³´ì •)

### ëŒ€ìƒ íŒŒì¼
- `temp_front/app/page.tsx`
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- `í‡´ê·¼ì‹œê°„ ë¸Œë¦¬í•‘` í´ë¦­ ì‹œ ê¸°ì¡´/ì‹ ê·œ ì†Œì¼“ ì´ë²¤íŠ¸ ë ˆì´ìŠ¤ë¡œ ì—°ê²° ìƒíƒœê°€ í”ë“¤ë¦¬ëŠ” ë¬¸ì œë¥¼ ì¤„ì´ê¸° ìœ„í•´.
- ë„ì°©ì •ë³´ íŒŒì‹±ì—ì„œ `0ë¶„`ì´ ê³¼ë„í•˜ê²Œ ë…¸ì¶œë˜ì–´ ì‹ ë¢°ë„ê°€ ë–¨ì–´ì§€ëŠ” ë¬¸ì œë¥¼ ì™„í™”í•˜ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- `temp_front/app/page.tsx`
  - WebSocket ì´ë²¤íŠ¸ í•¸ë“¤ëŸ¬ì—ì„œ í˜„ìž¬ í™œì„± ì†Œì¼“ ì¸ìŠ¤í„´ìŠ¤ì¸ì§€ í™•ì¸ í›„ ìƒíƒœ ê°±ì‹ 
    - êµ¬ ì†Œì¼“ì˜ ì§€ì—° `onclose`ê°€ ì‹ ê·œ ì†Œì¼“ ìƒíƒœë¥¼ ë®ì–´ì“°ì§€ ì•Šë„ë¡ ì²˜ë¦¬
  - `í‡´ê·¼ì‹œê°„ ë¸Œë¦¬í•‘` í´ë¦­ ì‹œ ì´ë¯¸ ì—°ê²° ì¤‘ì´ë©´ ìž¬ì—°ê²°í•˜ì§€ ì•Šê³  ë¸Œë¦¬í•‘ë§Œ ê°±ì‹ 
- `backend/server.py`
  - ETA íŒŒì‹± ë³´ì •:
    - `barvlDt > 0` ìš°ì„  ì‚¬ìš©
    - `0ë¶„` ì²˜ë¦¬ëŠ” ì²« ì—´ì°¨ì—ëŠ” í—ˆìš©, ë‹¤ìŒ ì—´ì°¨ì—ëŠ” ë³´ìˆ˜ì ìœ¼ë¡œ ì œí•œ
    - `next_eta <= first_eta`ì¸ ë¹„ì •ìƒ ì¼€ì´ìŠ¤ëŠ” ë¬´íš¨ ì²˜ë¦¬
  - ë‹¤ìŒ ì—´ì°¨ ETAê°€ ë¶ˆí™•ì‹¤í•  ë•Œë„ ë¬¸ìž¥ì„ ìžì—°ìŠ¤ëŸ½ê²Œ ìƒì„±í•˜ë„ë¡ ë¶„ê¸° ì¶”ê°€

### ê¸°ëŠ¥ ëª©ì 
- ë¸Œë¦¬í•‘ ë²„íŠ¼ í´ë¦­ ì‹œ í†µì‹  ëŠê¹€ ì²´ê° ìµœì†Œí™”
- "ì´ë²ˆ/ë‹¤ìŒ ì—´ì°¨" ë‚¨ì€ ì‹œê°„ ì•ˆë‚´ì˜ í˜„ì‹¤ì„± í–¥ìƒ

## 2026-02-13 (ë²„íŠ¼ ë™ìž‘ ë¶„ë¦¬ + ë¸Œë¦¬í•‘ ì¦‰ì‹œ ìŒì„± ì¶œë ¥)

### ëŒ€ìƒ íŒŒì¼
- `temp_front/app/page.tsx`

### ë³€ê²½ ì´ìœ 
- `í‡´ê·¼ì‹œê°„ ë¸Œë¦¬í•‘` í´ë¦­ ì‹œ Connect ë™ìž‘ê³¼ ì„žì—¬ ë³´ì´ëŠ” ì²´ê°ì„ ì œê±°í•˜ê¸° ìœ„í•´.
- ë¸Œë¦¬í•‘ ê²°ê³¼ê°€ í…ìŠ¤íŠ¸ë§Œ í‘œì‹œë˜ê³  ìŒì„± ì‘ë‹µì´ ì—†ëŠ” ë¬¸ì œë¥¼ í•´ê²°í•˜ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- `triggerCommuteBriefing`ì—ì„œ WebSocket ì—°ê²°/ìž¬ì—°ê²° í˜¸ì¶œ ì œê±°
  - ì´ì œ ë¸Œë¦¬í•‘ ë²„íŠ¼ì€ "ì‹¤ì‹œê°„ ì¡°íšŒ + ìš”ì•½ ìƒì„±"ë§Œ ìˆ˜í–‰
- ë¸Œë¦¬í•‘ ì™„ë£Œ ì‹œ ë¸Œë¼ìš°ì € `speechSynthesis`ë¡œ ì¦‰ì‹œ ìŒì„± ì¶œë ¥ ì¶”ê°€
  - `ko-KR` ì„¤ì •ìœ¼ë¡œ ìš”ì•½ ë¬¸ìž¥ì„ ë°”ë¡œ ì½ì–´ì¤Œ

### ê¸°ëŠ¥ ëª©ì 
- ë²„íŠ¼ ê°„ ì—­í•  ë¶„ë¦¬ ëª…í™•í™” (Connect vs Briefing)
- ë¸Œë¦¬í•‘ ë²„íŠ¼ ë‹¨ë… í´ë¦­ ì‹œì—ë„ ìŒì„± í”¼ë“œë°± ë³´ìž¥

## 2026-02-13 (ë¸Œë¦¬í•‘ ë²„íŠ¼ ì œê±° + ë¹„í—ˆìš© ì¶”ì • ì‘ë‹µ ì°¨ë‹¨)

### ëŒ€ìƒ íŒŒì¼
- `temp_front/app/page.tsx`
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ìŒì„± í…ŒìŠ¤íŠ¸ íë¦„ ë‹¨ìˆœí™”ë¥¼ ìœ„í•´ `í‡´ê·¼ì‹œê°„ ë¸Œë¦¬í•‘` ë²„íŠ¼ì„ ì œê±°í•˜ê¸° ìœ„í•´.
- ì‚¬ìš©ìžê°€ ì§€ì í•œ "ìµœë‹¨ê²½ë¡œ/ë°©í–¥/ë‚ ì”¨/ëŒ€ê¸°ì§ˆì„ ì§€ì–´ë‚´ëŠ” ë‹µë³€"ì„ ì¤„ì´ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- `temp_front/app/page.tsx`
  - `í‡´ê·¼ì‹œê°„ ë¸Œë¦¬í•‘` ë²„íŠ¼ UI ì œê±° (ë¹„ì—°ê²°/ì—°ê²° ìƒíƒœ ëª¨ë‘)
  - ê´€ë ¨ í•¸ë“¤ëŸ¬(`triggerCommuteBriefing`) ì œê±°
  - ìŒì„± í…ŒìŠ¤íŠ¸ëŠ” `Connect` + `Start Speaking` íë¦„ìœ¼ë¡œë§Œ ë™ìž‘
- `backend/server.py`
  - ì‹¤ì‹œê°„ ë¸Œë¦¬í•‘ ë¬¸êµ¬ì—ì„œ "ì§‘ìœ¼ë¡œ ê°€ì‹œë ¤ë©´ ... íƒ€ì‹œë©´ ë¼ìš”" ê°™ì€ ì¶”ì •ì„± í‘œí˜„ ì œê±°
  - `system_instruction` ê°•í™”:
    - live contextì— ì—†ëŠ” ì‚¬ì‹¤ì€ ë§í•˜ì§€ ì•Šê¸°
    - ë°ì´í„° ë¶€ì¡± ì‹œ ë¶€ì¡±í•œ í•­ëª©ì„ ëª…ì‹œí•˜ê³  í™•ì¸ ì§ˆë¬¸ 1ê°œ
    - ìµœë‹¨ê²½ë¡œ/ë°©í–¥/ETA/ë‚ ì”¨/ëŒ€ê¸°ì§ˆ ê°’ ìž„ì˜ ìƒì„± ê¸ˆì§€

### ê¸°ëŠ¥ ëª©ì 
- ìŒì„± ë°ëª¨ íë¦„ ë‹¨ìˆœí™”
- API ë¯¸ì—°ë™ ë°ì´í„°ì— ëŒ€í•œ í™˜ê°(hallucination) ì‘ë‹µ ì–µì œ

## 2026-02-13 (ë²„ìŠ¤ ì‘ë‹µ ê·œì¹™ ì œí•œ: ì •ë¥˜ìž¥ëª…+ë„ë³´ì‹œê°„ë§Œ)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ë²„ìŠ¤ê°€ ë” ë¹ ë¥¸ ìƒí™©ì—ì„œë„ ì§€í•˜ì²  ETA/ë°©ë©´ ì •ë³´ë¥¼ ì„žì–´ ë§í•´ ì˜¤ë‹µì´ ë°œìƒí•˜ëŠ” ë¬¸ì œë¥¼ ì¤„ì´ê¸° ìœ„í•´.
- ì‚¬ìš©ìžê°€ ìš”ì²­í•œ ì •ì±…: "ë²„ìŠ¤ê°€ ë‚˜ì˜¤ë©´ ì •ë¥˜ìž¥ ì´ë¦„ + ê±¸ì–´ì„œ ëª‡ ë¶„"ë§Œ ì•ˆë‚´.

### ë³€ê²½ ë‚´ìš©
- ODSAY ê·¼ì²˜ í¬ì¸íŠ¸ íƒìƒ‰ í•¨ìˆ˜ í™•ìž¥:
  - `stationClass=2`(ì§€í•˜ì² ) ì™¸ì— `stationClass=1`(ë²„ìŠ¤ì •ë¥˜ìž¥) ì¡°íšŒ ì¶”ê°€
  - ë²„ìŠ¤ì •ë¥˜ìž¥ëª…/ì¢Œí‘œë¥¼ ë°›ì•„ ë„ë³´ ì‹œê°„ ì¶”ì •(`walkToBusStopMinutes`) ê³„ì‚°
- `/api/seoul-info/live` ì‘ë‹µì— ë²„ìŠ¤ í•„ë“œ ì¶”ê°€:
  - `busStopName`
  - `walkToBusStopMinutes`
- ë¸Œë¦¬í•‘ ë¬¸êµ¬ì— ë²„ìŠ¤ ë¬¸ìž¥ ì¶”ê°€:
  - ë²„ìŠ¤ ì´ìš© ì‹œ ê°€ìž¥ ê°€ê¹Œìš´ ì •ë¥˜ìž¥ëª… + ë„ë³´ ë¶„ë§Œ ì•ˆë‚´
- ì‹œìŠ¤í…œ ì§€ì¹¨ ê°•í™”:
  - ë²„ìŠ¤ ê´€ë ¨ ë°œí™” ì‹œ ì •ë¥˜ìž¥ëª…/ë„ë³´ì‹œê°„ë§Œ í—ˆìš©
  - ë²„ìŠ¤ ë…¸ì„ /ë²„ìŠ¤ ETA/ë²„ìŠ¤ ë°©ë©´ì€ live contextì— ëª…ì‹œë˜ì§€ ì•Šìœ¼ë©´ ê¸ˆì§€

### ê¸°ëŠ¥ ëª©ì 
- ë²„ìŠ¤/ì§€í•˜ì²  ì»¨í…ìŠ¤íŠ¸ í˜¼í•©ìœ¼ë¡œ ì¸í•œ ìž˜ëª»ëœ ì•ˆë‚´ ê°ì†Œ
- ì‚¬ìš©ìž ìš”ì²­ ì •ì±…ì— ë§žëŠ” ë³´ìˆ˜ì  ë²„ìŠ¤ ì•ˆë‚´ ê³ ì •

## 2026-02-13 (ë©€í‹°ëª¨ë‹¬ ê²½ë¡œ ìš”ì•½ ê°•í™”: ë²„ìŠ¤ë²ˆí˜¸ + ì§€í•˜ì²  ìƒì„¸ + ë‚ ì”¨/ëŒ€ê¸°ì§ˆ)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ì‚¬ìš©ìž ìš”êµ¬ì‚¬í•­ í™•ìž¥:
  - ë²„ìŠ¤ëŠ” ì •ë¥˜ìž¥+ë„ë³´ë¿ ì•„ë‹ˆë¼ íƒ‘ìŠ¹ ë²„ìŠ¤ ë²ˆí˜¸ê¹Œì§€ í•„ìš”
  - ì§€í•˜ì² ì€ ìµœë‹¨ ê²½ë¡œ ê¸°ì¤€ìœ¼ë¡œ ë°©ë©´/ë„ì°©/ë‹¤ìŒì—´ì°¨/ë„ë³´ íŒë‹¨ê¹Œì§€ í•„ìš”
  - ë‚ ì”¨/ëŒ€ê¸°ì§ˆ ë°˜ì˜ ì¶”ì²œ(ë¹„ ì˜¤ë©´ ë”°ë¦‰ì´ ë¹„ì¶”ì²œ) í•„ìš”

### ë³€ê²½ ë‚´ìš©
- í™˜ê²½ë³€ìˆ˜ ì¶”ê°€ ì‚¬ìš©:
  - `HOME_LAT`, `HOME_LNG` (ëª©ì ì§€ ì¢Œí‘œ; ì—†ìœ¼ë©´ ê²½ë¡œ ê¸°ë°˜ ì•ˆë‚´ ì œí•œ)
- API ì—°ë™ ì¶”ê°€/í™•ìž¥:
  - ODSAY `searchPubTransPathT`ë¡œ í˜„ìž¬ ìœ„ì¹˜ -> ëª©ì ì§€ ìµœë‹¨ ëŒ€ì¤‘êµí†µ ê²½ë¡œ ì¡°íšŒ
  - ODSAY ê²°ê³¼ì—ì„œ ì²« íƒ‘ìŠ¹ ìˆ˜ë‹¨(ë²„ìŠ¤/ì§€í•˜ì² ), íƒ‘ìŠ¹ ì§€ì , ë°©ë©´, ë²„ìŠ¤ë²ˆí˜¸ ì¶”ì¶œ
  - ì„œìš¸ ì§€í•˜ì²  ì‹¤ì‹œê°„ ë„ì°© APIë¡œ ì¶œë°œì—­ ë„ì°©ì‹œê°„(í˜„ìž¬/ë‹¤ìŒ ì—´ì°¨) ê²°í•©
  - Open-Meteo(ë‚ ì”¨), Open-Meteo Air Quality(ëŒ€ê¸°ì§ˆ) ì¡°íšŒ ê²°í•©
- ìš”ì•½ ë¡œì§ ê°•í™” (`_build_live_seoul_summary` ì „ë©´ êµì²´):
  - ë²„ìŠ¤ ì‹œìž‘ ê²½ë¡œ: ë²„ìŠ¤ë²ˆí˜¸ + íƒ‘ìŠ¹ì •ë¥˜ìž¥ + ë„ë³´ì‹œê°„ ì¤‘ì‹¬ ì•ˆë‚´
  - ì§€í•˜ì²  ì‹œìž‘ ê²½ë¡œ: ì¶œë°œì—­/ë°©ë©´/ë„ì°©ì‹œê°„/ë„ë³´ì‹œê°„/í˜„ìž¬ì—´ì°¨ vs ë‹¤ìŒì—´ì°¨ íŒë‹¨ ì•ˆë‚´
  - ë¹„ê°€ ì˜¤ë©´ ë”°ë¦‰ì´ ë¹„ì¶”ì²œ, ë¹„ê°€ ì—†ê³  ë„ë³´ê°€ ê¸¸ë©´ ë”°ë¦‰ì´ ëŒ€ì•ˆ ì–¸ê¸‰
- ë°˜í™˜ í•„ë“œ í™•ìž¥:
  - `busNumbers`, `firstMode`, `firstDirection`, `weather`, `air`, `homeConfigured` ë“±
- ì‹œìŠ¤í…œ ì§€ì¹¨ ì—…ë°ì´íŠ¸:
  - ì§€í•˜ì² /ë²„ìŠ¤ ì•ˆë‚´ì— í•„ìš”í•œ í•„ìˆ˜ í•­ëª©ì„ ë¼ì´ë¸Œ ì»¨í…ìŠ¤íŠ¸ ê¸°ë°˜ìœ¼ë¡œë§Œ ë°œí™”
  - ê°’ ìž„ì˜ ìƒì„± ê¸ˆì§€ ìœ ì§€

### ê¸°ëŠ¥ ëª©ì 
- ìš”ì²­í•œ ì„¤ëª… í¬ë§·(ë²„ìŠ¤ë²ˆí˜¸, ì§€í•˜ì²  ìƒì„¸ íŒë‹¨, ë‚ ì”¨ ë°˜ì˜ ì¶”ì²œ)ì„ ë°ì´í„° ê¸°ë°˜ìœ¼ë¡œ êµ¬í˜„
- í™˜ê°ì„± ì•ˆë‚´ë¥¼ ì¤„ì´ê³ , ì‹¤ì œ API ê°’ ì¤‘ì‹¬ì˜ ì‘ë‹µìœ¼ë¡œ ì •í•©ì„± í–¥ìƒ

## 2026-02-13 (ë§¤ ì§ˆë¬¸ ëª©ì ì§€ ê¸°ì¤€ ìž¬ê³„ì‚° + Connect ìžë™ ë¡œê·¸ ì œê±°)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`
- `temp_front/app/page.tsx`

### ë³€ê²½ ì´ìœ 
- ì‚¬ìš©ìžê°€ ëª…ì‹œí•œ ìš”êµ¬ì‚¬í•­: ëª©ì ì§€ë¥¼ `.env` ê³ ì •ê°’ì´ ì•„ë‹ˆë¼ "ë§¤ ì§ˆë¬¸(ìŒì„± ë°œí™”)ì˜ ëª©ì ì§€" ê¸°ì¤€ìœ¼ë¡œ ê³„ì‚°í•´ì•¼ í•¨.
- Connect ì‹œ ìžë™ìœ¼ë¡œ ëŒ€í™”ì°½ì— í‡´ê·¼ê¸¸ ë¡œê·¸ê°€ ì°ížˆëŠ” ë¶€ìž‘ìš© ì œê±° í•„ìš”.

### ë³€ê²½ ë‚´ìš©
- `temp_front/app/page.tsx`
  - Connect ì‹œ ì´ˆê¸° `/api/seoul-info/live` í˜¸ì¶œ ê²°ê³¼ë¥¼ ë” ì´ìƒ ëŒ€í™”ì°½(`setTranscripts`)ì— ìžë™ ê¸°ë¡í•˜ì§€ ì•Šë„ë¡ ì œê±°.
  - WebSocket ì—°ê²° ì‹œ `lat`, `lng`ë¥¼ ì¿¼ë¦¬ íŒŒë¼ë¯¸í„°ë¡œ ì „ë‹¬í•´ ì„œë²„ê°€ í„´ë³„ ìž¬ê³„ì‚°ì— í™œìš© ê°€ëŠ¥í•˜ë„ë¡ í™•ìž¥.
- `backend/server.py`
  - ì‚¬ìš©ìž STT í…ìŠ¤íŠ¸ì—ì„œ ëª©ì ì§€ í›„ë³´ë¥¼ ì¶”ì¶œí•˜ëŠ” í—¬í¼ ì¶”ê°€ (`_extract_destination_from_text`)
  - ëª©ì ì§€ ì—­ëª… -> ì¢Œí‘œ í•´ì„ í—¬í¼ ì¶”ê°€ (`_resolve_destination_coords_from_name`)
  - `/ws/audio` ì„¸ì…˜ì—ì„œ ì‚¬ìš©ìž ë°œí™”ê°€ ë“¤ì–´ì˜¬ ë•Œë§ˆë‹¤:
    - ëª©ì ì§€ ìƒíƒœ ê°±ì‹ 
    - ìµœì‹  ìœ„ì¹˜+ëª©ì ì§€ ê¸°ì¤€ ì‹¤ì‹œê°„ ìš”ì•½ ìž¬ê³„ì‚°
    - Gemini ì„¸ì…˜ì— ë™ì  ì»¨í…ìŠ¤íŠ¸ ì—…ë°ì´íŠ¸ íë¡œ ì£¼ìž…
  - ëª©ì ì§€ ì¢Œí‘œë¥¼ ìš°ì„  ì‚¬ìš©í•˜ê³ , ì—†ì„ ë•Œë§Œ ê¸°ì¡´ fallbackìœ¼ë¡œ ë™ìž‘í•˜ë„ë¡ ê²½ë¡œ ê³„ì‚° ìš°ì„ ìˆœìœ„ ì¡°ì •

### ê¸°ëŠ¥ ëª©ì 
- ë™ì¼ í†µí™” ì„¸ì…˜ ë‚´ì—ì„œë„ ì§ˆë¬¸ë§ˆë‹¤ ëª©ì ì§€ê°€ ë°”ë€Œë©´ ì¦‰ì‹œ ë°˜ì˜
- Connect ì§í›„ ë¶ˆí•„ìš”í•œ "í‡´ê·¼ê¸¸ ì•ˆë‚´ ë¡œê·¸" ìžë™ ì¶œë ¥ ì œê±°

## 2026-02-13 (gpt-4o-mini ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´í„° ì¶”ê°€: intent_router + tool_executor)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ë‹¨ì¼ ëª¨ë¸ ì¶”ë¡ ë§Œìœ¼ë¡œ íŠ¸ë¦¬ê±°ë¥¼ ì²˜ë¦¬í•˜ë©´ API í˜¸ì¶œ íƒ€ì´ë°/ë²”ìœ„ê°€ í”ë“¤ë ¤ ì •í™•ë„ê°€ ë–¨ì–´ì ¸,
  "ì˜ë„ ë¶„ë¥˜ -> í•„ìš”í•œ APIë§Œ í˜¸ì¶œ -> ê²°ê³¼ ì •ê·œí™” í›„ ë‹µë³€" êµ¬ì¡°ê°€ í•„ìš”í–ˆê¸° ë•Œë¬¸.

### ë³€ê²½ ë‚´ìš©
- `IntentRouter` ì¶”ê°€:
  - Azure OpenAI ê¸°ë°˜ intent ë¼ìš°í„° í´ëž˜ìŠ¤ êµ¬í˜„
  - ê¸°ë³¸ ëª¨ë¸: `INTENT_ROUTER_MODEL` (ê¸°ë³¸ê°’ `gpt-4o-mini`)
  - ì¶œë ¥ ìŠ¤í‚¤ë§ˆ: `intent`, `destination`
  - ë¼ìš°í„° ì‹¤íŒ¨ ì‹œ í‚¤ì›Œë“œ ê¸°ë°˜ fallback ë¼ìš°íŒ…
- `Tool Executor` ì¶”ê°€:
  - `_execute_tools_for_intent(intent, lat, lng, destination)` êµ¬í˜„
  - intentë³„ë¡œ í•„ìš”í•œ live ë°ì´í„°ë¥¼ ì„ ë³„/ê°€ê³µ
    - `subway_route`, `bus_route`, `weather`, `air_quality`, `commute_overview`
- WebSocket í„´ ì²˜ë¦¬ ì—°ë™:
  - ì‚¬ìš©ìž STT í…ìŠ¤íŠ¸ë§ˆë‹¤ intent ë¼ìš°íŒ… ì‹¤í–‰
  - ëª©ì ì§€ ìƒíƒœ ê°±ì‹  í›„ tool executor ì‹¤í–‰
  - ê²°ê³¼ë¥¼ Gemini ì„¸ì…˜ ì»¨í…ìŠ¤íŠ¸ ì—…ë°ì´íŠ¸(`send_client_content`) íë¡œ ì£¼ìž…

### ê¸°ëŠ¥ ëª©ì 
- ë§¤ ì§ˆë¬¸ ì˜ë„ì— ë§žëŠ” API íŠ¸ë¦¬ê±° ìžë™í™”
- ì‘ë‹µ ê·¼ê±°ë¥¼ live ë°ì´í„°ë¡œ ì œí•œí•´ í™˜ê°ì„± ì‘ë‹µ ê°ì†Œ

## 2026-02-13 (ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´ì…˜ ë‹¨ì¼í™” ì •ë¦¬)

### ëŒ€ìƒ íŒŒì¼
- `temp_front/app/page.tsx`
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- í˜¼í•© ìƒíƒœ(êµ¬ë°©ì‹ `seoul_summary` + ì‹ ë°©ì‹ ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´ì…˜)ê°€ ì¶©ëŒì„ ë§Œë“¤ ìˆ˜ ìžˆì–´,
  ì‹ ë°©ì‹ë§Œ ì‚¬ìš©í•˜ë„ë¡ ê²½ë¡œë¥¼ ë‹¨ì¼í™”í•˜ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- `temp_front/app/page.tsx`
  - Connect ì‹œ êµ¬ë°©ì‹ live prefetch/`seoul_summary` ìƒì„±/ë³´ê´€ ë¡œì§ ì œê±°
  - WebSocket ì—°ê²° íŒŒë¼ë¯¸í„°ë¥¼ `user_id + lat/lng` ì¤‘ì‹¬ìœ¼ë¡œ ë‹¨ìˆœí™”
- `backend/server.py`
  - `/ws/audio`ì—ì„œ `seoul_summary` ì¿¼ë¦¬ íŒŒë¼ë¯¸í„° ì²˜ë¦¬ ì œê±°
  - ì´ˆê¸° ì‹œìŠ¤í…œ ì§€ì¹¨ì— `SEOUL SUMMARY CONTEXT`ë¥¼ ë¶™ì´ëŠ” êµ¬ë°©ì‹ ì£¼ìž… ì œê±°
  - í„´ë³„ ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´ì…˜ ì»¨í…ìŠ¤íŠ¸ ì£¼ìž… ê²½ë¡œë§Œ ìœ ì§€

### ê¸°ëŠ¥ ëª©ì 
- ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´ì…˜ ì „ìš© ìš´ì˜(ë‹¨ì¼ ì†ŒìŠ¤ ì˜¤ë¸Œ íŠ¸ë£¨ìŠ¤) í™•ë³´
- Connect ì‹œì  ë¶ˆí•„ìš”í•œ ì„ í–‰ ì»¨í…ìŠ¤íŠ¸/ë¡œê·¸ ë¶€ìž‘ìš© ì œê±°

## 2026-02-13 (ìœ„ì¹˜ í•„ìˆ˜ ì—°ê²° ê°•ì œ + ì¢Œí‘œ ìˆ˜ì‹  ë¡œê·¸ ì¶”ê°€)

### ëŒ€ìƒ íŒŒì¼
- `temp_front/app/page.tsx`
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ì‚¬ìš©ìž í…ŒìŠ¤íŠ¸ì—ì„œ ìœ„ì¹˜ì •ë³´ ëˆ„ë½ìœ¼ë¡œ ODSAY ê¸°ë°˜ ê²½ë¡œê°€ ì‹¤íŒ¨í•˜ëŠ” ë¬¸ì œê°€ ë°˜ë³µë˜ì–´,
  ìœ„ì¹˜ ê¶Œí•œì´ ì—†ìœ¼ë©´ ì—°ê²°ì„ ì§„í–‰í•˜ì§€ ì•Šë„ë¡ ëª…í™•ížˆ ì œì–´í•  í•„ìš”ê°€ ìžˆì—ˆìŒ.

### ë³€ê²½ ë‚´ìš©
- `temp_front/app/page.tsx`
  - Connect ì‹œ geolocation ì‹¤íŒ¨í•˜ë©´ WebSocket ì—°ê²° ì¤‘ë‹¨
  - ìƒíƒœ ë©”ì‹œì§€ë¡œ ìœ„ì¹˜ ê¶Œí•œ í•„ìš” ì•ˆë‚´ (`localhost` + ìœ„ì¹˜ í—ˆìš©)
- `backend/server.py`
  - WebSocket ì—°ê²° ì‹œ `lat/lng` ìˆ˜ì‹  ì—¬ë¶€ ë¡œê·¸ ì¶”ê°€
    - ì¢Œí‘œ ìžˆìŒ: ìˆ˜ì‹  ê°’ ì¶œë ¥
    - ì¢Œí‘œ ì—†ìŒ: ODSAY ì‹¤ì‹œê°„ ë¼ìš°íŒ… ë¶ˆê°€ ê²½ê³  ì¶œë ¥

### ê¸°ëŠ¥ ëª©ì 
- ìœ„ì¹˜ ëˆ„ë½ ìƒíƒœì—ì„œ ìž˜ëª»ëœ ê²½ë¡œ ì‘ë‹µì„ ë°©ì§€
- ì„œë²„ ë¡œê·¸ë§Œ ë³´ê³ ë„ ìœ„ì¹˜ ì „ë‹¬ ì„±ê³µ/ì‹¤íŒ¨ë¥¼ ì¦‰ì‹œ íŒë‹¨ ê°€ëŠ¥

## 2026-02-13 (IntentRouter ë°°í¬ëª… ì˜¤ë¥˜ ëŒ€ì‘)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ë¡œê·¸ì—ì„œ Azure OpenAI `DeploymentNotFound`(404)ë¡œ intent ë¼ìš°íŒ…ì´ ë°˜ë³µ ì‹¤íŒ¨í•˜ì—¬,
  ë§¤ í„´ ì—ëŸ¬ ëˆ„ì  ë° ë¼ìš°í„° í’ˆì§ˆ ì €í•˜ê°€ ë°œìƒí–ˆê¸° ë•Œë¬¸.

### ë³€ê²½ ë‚´ìš©
- ë¼ìš°í„° ëª¨ë¸ëª… ê²°ì • ë¡œì§ ë³´ê°•:
  - `INTENT_ROUTER_MODEL` ì—†ìœ¼ë©´ `AZURE_OPENAI_DEPLOYMENT_NAME` ìš°ì„  ì‚¬ìš©
- ë¼ìš°íŒ… ì‹¤íŒ¨ ì²˜ë¦¬ ë³´ê°•:
  - ì˜ˆì™¸ ë©”ì‹œì§€ì— `DeploymentNotFound` í¬í•¨ ì‹œ Azure ë¼ìš°í„° ë¹„í™œì„±í™”
  - ì´í›„ í‚¤ì›Œë“œ fallback ë¼ìš°íŒ…ìœ¼ë¡œ ìžë™ ì „í™˜

### ê¸°ëŠ¥ ëª©ì 
- ë°°í¬ëª… ì˜¤ì„¤ì • ìƒíƒœì—ì„œë„ ëŒ€í™” íë¦„ ì§€ì†
- ë™ì¼ 404 ë¡œê·¸ ë°˜ë³µ ë°©ì§€ ë° fallback ì•ˆì •ì„± í™•ë³´

## 2026-02-13 (í„´ ì‘ë‹µ ì•ˆì •í™”: ì¦‰ì‹œ ì»¨í…ìŠ¤íŠ¸ ì£¼ìž… + ìž¬ì§ˆë¬¸ ê·œì¹™)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ìœ„ì¹˜ ì¢Œí‘œê°€ ì´ë¯¸ ìžˆìŒì—ë„ ëª¨ë¸ì´ ìœ„ì¹˜ë¥¼ ë‹¤ì‹œ ë¬»ëŠ” ì‘ë‹µì´ ë°œìƒí•˜ê³ ,
  í„´ ì»¨í…ìŠ¤íŠ¸ ì£¼ìž… íƒ€ì´ë° ì§€ì—°ìœ¼ë¡œ ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´ì…˜ ë°˜ì˜ì´ ëŠ¦ì–´ì§€ëŠ” ë¬¸ì œë¥¼ ì™„í™”í•˜ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- ì‚¬ìš©ìž STT í™•ì •(`on_recognized`, role=user) ì‹œì ì— ì»¨í…ìŠ¤íŠ¸ë¥¼ ì¦‰ì‹œ `send_client_content`ë¡œ ì£¼ìž…
  - ì„¸ì…˜ ì¤€ë¹„ ì „ì—ëŠ” í ì ìž¬, ì„¸ì…˜ ì¤€ë¹„ í›„ ì¦‰ì‹œ ì£¼ìž…
- ì‹œìŠ¤í…œ ì§€ì¹¨ ê°•í™”:
  - `lat/lng` ìˆ˜ì‹  ì‹œ "í˜„ìž¬ ìœ„ì¹˜ ìž¬ì§ˆë¬¸ ê¸ˆì§€" ëª…ì‹œ
- ëª©ì ì§€ ë¯¸ì§€ì • ìž¬ì§ˆë¬¸ ì •ì±… ì¶”ê°€:
  - êµí†µ ì˜ë„(`subway_route`, `bus_route`, `commute_overview`)ì—ì„œ ëª©ì ì§€ê°€ ì—†ìœ¼ë©´ ëª©ì ì§€ ì§ˆë¬¸ 1íšŒë§Œ í—ˆìš©
  - ë™ì¼ ì„¸ì…˜ì—ì„œ ë°˜ë³µ ì§ˆë¬¸ ê¸ˆì§€
- ì„¸ì…˜ ì¢…ë£Œ ì‹œ `session_ref` í•´ì œ ì²˜ë¦¬ ì¶”ê°€

### ê¸°ëŠ¥ ëª©ì 
- ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´ì…˜ ì»¨í…ìŠ¤íŠ¸ê°€ ì²« ì‘ë‹µ ì „ì— ë°˜ì˜ë  í™•ë¥  ê°œì„ 
- "í˜„ìž¬ ìœ„ì¹˜ê°€ ì–´ë””ëƒ" ë°˜ë³µ ì§ˆì˜ ê°ì†Œ
- ëª©ì ì§€ ìž¬ì§ˆë¬¸ ë°˜ë³µ ë£¨í”„ ë°©ì§€

## 2026-02-13 (ì—°ê²° ì§í›„ ìœ„ì¹˜ ì»¨í…ìŠ¤íŠ¸ ì„ ì£¼ìž…)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ìœ„ì¹˜ ì¢Œí‘œê°€ WS ì¿¼ë¦¬ë¡œ ìˆ˜ì‹ ë˜ë”ë¼ë„, ëª¨ë¸ ì„¸ì…˜ ì‹œìž‘ ì§í›„ì—ëŠ” í•´ë‹¹ ë§¥ë½ì„ ëª…ì‹œì ìœ¼ë¡œ ì „ë‹¬í•˜ì§€ ì•Šì•„
  ì²« ì‘ë‹µì—ì„œ "í˜„ìž¬ ìœ„ì¹˜ë¥¼ ëª¨ë¥´ê² ë‹¤"ëŠ” ë°œí™”ê°€ ë°œìƒí•  ìˆ˜ ìžˆì—ˆê¸° ë•Œë¬¸.

### ë³€ê²½ ë‚´ìš©
- Gemini Live ì„¸ì…˜ ì—°ê²° ì§í›„(`Connected to Live API`) ì¦‰ì‹œ:
  - í˜„ìž¬ `lat/lng` ê¸°ë°˜ `commute_overview` ì»¨í…ìŠ¤íŠ¸ ìƒì„±
  - `send_client_content`ë¡œ ëª¨ë¸ì— ì„ ì£¼ìž…
- ì£¼ìž… ì‹¤íŒ¨ ì‹œ ë¡œê·¸ ì¶œë ¥:
  - `[SeoulInfo] initial location context injection failed: ...`

### ê¸°ëŠ¥ ëª©ì 
- ì—°ê²° ì‹œìž‘ ì‹œì ë¶€í„° ëª¨ë¸ì´ ì‚¬ìš©ìž í˜„ìž¬ ìœ„ì¹˜ ë§¥ë½ì„ ì¸ì§€
- í‡´ê·¼ê¸¸/ê²½ë¡œ ì§ˆë¬¸ ì²« í„´ ì •í™•ë„ ê°œì„ 

## 2026-02-14 (Default destination preload + cache-first commute context)

### Target files
- `backend/server.py`

### Why
- User requested that commute information should be prepared immediately at websocket connect time using current coordinates, so voice responses can be immediate without asking location again.
- Destination should be recalculated only when user changes destination.

### What changed
- Added per-session `destination_state` at websocket start:
  - `name` (default: `COMMUTE_DEFAULT_DESTINATION`)
  - `cached_summary` (preloaded commute summary)
  - `asked_once` (destination follow-up guard)
- At websocket connect:
  - if `lat/lng` exists, run one-time `commute_overview` tool execution
  - cache summary in `destination_state["cached_summary"]`
- System instruction now includes `[PRELOADED_COMMUTE_CONTEXT]` when cache exists.
- Initial live context injection uses cached summary first; fallback executes tools only if cache is empty.
- Turn handling behavior:
  - transit intents (`subway_route`, `bus_route`, `commute_overview`) use cached summary first
  - if user says a different destination, cache is invalidated and recomputed on demand

### Fix included
- Fixed ordering bug where `destination_state` was referenced before initialization in websocket startup.

### Functional goal
- On first user request (for commute), model already has route context from current location.
- Avoid repeated "where are you?" prompts when device coordinates are already present.

## 2026-02-14 (Åð±Ù±æ ±âº» ÀÀ´äÀ» ÁöÇÏÃ¶ Àü¿ëÀ¸·Î °íÁ¤)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- "Åð±Ù±æ ¾Ë·ÁÁà" ±âº» ¿äÃ»¿¡¼­ ¹ö½º °æ·Î°¡ ¸ÕÀú ¾È³»µÇ¾î »ç¿ëÀÚ ¿ä±¸(ÁöÇÏÃ¶ ±âÁØ Ãâ¹ß¿ª/¹æ¸é/µµÂøºÐ/Å¾½ÂÆÇ´Ü)¿Í ºÒÀÏÄ¡.
- Ä³½Ã°¡ ¹ö½º ¿ä¾àÀ¸·Î ³²¾Æ ÀÌÈÄ ÁöÇÏÃ¶ ¿äÃ»¿¡µµ ¼¯¿© ³ª¿À´Â ¹®Á¦ Á¸Àç.

### º¯°æ ³»¿ë
- ±âº» ¸ñÀûÁö(`COMMUTE_DEFAULT_DESTINATION`)¿¡ ´ëÇÑ `commute_overview`´Â ÁöÇÏÃ¶ ¿ì¼± ¸ðµå·Î ½ÇÇàÇÏµµ·Ï º¯°æ.
  - ODSAY Á¶È¸ ½Ã `SearchPathType=1`(subway) ¿ì¼± ½Ãµµ.
  - ½ÇÆÐ ½Ã ÀÏ¹Ý °æ·Î(`SearchPathType=0`)·Î º¸Á¶ Á¶È¸.
- ÁöÇÏÃ¶ ¾È³» ¹®±¸¸¦ °­Á¦:
  - Ãâ¹ß¿ª, ³ë¼±/¹æ¸é, ÇöÀç¿ª¡æÃâ¹ß¿ª µµº¸ºÐ, ÀÌ¹ø ¿­Â÷ ETA, ´ÙÀ½ ¿­Â÷ ETA Áß½ÉÀ¸·Î ±¸¼º.
- ¿­Â÷ Å¾½Â ÆÇ´Ü ±âÁØ Á¶Á¤:
  - `µµº¸ºÐ >= ÀÌ¹ø¿­Â÷ ETA` ÀÌ¸é "ÀÌ¹ø ¿­Â÷ ³õÄ¥ °¡´É¼º ³ôÀ½, ´ÙÀ½ ¿­Â÷ ±ÇÀå".
- ETA ¹Ý¿Ã¸² ±ÔÄ¢ Á¶Á¤:
  - 3ºÐ 30ÃÊ¸¦ 4ºÐÀ¸·Î ¿Ã¸®Áö ¾Ê°í "¾à 3ºÐ"À¸·Î º¸¼öÀûÀ¸·Î °è»ê(1ºÐ ¹Ì¸¸Àº 1ºÐ Ã³¸®).
- Ä³½Ã »ç¿ë ¹üÀ§ Ãà¼Ò:
  - `cached_summary`´Â `commute_overview`¿¡¼­¸¸ »ç¿ë.
  - `subway_route`/`bus_route`´Â ¸Å¹ø ÃÖ½Å µµ±¸ ½ÇÇà °á°ú¸¦ »ç¿ëÇØ È¥¼± ¹æÁö.

### ±â´ë È¿°ú
- "Åð±Ù±æ ¾Ë·ÁÁà" ½Ã ÁöÇÏÃ¶ Áß½ÉÀ¸·Î ÀÏ°üµÈ ÀÀ´ä.
- "Áö±Ý Å¸¸é µÇ´ÂÁö / ´ÙÀ½ ¿­Â÷ Å¸¾ß ÇÏ´ÂÁö" ÆÇ´Ü Á¤È®µµ Çâ»ó.
- ÁöÇÏÃ¶ ¿äÃ» ½Ã ÀÌÀü ¹ö½º Ä³½Ã°¡ ¼¯ÀÌ´Â ¹®Á¦ ¿ÏÈ­.

## 2026-02-14 (Åð±Ù±æ ¾È³» ±ÔÄ¢ Á¤±³È­: ETA/Å¾½ÂÆÇ´Ü/ºÒÇÊ¿ä Á¤º¸ Á¦°Å)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- 1~2ºÐ ³²Àº ¿­Â÷¸¦ "È¥ÀâÇØ¼­ ³õÄ¡±â ½±´Ù"Ã³·³ °úµµÇÏ°Ô ÇØ¼®ÇÏ´Â ¹®Á¦°¡ ÀÖ¾úÀ½.
- µµº¸ 11ºÐ vs ´ÙÀ½ ¿­Â÷ 4ºÐ °°Àº ºÒ°¡´É ÄÉÀÌ½º¿¡¼­µµ "´ÙÀ½ ¿­Â÷ ±ÇÀå" ¹®±¸°¡ ³ª¿À´Â ¹®Á¦ Á¸Àç.
- Åð±Ù±æ ÀÀ´ä¿¡ ´ë±âÁú/³¯¾¾/µû¸ªÀÌ ¹®±¸°¡ ¼¯¿© ÇÙ½É ¾È³»¸¦ Èå¸².

### º¯°æ ³»¿ë
- ETA Ç¥Çö ±ÔÄ¢ Ãß°¡(`_format_eta_phrase`):
  - 1~2ºÐ: "°ð µµÂø"
  - 3ºÐ ÀÌ»ó: "¾à NºÐ"
- ÁöÇÏÃ¶ Å¾½Â ÆÇ´Ü ·ÎÁ÷ ¼¼ºÐÈ­:
  - `first`: µµº¸½Ã°£ < ÀÌ¹ø ¿­Â÷ ETA
  - `next`: ÀÌ¹øÀº ¾î·Æ°í µµº¸½Ã°£ < ´ÙÀ½ ¿­Â÷ ETA
  - `after_next`: ÀÌ¹ø/´ÙÀ½ ¸ðµÎ ¾î·Á¿ò (´ÙÀ½ ¿­Â÷ ±ÇÀå ¹®±¸ ±ÝÁö)
- Åð±Ù±æ/°æ·Î ¿ä¾à¿¡¼­ ´ë±âÁú/³¯¾¾/µû¸ªÀÌ ¹®±¸ Á¦°Å.
- ½Ã½ºÅÛ ÁöÄ§ °­È­:
  - ½Çµ¥ÀÌÅÍ ¾øÀ¸¸é È¥Àâ/±ºÁß(È¥Àâµµ) ¾ð±Þ ±ÝÁö.

### ±â´ë È¿°ú
- "1ºÐ ³²À½" ÄÉÀÌ½º¿¡¼­ °úµµÇÑ °æ°í ´ë½Å ÀÚ¿¬½º·¯¿î "°ð µµÂø" ¾È³».
- ¹°¸®ÀûÀ¸·Î ºÒ°¡´ÉÇÑ "´ÙÀ½ ¿­Â÷ ±ÇÀå" ¿À·ù °¨¼Ò.
- Åð±Ù±æ ÀÀ´äÀÌ Ãâ¹ß¿ª/¹æ¸é/ETA/µµº¸/Å¾½ÂÆÇ´Ü Áß½ÉÀ¸·Î °£°áÈ­.

## 2026-02-14 (ºñ±âº» ¸ñÀûÁö ÁöÇÏÃ¶ »ó¼¼ °æ·Î/È¯½Â ¾È³» °­È­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- ±âº» Åð±Ù±æ(Áý) ¿Ü ¸ñÀûÁö¸¦ ¹°À» ¶§´Â ´Ü¼ø ¿ä¾àÀÌ ¾Æ´Ï¶ó
  - ¾î´À ¿ª/¸î È£¼±/¾î´À ¹æ¸é Å¾½Â,
  - ¾îµð¼­ ³»·Á È¯½Â,
  - È¯½Â ÈÄ ¾îµð¼­ ÇÏÂ÷
  ±îÁö ´Ü°èÇü ¾È³»°¡ ÇÊ¿äÇÔ.

### º¯°æ ³»¿ë
- ODSAY °æ·Î ÆÄ½Ì È®Àå:
  - `subPath`ÀÇ ¸ðµç ÁöÇÏÃ¶ ±¸°£À» `subwayLegs`·Î ¼öÁý
  - °¢ ±¸°£º° `line`, `start`, `end`, `direction` ÀúÀå
- ºñ±âº» ¸ñÀûÁö + (`commute_overview` ¶Ç´Â `subway_route`)ÀÏ ¶§ `detailed_subway` È°¼ºÈ­.
- ÀÀ´ä »ý¼º °­È­:
  - ±âÁ¸ Ãâ¹ß¿ª ¿­Â÷ µµÂøÁ¤º¸(ÀÌ¹ø/´ÙÀ½ ETA, µµº¸ ºñ±³)´Â À¯Áö
  - Ãß°¡·Î ÁöÇÏÃ¶ ±¸°£ »ó¼¼ ¹®±¸¸¦ ¼øÂ÷ Á¦°ø
    - 1±¸°£: ¾îµð ¿ª¿¡¼­ ¸î È£¼±/¹æ¸é Å¾½Â, ¾îµð¼­ ÇÏÂ÷
    - 2±¸°£ ÀÌ»ó: nÂ÷ È¯½Â¿ª, È¯½Â ³ë¼±/¹æ¸é, ÇÏÂ÷¿ª

### ±â´ë È¿°ú
- ºñ±âº» ¸ñÀûÁö Áú¹® ½Ã ÁöÇÏÃ¶ Áß½ÉÀÇ ´Ü°èº° È¯½Â ¾È³»°¡ Á¦°øµÇ¾î ½ÇÁ¦ ÀÌµ¿¿¡ ¹Ù·Î »ç¿ë °¡´É.

## 2026-02-14 (´Ù¸¥ ¸ñÀûÁö ÀÚµ¿ ÀÎ½Ä/À§Ä¡ ÀçÁú¹® ¹æÁö º¸°­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- "¼º¼ö¿¡¼­ ¾à¼Ó", "¼º¼ö ÂÊ" °°Àº ¹ßÈ­¿¡¼­ ¸ñÀûÁö°¡ ÃßÃâµÇÁö ¾Ê¾Æ °æ·Î ÀÀ´äÀÌ ºñ°Å³ª ¹Ýº¹ È®ÀÎ Áú¹®ÀÌ ¹ß»ý.
- ¶óÀÌºê ¿ä¾à »ý¼º ½ÇÆÐ ½Ã ¸ðµ¨ÀÌ À§Ä¡¸¦ ´Ù½Ã ¹°¾îº¸´Â ÄÉÀÌ½º°¡ ³²¾Æ ÀÖ¾úÀ½.

### º¯°æ ³»¿ë
- ¸ñÀûÁö ÃßÃâ ÆÐÅÏ È®Àå:
  - `...¿¡¼­ ¾à¼Ó`, `...ÂÊ(À¸·Î)`, `...¿¡/¿¡¼­ °¡` ÇüÅÂ ÀÎ½Ä
  - ¹®Àå ³¡ `...À¸·Î/·Î` ´Ü¹®(¿¹: "¼º¼ö·Î") ÀÎ½Ä
  - ÈÄÃ³¸®·Î `ÂÊ/±ÙÃ³/ºÎ±Ù/¹æÇâ` Á¢¹Ì Á¤¸®
- ¸ñÀûÁö ÁÂÇ¥ ÇØ¼® º¸°­:
  - `searchStation(name)` ½ÇÆÐ ½Ã `searchStation(name + "¿ª")` ÀÚµ¿ Àç½Ãµµ
  - ¿¹: `¼º¼ö` -> `¼º¼ö¿ª` ÀÚµ¿ º¸Á¤
- µ¿Àû ÄÁÅØ½ºÆ® ÁÖÀÔ º¸°­:
  - µµ±¸ ¿ä¾àÀÌ ºñ¾îµµ ÃÖ¼Ò ÄÁÅØ½ºÆ®¸¦ Ç×»ó ÁÖÀÔ
  - ÁÂÇ¥°¡ ÀÖ´Â °æ¿ì: "ÇöÀç À§Ä¡ ÁÂÇ¥´Â ÀÌ¹Ì ¼ö½Å" ¸Þ½ÃÁö °­Á¦
  - °¡ÀÌµå·Î "»ç¿ëÀÚ ÇöÀç À§Ä¡ ÀçÁú¹® ±ÝÁö"¸¦ Ç×»ó µ¿ºÀ

### ±â´ë È¿°ú
- ´Ù¸¥ ¸ñÀûÁö Áú¹® ½Ã ¸ñÀûÁö ÀÚµ¿ ÀÎ½Ä ¼º°ø·ü »ó½Â.
- À§Ä¡¸¦ ÀÌ¹Ì ¹Þ¾Ò´Âµ¥µµ ´Ù½Ã ¹¯´Â Çö»ó °¨¼Ò.

## 2026-02-14 (´Ù¸¥ ¸ñÀûÁö ¿äÃ» ½Ã ±¤È­¹®À¸·Î µÇµ¹¾Æ°¡´Â ¹®Á¦ ¼öÁ¤)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ ¿øÀÎ
- »ç¿ëÀÚ°¡ ´Ù¸¥ ¸ñÀûÁö¸¦ ¸í½ÃÇß´Âµ¥ ¸ñÀûÁö ÁÂÇ¥ ÇØ¼®ÀÌ ½ÇÆÐÇÏ¸é, ·ÎÁ÷ÀÌ ±âº» ¸ñÀûÁö(±¤È­¹®) ÁÂÇ¥·Î Æú¹éµÇ¾î Àß¸øµÈ °æ·Î¸¦ ¾È³»ÇÔ.

### º¯°æ ³»¿ë
- ¸ñÀûÁö Æú¹é ±ÔÄ¢ ¼öÁ¤:
  - »ç¿ëÀÚ°¡ ¸ñÀûÁö¸¦ ¸í½ÃÇÑ °æ¿ì(`destination_requested=True`) ÁÂÇ¥ ÇØ¼® ½ÇÆÐ ½Ã **±âº» ¸ñÀûÁö·Î Æú¹éÇÏÁö ¾ÊÀ½**.
  - ±âº» ¸ñÀûÁö Æú¹éÀº »ç¿ëÀÚ°¡ ¸ñÀûÁö¸¦ ¸í½ÃÇÏÁö ¾Ê¾ÒÀ» ¶§¸¸ Çã¿ë.
- ¸ñÀûÁö ÃßÃâ °­È­:
  - `...°¡´Â ±æ`, `...°¡´Â±æ` ÆÐÅÏ Ãß°¡ ÀÎ½Ä.
- ¸ñÀûÁö ¹ÌÇØ¼® ½Ã ¾È³» °³¼±:
  - `'<¸ñÀûÁö>' ¸ñÀûÁö¸¦ ¿ª ±âÁØÀ¸·Î Ã£Áö ¸øÇß¾î¿ä. ¿¹: ¼º¼ö¿ª` ÇüÅÂ·Î ¸íÈ®È÷ ¾È³».
  - µ¿½Ã¿¡ ÇöÀç ±âÁØ °¡±î¿î ¿ªµµ ÇÔ²² Á¦°ø.
- ÀÇµµ º¸Á¤:
  - `intent=general`ÀÌ¶óµµ ¸ñÀûÁö°¡ ÃßÃâµÇ°í ¹®Àå¿¡ `±æ/°æ·Î/°¡´Â`ÀÌ ÀÖÀ¸¸é `commute_overview`·Î °­Á¦ º¸Á¤.

### ±â´ë È¿°ú
- "¼º¼ö °¡´Â ±æ" ¿äÃ»¿¡¼­ ±¤È­¹® °æ·Î°¡ ´Ù½Ã ³ª¿À´Â ¿Àµ¿ÀÛ ¹æÁö.
- ¸ñÀûÁö°¡ ¾Ö¸ÅÇÒ ¶§µµ ÀÚµ¿À¸·Î °æ·Î ÀÇµµ·Î Ã³¸®ÇÏ°í, ÇÊ¿äÇÑ ÃÖ¼Ò ÀçÁú¹®¸¸ ¼öÇà.

## 2026-02-14 (¼º¼ö/´Ü¹® ¸ñÀûÁö ÀÎ½Ä ½ÇÆÐ Ãß°¡ º¸°­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- "¼º¼ö °¡´Â ¹æ¹ý" °°Àº ¹ßÈ­¿¡¼­ STT º¯Çü(¿¹: °¡´É/¹æ¹ý/°æ·Î) ¶§¹®¿¡ ¸ñÀûÁö ¹®ÀÚ¿­ÀÌ Èçµé·Á ¿ª °Ë»ö ½ÇÆÐ °¡´É¼ºÀÌ ³²¾Æ ÀÖ¾úÀ½.

### º¯°æ ³»¿ë
- ¸ñÀûÁö ÃßÃâ ÆÐÅÏ Ãß°¡:
  - `... (°¡´Â|°¥|°¡´É) ¹æ¹ý`
  - `... ¹æ¹ý`, `... °æ·Î` ´Ü¹® ÆÐÅÏ
- ¸ñÀûÁö ÈÄº¸ Á¤±ÔÈ­ ÇÔ¼ö Ãß°¡(`_build_destination_candidates`):
  - Á¶»ç/ÀâÀ½(`À¸·Î/·Î/¿¡/¿¡¼­/ÂÊ/±ÙÃ³/¹æÇâ/°¡´Â/¹æ¹ý/°æ·Î`) Á¦°Å
  - °ø¹é Á¦°Å º¯Çü Ãß°¡
  - `¿ª` ¹ÌÆ÷ÇÔ ½Ã `...¿ª` ÀÚµ¿ È®Àå
- ÁÂÇ¥ ÇØ¼® ½Ã À§ ÈÄº¸±ºÀ» ¼øÂ÷ Àç½ÃµµÇÏµµ·Ï º¯°æ.

### ±â´ë È¿°ú
- "¼º¼ö °¡´Â ¹æ¹ý", "¼º¼ö °æ·Î" °°Àº ¹®Àå¿¡¼­µµ `¼º¼ö¿ª`À¸·Î ¾ÈÁ¤ÀûÀ¸·Î ¸ÅÇÎµÉ È®·ü Çâ»ó.

## 2026-02-14 (LLM ¿ì¼± Æ®¸®°Å °æ°è ¸íÈ®È­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- »ç¿ëÀÚ ÁöÀû´ë·Î, LLMÀÌ Á¤»ó µ¿ÀÛ °¡´ÉÇÑµ¥µµ Á¤±Ô½Ä º¸Á¤ÀÌ Ç×»ó °³ÀÔÇÏ¸é "LLM ÆÇ´Ü" ÀÏ°ü¼ºÀÌ ¾àÇØÁü.

### º¯°æ ³»¿ë
- `IntentRouter.route()` ÀÀ´ä¿¡ `source` ÇÊµå Ãß°¡:
  - LLM ¼º°ø: `source="llm"`
  - Python fallback: `source="fallback"`
- »ç¿ëÀÚ ¹ßÈ­ Ã³¸® ½Ã ¸ñÀûÁö °áÁ¤ ±ÔÄ¢ º¯°æ:
  - `source="llm"`ÀÌ¸é LLMÀÇ `destination`¸¸ »ç¿ë(Á¤±Ô½Ä º¸Á¤ ¹Ì»ç¿ë)
  - `source="fallback"`ÀÏ ¶§¸¸ Á¤±Ô½Ä ÃßÃâ º¸Á¶ »ç¿ë
- °üÃø ·Î±× Ãß°¡:
  - `[IntentRouter] source=..., intent=..., destination=...`

### ±â´ë È¿°ú
- LLM »ç¿ë °¡´É ½Ã Æ®¸®°Å/¸ñÀûÁö ÆÇ´ÜÀÌ LLM Áß½ÉÀ¸·Î ÀÏ°üµÇ°Ô µ¿ÀÛ.
- fallback °³ÀÔ ½ÃÁ¡ÀÌ ¸íÈ®ÇØÁ® µð¹ö±ë ¿ëÀÌ.

## 2026-02-14 (±âÁ¸ ±¤È­¹® ÄÁÅØ½ºÆ® ¿À¿°À¸·Î ÀÎÇÑ ¸ñÀûÁö È¥¼± ¿ÏÈ­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ ¿øÀÎ
- ¿¬°á ½ÃÁ¡¿¡ ±âº» ¸ñÀûÁö(±¤È­¹®) °æ·Î ¿ä¾àÀ» ½Ã½ºÅÛ/ÃÊ±â ÄÁÅØ½ºÆ®¿¡ °­ÇÏ°Ô ÁÖÀÔÇØ,
  ÀÌÈÄ »ç¿ëÀÚ°¡ ´Ù¸¥ ¸ñÀûÁö(¿¹: ¼º¼ö)¸¦ ¸»ÇØµµ ÀÌÀü ¸ñÀûÁö ¸Æ¶ôÀÌ ´äº¯¿¡ ¼¯ÀÏ ¼ö ÀÖ¾úÀ½.
- `intent=general` ÅÏ¿¡µµ ¶óÀÌºê °æ·Î ÄÁÅØ½ºÆ®¸¦ °è¼Ó ÁÖÀÔÇØ ¹®¸Æ ¿À¿°ÀÌ ´©ÀûµÉ ¼ö ÀÖ¾úÀ½.

### º¯°æ ³»¿ë
- ½Ã½ºÅÛ ÇÁ·ÒÇÁÆ®¿¡¼­ preloaded °æ·Î ¿ä¾à °íÁ¤ ÁÖÀÔ Á¦°Å.
- ¿¬°á Á÷ÈÄ ÃÊ±â ÁÖÀÔÀº "À§Ä¡ ÀÎÁö" Á¤º¸¸¸ Àü´Þ(Æ¯Á¤ ¸ñÀûÁö °æ·Î ¹ÌÁÖÀÔ).
- »ç¿ëÀÚ ¹ßÈ­ Ã³¸®¿¡¼­ ¶óÀÌºê ÄÁÅØ½ºÆ® ÁÖÀÔ ¹üÀ§ Á¦ÇÑ:
  - `subway_route`, `bus_route`, `commute_overview`, `weather`, `air_quality`¿¡¸¸ ÁÖÀÔ
  - `general` ÅÏ¿¡´Â °æ·Î ÄÁÅØ½ºÆ® ÁÖÀÔÇÏÁö ¾ÊÀ½
- °æ·Î ÅÏ °¡ÀÌµå °­È­:
  - "ÀÌ¹ø ÅÏ ¸ñÀûÁö(destination_state)¸¦ ¿ì¼± »ç¿ëÇÏ°í ÀÌÀü ¸ñÀûÁö ¸Æ¶ô ¹«½Ã" Áö½Ã Ãß°¡

### ±â´ë È¿°ú
- ¼º¼ö ¿äÃ» ½Ã ±¤È­¹® °æ·Î°¡ ÀçÃâ·ÂµÇ´Â È¥¼± °¨¼Ò.
- ºñ°æ·Î ¹ßÈ­°¡ µé¾î¿Íµµ °æ·Î ¸Æ¶ô ¿À¿°ÀÌ ´©ÀûµÇÁö ¾ÊÀ½.

## 2026-02-14 (¼º¼ö °æ·Î ÄÁÅØ½ºÆ® ¹Ý¿µ Å¸ÀÌ¹Ö º¸°­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ Â¡ÈÄ
- LLM ¶ó¿ìÅÍ ·Î±×¿¡¼­ `intent=subway_route, destination=¼º¼ö`°¡ È®ÀÎµÇ´Âµ¥,
  ½ÇÁ¦ À½¼º ÀÀ´äÀº À§Ä¡ ÀçÁú¹®/¿À´äÀ¸·Î ÀÌ¾îÁü.

### ¿øÀÎ ÃßÁ¤
- ¶óÀÌºê ÄÁÅØ½ºÆ® ÁÖÀÔÀÌ ºñµ¿±â Å¸ÀÌ¹Ö¿¡¼­ ÀÀ´äº¸´Ù ´Ê°Ô ¹Ý¿µµÇ¾î,
  ¸ðµ¨ÀÌ ÄÁÅØ½ºÆ® ¾ø´Â »óÅÂ·Î ¸ÕÀú ´äº¯ÇÏ´Â °æ¿ì ¹ß»ý.

### º¯°æ ³»¿ë
- ¶óÀÌºê ÄÁÅØ½ºÆ® ÁÖÀÔ ÇÔ¼ö È®Àå:
  - `_inject_live_context_now(..., complete_turn: bool)` Ãß°¡
  - ³»ºÎ `send_client_content`¿¡ `turn_complete=complete_turn` ¹Ý¿µ
- °æ·Î ÀÇµµ(`subway_route`,`bus_route`,`commute_overview`)¿¡¼­´Â
  - ÄÁÅØ½ºÆ® ÁÖÀÔ ½Ã `complete_turn=True`·Î Áï½Ã ÀÀ´ä ÅÏÀ» °­Á¦
  - `[ACTION] Respond to the user's latest request now using this context.` °¡ÀÌµå Ãß°¡
- °üÃø ·Î±× º¸°­:
  - `[SeoulInfo] live context built: intent=..., destination=..., summary_ok=...`

### ±â´ë È¿°ú
- "¼º¼ö" ¸ñÀûÁö ÄÁÅØ½ºÆ®°¡ ¸ðµ¨ ÀÀ´ä Àü¿¡ ¹Ý¿µµÉ È®·ü »ó½Â.
- À§Ä¡ ÀçÁú¹® ºóµµ °¨¼Ò ¹× ¸ñÀûÁö ¸ÂÃã ÀÀ´ä ÀÏ°ü¼º °³¼±.

## 2026-02-14 (½Ç½Ã°£ °æ·Î Á¶È¸ Áö¿¬ ½Ã À½¼º ÇÊ·¯ ¸àÆ® Ãß°¡)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- ODSAY/½Ç½Ã°£ API Á¶È¸ Áß ¹«À½ ±¸°£ÀÌ ¹ß»ýÇØ »ç¿ëÀÚ Ã¼°¨ Áö¿¬ÀÌ Å­.

### º¯°æ ³»¿ë
- »ç¿ëÀÚ ¿äÃ»ÀÌ ½Ç½Ã°£ °æ·Î Á¶È¸°¡ ÇÊ¿äÇÑ ÀÇµµ(`subway_route`, `bus_route`, `commute_overview`)ÀÌ°í
  Ä³½ÃµÈ Áï½Ã ÀÀ´äÀÌ ¾ø´Â °æ¿ì:
  - º» Á¶È¸ Àü¿¡ `INTENT:loading` ÄÁÅØ½ºÆ®¸¦ ¸ÕÀú ÁÖÀÔ
  - ¸ðµ¨ÀÌ ÂªÀº ÇÑ±¹¾î ÇÊ·¯ ¸àÆ®(¿¹: "À½, Àá½Ã¸¸¿ä. Áö±Ý È®ÀÎÇØº¼°Ô¿ä.")¸¦ ¸ÕÀú ¸»ÇÏµµ·Ï À¯µµ
- ÀÌÈÄ ±âÁ¸´ë·Î API Á¶È¸ °á°ú ÄÁÅØ½ºÆ®¸¦ ÁÖÀÔÇØ º» ´äº¯À» ÀÌ¾î¼­ Á¦°ø.

### ±â´ë È¿°ú
- Á¶È¸ Áö¿¬ ±¸°£¿¡¼­ »ç¿ëÀÚ¿¡°Ô ÁøÇàÁßÀÓÀ» ÀÚ¿¬½º·´°Ô Àü´Þ.
- ¹«ÀÀ´äÃ³·³ ´À²¸Áö´Â Ã¼°¨ ¹®Á¦ ¿ÏÈ­.

## 2026-02-14 (Åð±Ù µµÂøÁ¤º¸ Ä³½Ã Á¦°Å: ¿äÃ» ½ÃÁ¡ ½Ç½Ã°£ ÀçÁ¶È¸)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- ÁöÇÏÃ¶ µµÂøÁ¤º¸´Â ºÐ ´ÜÀ§·Î º¯ÇÏ¹Ç·Î, Á¢¼Ó ½Ã ¼±Ä³½Ã/Àç»ç¿ëÇÏ¸é ¾È³»°¡ ½±°Ô stale(¿À·¡µÈ Á¤º¸) »óÅÂ°¡ µÊ.

### º¯°æ ³»¿ë
- ¼¼¼Ç »óÅÂ¿¡¼­ `cached_summary` Á¦°Å.
- websocket ¿¬°á ½Ã `commute_overview` ¼±Á¶È¸(preload) Á¦°Å.
- `commute_overview` Æ÷ÇÔ ±³Åë ÀÇµµ´Â ¸Å ¿äÃ» ½Ã `_execute_tools_for_intent(...)`·Î ½Ç½Ã°£ ÀçÁ¶È¸.
- ¸ñÀûÁö º¯°æ ½Ã Ä³½Ã ¹«È¿È­ ·ÎÁ÷µµ Á¦°Å(Ä³½Ã ÀÚÃ¼ ¾øÀ½).

### ±â´ë È¿°ú
- Åð±Ù ¿­Â÷ ETA/´ÙÀ½ ¿­Â÷ ÆÇ´ÜÀÌ Ç×»ó ¿äÃ» ½ÃÁ¡ ±âÁØÀ¸·Î °è»êµÊ.
- Á¢¼Ó Á÷ÈÄ ¿À·¡µÈ °æ·Î/µµÂøÁ¤º¸°¡ ¹Ýº¹µÇ´Â ¹®Á¦ ¿ÏÈ­.

## 2026-02-14 (Start Speaking ¹öÆ° ¹ÝÀÀ ºÒ°¡ ÀÌ½´ ´ëÀÀ)

### ´ë»ó ÆÄÀÏ
- `temp_front/app/page.tsx`

### ¹®Á¦ Â¡ÈÄ
- Start Speaking ¹öÆ°ÀÌ ´­¸®Áö ¾Ê°Å³ª, WebSocket Àç¿¬°á/Á¾·á ÈÄ UI »óÅÂ°¡ ²¿¿© À½¼º ½ÃÀÛÀÌ ½ÇÆÐ.

### º¯°æ ³»¿ë
- ¿¬°á »óÅÂ °ü¸® °­È­:
  - `isConnecting` »óÅÂ Ãß°¡, ¿¬°á Áß Áßº¹ Connect ¹æÁö
  - Connect ¹öÆ°¿¡ `Connecting...` ¹× ºñÈ°¼º ½ºÅ¸ÀÏ Àû¿ë
- WebSocket Á¾·á/¿À·ù Á¤¸® °­È­:
  - `onclose`/`onerror`¿¡¼­ `websocketRef` Á¤¸®
  - ³ìÀ½ ¸®¼Ò½º Áï½Ã Á¤¸®(`stopAudioProcessing`) ÈÄ »óÅÂ º¹±¸
- ¿Àµð¿À ½ÃÀÛ °¡µå Ãß°¡:
  - WS°¡ OPENÀÌ ¾Æ´Ï¸é ½ÃÀÛ Â÷´Ü + `Connect first` »óÅÂ Ç¥½Ã
  - ÀÌ¹Ì ³ìÀ½ ÁßÀÌ¸é Áßº¹ ½ÃÀÛ Â÷´Ü
  - AudioContext `suspended` »óÅÂ¸é `resume()` È£Ãâ
- ¸¶ÀÌÅ© ¸®¼Ò½º ÇØÁ¦ °­È­:
  - `MediaStream` Æ®·¢ `stop()` Ã³¸® Ãß°¡
  - processor/source/context ref¸¦ null·Î ÃÊ±âÈ­

### ±â´ë È¿°ú
- Start Speaking Å¬¸¯ ½Ã »óÅÂ ²¿ÀÓÀ¸·Î ¹ÝÀÀ ¾ø´Â ¹®Á¦ ¿ÏÈ­.
- ¿¬°á ²÷±è/Àç¿¬°á ÀÌÈÄ¿¡µµ À½¼º ½ÃÀÛ ¹öÆ° µ¿ÀÛ ÀÏ°ü¼º °³¼±.

## 2026-02-14 (»ç¿ëÀÚ Áý ¸ñÀûÁö ÇÁ·ÎÇÊ DB ÀúÀå/¾÷µ¥ÀÌÆ® µµÀÔ)

### ´ë»ó ÆÄÀÏ
- `backend/modules/cosmos_db.py`
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- Åð±Ù ºÐ±â ±âº» ¸ñÀûÁö´Â »ç¿ëÀÚº°·Î ´Þ¶ó¾ß ÇÏ¸ç, ¼¼¼Ç Àç½ÃÀÛ ÈÄ¿¡µµ À¯ÁöµÇ¾î¾ß ÇÔ.
- µµÂø ETA´Â ½Ç½Ã°£ ÀçÁ¶È¸°¡ ¸ÂÁö¸¸, "Áý ¸ñÀûÁö" ÀÚÃ¼´Â ¿µ±¸ ÀúÀåÀÌ ÇÊ¿äÇÔ.

### º¯°æ ³»¿ë
- CosmosDB ÇÁ·ÎÇÊ API Ãß°¡:
  - `get_user_profile(user_id)`
  - `upsert_user_profile(user_id, profile_updates)`
  - ÇÁ·ÎÇÊ ¹®¼­ Å°: `id = profile:{user_id}`, `doc_type = profile`
- ¸Þ¸ð¸® ¹®¼­¿¡ `doc_type = memory` Ãß°¡ ¹× Á¶È¸ ÇÊÅÍ º¸°­:
  - `get_all_memories`°¡ profile ¹®¼­¸¦ ¸Þ¸ð¸® ¸ñ·ÏÀ¸·Î ¼¯¾î ÀÐÁö ¾Êµµ·Ï ºÐ¸®.
- WebSocket ¿¬°á ½Ã »ç¿ëÀÚ ÇÁ·ÎÇÊ ·Îµå:
  - `home_destination`°¡ ÀÖÀ¸¸é ±âº» ¸ñÀûÁö·Î ¿ì¼± »ç¿ë
  - ¾øÀ¸¸é `.env`ÀÇ `COMMUTE_DEFAULT_DESTINATION` »ç¿ë
- ´ëÈ­ Áß Áý º¯°æ °¨Áö/¾÷µ¥ÀÌÆ®:
  - `ÀÌ»ç`, `ÁýÀº`, `¿ì¸®Áý`, `Áý ÁÖ¼Ò` µî È¨ ¾÷µ¥ÀÌÆ® ¹ßÈ­ °¨Áö
  - ¸ñÀûÁö°¡ ÃßÃâµÇ¸é ¼¼¼Ç ¸ñÀûÁö °»½Å + `upsert_user_profile`·Î DB ¹Ý¿µ

### ±â´ë È¿°ú
- »ç¿ëÀÚ Áý ¸ñÀûÁö°¡ ¼¼¼Ç °£ À¯ÁöµÊ.
- "ÀÌ»çÇß¾î/ÁýÀº ~" ¹ßÈ­·Î ÃÖ½Å Áý ¸ñÀûÁö Áï½Ã °»½Å °¡´É.
- Åð±Ù ¾È³»´Â ÃÖ½Å ÀúÀå Áý ¸ñÀûÁö¸¦ ±âº» µµÂøÁö·Î »ç¿ë.

## 2026-02-14 (Áý º¯°æ ¿©ºÎ¸¦ LLMÀÌ ÆÇÁ¤ÇÏµµ·Ï ÀüÈ¯)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- Áý º¯°æ/ÀÌ»ç ¿©ºÎ´Â ±ÔÄ¢ Å°¿öµåº¸´Ù ´ëÈ­ ¸Æ¶ô ±â¹Ý ÆÇ´ÜÀÌ ÇÊ¿äÇÔ.
- Ä£±¸ Áý ¹æ¹®/¿ÜÃâ ¸ñÀûÁö¿Í ½ÇÁ¦ Áý º¯°æÀ» ±¸ºÐÇÏ·Á¸é LLM ÆÇÁ¤ÀÌ ÀûÇÕ.

### º¯°æ ³»¿ë
- IntentRouter Ãâ·Â ½ºÅ°¸¶ È®Àå:
  - ±âÁ¸: `intent`, `destination`
  - º¯°æ: `intent`, `destination`, `home_update`
- ¶ó¿ìÅÍ ½Ã½ºÅÛ ÇÁ·ÒÇÁÆ® °­È­:
  - `home_update=true`´Â »ç¿ëÀÚ ¹ßÈ­°¡ "ÁýÀÌ ¹Ù²î¾ú´Ù/ÀÌ»çÇß´Ù/Áý À§Ä¡ º¯°æ"À» ¸í½ÃÇÒ ¶§¸¸ Çã¿ë
  - ´Ü¼ø °æ·ÎÁú¹®(Ä£±¸ Áý/³î·¯°¨/¹æ¹®)Àº `home_update=false` °­Á¦
- »ç¿ëÀÚ ¹ßÈ­ Ã³¸® ·ÎÁ÷ º¯°æ:
  - DB Áý ¸ñÀûÁö upsert´Â `home_update=true`ÀÏ ¶§¸¸ ¼öÇà
  - fallback ¸ðµå¿¡¼­¸¸ ±âÁ¸ Å°¿öµå º¸Á¶ ÆÇ´Ü Çã¿ë
- ¶ó¿ìÅÍ ·Î±× È®Àå:
  - `[IntentRouter] ... home_update=...` Ãâ·Â

### ±â´ë È¿°ú
- "¼º¼ö °¡´Â ±æ" °°Àº ÀÏÈ¸¼º ¸ñÀûÁö Áú¹®À¸·Î Áý Á¤º¸°¡ Àß¸ø µ¤¾î½áÁö´Â ¹®Á¦ ¿ÏÈ­.
- ½ÇÁ¦ ÀÌ»ç/Áý º¯°æ ¹ßÈ­¿¡¼­¸¸ »ç¿ëÀÚ È¨ ¸ñÀûÁö°¡ ¾÷µ¥ÀÌÆ®µÊ.

## 2026-02-14 (WebSocket 1008 policy violation ¿ÏÈ­: ÀÔ·Â ÇÁ·¹ÀÓ Ã³¸® ¾ÈÁ¤È­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ Â¡ÈÄ
- °æ·Î ÁúÀÇ ÈÄ °£ÇæÀûÀ¸·Î `[Server] Error processing input: received 1008 (policy violation)` ¹ß»ýÇÏ¸ç ¿¬°á Á¾·á.

### º¯°æ ³»¿ë
- `receive_from_client` ÀÔ·Â ·çÇÁ¸¦ `ws.receive_bytes()` -> `ws.receive()` ±â¹ÝÀ¸·Î ÀüÈ¯.
- ¼ö½Å ÇÁ·¹ÀÓ Å¸ÀÔ ºÐ±â Ã³¸®:
  - `websocket.disconnect` Áï½Ã Á¾·á
  - `websocket.receive` Áß `bytes`¸¸ ¿Àµð¿À ÀÔ·ÂÀ¸·Î Ã³¸®
  - text/control/non-binary ÇÁ·¹ÀÓÀº ¹«½Ã

### ±â´ë È¿°ú
- ÇÁ·¹ÀÓ Å¸ÀÔ ºÒÀÏÄ¡·Î ÀÎÇÑ policy violation(1008) ºóµµ °¨¼Ò.
- Start/Stop ¶Ç´Â ºê¶ó¿ìÀú Á¦¾î ÇÁ·¹ÀÓÀÌ ¼¯¿©µµ ¼¼¼Ç ¾ÈÁ¤¼º Çâ»ó.

## 2026-02-14 (°æ·Î ÁúÀÇ ¼±ÀÀ´ä¿¡¼­ À§Ä¡ ÀçÁú¹® ¹æÁö °­È­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ Â¡ÈÄ
- °æ·Î ´äº¯ ÀÚÃ¼´Â ¸ÂÁö¸¸, Ã¹ ¹®ÀåÀ¸·Î "ÇöÀç À§Ä¡ ¾Ë·Á´Þ¶ó"´Â ¹ßÈ­°¡ ¸ÕÀú ³ª¿À´Â ÄÉÀÌ½º Á¸Àç.

### ¿øÀÎ
- ½Ç½Ã°£ À½¼º ÀÀ´ä Å¸ÀÌ¹Ö °æÀïÀ¸·Î, µµ±¸ ÄÁÅØ½ºÆ® ¹Ý¿µ Àü¿¡ ¸ðµ¨ÀÌ ¼±ÀÀ´äÇÒ ¼ö ÀÖÀ½.

### º¯°æ ³»¿ë
- ½Ã½ºÅÛ ÁöÄ§ °­È­:
  - ÇÑ±¹¾î ±³Åë ÁúÀÇ¿¡¼­´Â »ç¿ëÀÚ À§Ä¡¸¦ Àý´ë ÀçÁú¹®ÇÏÁö ¾Êµµ·Ï ¸í½Ã.
  - ¼¼¼Ç ½ÃÀÛ ½Ã ¼­¹ö°¡ Àü´ÞÇÑ `lat/lng`¸¦ ½Ã½ºÅÛ ÁöÄ§¿¡ ¸í½ÃÀûÀ¸·Î ÁÖÀÔ.
- °æ·Î intent Ã³¸® ½ÃÀÛ ½Ã ¼±ÁÖÀÔ °¡µå Ãß°¡:
  - `[INTENT:location_guard] Device location is already known ... Do not ask user location.`
- Áö¿¬ ÇÊ·¯ Áö½Ã °­È­:
  - ÇÊ·¯ ¸àÆ® ´Ü°è¿¡¼­µµ À§Ä¡ Áú¹® ±ÝÁö ¹®±¸ Ãß°¡.

### ±â´ë È¿°ú
- Ã¹ ÀÀ´ä¿¡¼­ "À§Ä¡ ¾Ë·ÁÁÖ¼¼¿ä" ¼±¹ßÈ­ ºóµµ °¨¼Ò.
- °æ·Î ¾È³»°¡ À§Ä¡ Áú¹® ¾øÀÌ ¹Ù·Î º»·ÐÀ¸·Î ½ÃÀÛµÉ °¡´É¼º Çâ»ó.

## 2026-02-14 (¼¼¼Ç Áß »ç¿ëÀÚ À§Ä¡ º¯°æ ¹Ý¿µ)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`
- `temp_front/app/page.tsx`

### º¯°æ ÀÌÀ¯
- ±âÁ¸¿¡´Â WebSocket ¿¬°á ½ÃÁ¡ÀÇ `lat/lng`¸¸ »ç¿ëÇØ, ÀÌµ¿ Áß À§Ä¡ º¯°æÀÌ °æ·Î °è»ê¿¡ ¹Ý¿µµÇÁö ¾ÊÀ½.

### º¯°æ ³»¿ë
- ÇÁ·ÐÆ®(`temp_front/app/page.tsx`)
  - `location_update` ¸Þ½ÃÁö Àü¼Û ÇÔ¼ö Ãß°¡
  - WebSocket ¿¬°á Á÷ÈÄ 1È¸ À§Ä¡ Àü¼Û
  - ¿¬°á Áß 15ÃÊ ÁÖ±â À§Ä¡ Àü¼Û Å¸ÀÌ¸Ó Ãß°¡
  - `Start Speaking` Á÷Àü À§Ä¡ 1È¸ °»½Å Àü¼Û
  - ¿¬°á Á¾·á/¿À·ù/¾ð¸¶¿îÆ® ½Ã À§Ä¡ Å¸ÀÌ¸Ó Á¤¸®
- ¹é¿£µå(`backend/server.py`)
  - ¼¼¼Çº° `client_state(lat/lng)` µµÀÔ
  - `receive_from_client`¿¡¼­ text ÇÁ·¹ÀÓ(JSON) `type=location_update` ¼ö½Å ½Ã `client_state` °»½Å
  - °æ·Î °è»ê/°¡ÀÌµå¿¡¼­ °íÁ¤ `current_lat/lng` ´ë½Å ÃÖ½Å `client_state` »ç¿ë

### ±â´ë È¿°ú
- »ç¿ëÀÚ°¡ ÀÌµ¿ÇØµµ ´ÙÀ½ ÁúÀÇºÎÅÍ ÃÖ½Å À§Ä¡ ±âÁØ °æ·Î/µµÂøÁ¤º¸ °è»ê.
- "À§Ä¡°¡ ¹Ù²î¾ú´Âµ¥ ÀÌÀü À§Ä¡·Î ¾È³»" ¹®Á¦ ¿ÏÈ­.

## 2026-02-14 (À§Ä¡ °»½Å ÁÖ±â Á¶Á¤)

### ´ë»ó ÆÄÀÏ
- `temp_front/app/page.tsx`

### º¯°æ ³»¿ë
- WebSocket ¿¬°á Áß ÁÖ±â À§Ä¡ ¾÷µ¥ÀÌÆ® °£°ÝÀ» `15ÃÊ`¿¡¼­ `60ÃÊ(1ºÐ)`·Î º¯°æ.
- ¿¬°á Á÷ÈÄ 1È¸ Àü¼Û, Start Speaking Á÷Àü 1È¸ Àü¼Û ·ÎÁ÷Àº À¯Áö.

### ±â´ë È¿°ú
- À§Ä¡ API È£Ãâ ºóµµ °¨¼Ò·Î Å¬¶óÀÌ¾ðÆ®/¹èÅÍ¸® ºÎ´ã ¿ÏÈ­.
- ¿©ÀüÈ÷ ´ëÈ­ ½ÃÀÛ Á÷Àü À§Ä¡´Â ÃÖ½Å »óÅÂ·Î ¹Ý¿µ.

## 2026-02-14 (¼±¹ßÈ­/Áßº¹ ÀÀ´ä ¿ÏÈ­: ÇÊ·¯ ¿É¼ÇÈ­ + STT Áßº¹ µðµàÇÁ)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ Â¡ÈÄ
- °æ·Î ÁúÀÇ ½Ã ¸ðµ¨ÀÌ ¸ÕÀú "Á¤º¸ ¾øÀ½/À§Ä¡ ÇÊ¿ä" °°Àº ¼±¹ßÈ­¸¦ ÇÏ°Å³ª,
  À¯»çÇÑ °æ·Î ´äº¯ÀÌ 2È¸ Ãâ·ÂµÇ´Â ÄÉÀÌ½º°¡ °£Çæ ¹ß»ý.

### º¯°æ ³»¿ë
- ÇÊ·¯ ¸àÆ® ¿É¼ÇÈ­:
  - `ENABLE_TRANSIT_FILLER` È¯°æº¯¼ö Ãß°¡(±âº» `false`)
  - ±âº»°ª¿¡¼­ ÇÊ·¯ º°µµ ÅÏÀ» ºñÈ°¼ºÈ­ÇØ ÀÌÁß ÀÀ´ä °¡´É¼º Ãà¼Ò
  - ÇÊ¿ä ½Ã `.env`¿¡¼­ `ENABLE_TRANSIT_FILLER=true`·Î ÀçÈ°¼º °¡´É
- STT »ç¿ëÀÚ ÅÏ µðµàÇÁ Ãß°¡:
  - Azure STTÀÇ ±ÙÁ¢ Áßº¹ final chunk¸¦ 1.5ÃÊ À©µµ¿ì¿¡¼­ ½ºÅµ
  - ·Î±×: `[IntentRouter] skip duplicate user turn: ...`

### ±â´ë È¿°ú
- °°Àº Áú¹®¿¡ ´ëÇÑ Áßº¹ °æ·Î ¾È³» ºóµµ °¨¼Ò.
- ÄÁÅØ½ºÆ® ¹Ý¿µ Àü ¼±ÀÀ´ä(ºÒÈ®½Ç ¸àÆ®) ¹ß»ý ºóµµ ¿ÏÈ­.

## 2026-02-14 (¼±¹ßÈ­/Áßº¹ ÀÀ´ä Ãß°¡ ¿ÏÈ­: Gemini Á÷Á¢ ¿Àµð¿À ÀÔ·Â OFF ±âº»)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ Â¡ÈÄ
- °æ·Î ÁúÀÇ¿¡¼­ ¸ðµ¨ÀÌ ¸ÕÀú "ºÒ°¡/Á¤º¸ ¾øÀ½"À» ¸»ÇÑ µÚ, µÚ´Ê°Ô ¿Ã¹Ù¸¥ Á¤º¸¸¦ ÀçÀÀ´ä.
- À§Ä¡ ¾÷µ¥ÀÌÆ® ·Î±×°¡ ´Ù¼ö ¹Ýº¹ Ãâ·Â.

### ¿øÀÎ
- ¸¶ÀÌÅ© ¿Àµð¿À°¡ Gemini·Î Á÷Á¢ µé¾î°¡´Â °æ·Î¿Í Azure STT ±â¹Ý ÄÁÅØ½ºÆ® °æ·Î°¡ µ¿½Ã¿¡ Á¸ÀçÇØ,
  ÄÁÅØ½ºÆ® ¹Ý¿µ Àü ¼±ÀÀ´ä/Áßº¹ ÅÏÀÌ ¹ß»ýÇÒ ¼ö ÀÖÀ½.

### º¯°æ ³»¿ë
- ÀÔ·Â °æ·Î ´Ü¼øÈ­:
  - `GEMINI_DIRECT_AUDIO_INPUT` È¯°æº¯¼ö µµÀÔ(±âº» `false`)
  - ±âº»°ª¿¡¼­ Gemini `send_realtime_input(audio=...)` ºñÈ°¼ºÈ­
  - Azure STT ÅØ½ºÆ®¸¦ ´ÜÀÏ ÀÔ·Â °æ·Î·Î »ç¿ë
- ÀÏ¹Ý ´ëÈ­ ÀÀ´ä À¯Áö:
  - non-routing intent´Â `_send_user_text_turn(text)`·Î ÅØ½ºÆ® ÅÏÀ» Á÷Á¢ Àü´Þ
- À§Ä¡ ·Î±× ³ëÀÌÁî ¿ÏÈ­:
  - `location_update` ¼ö½Å ½Ã ÁÂÇ¥´Â Ç×»ó °»½ÅÇÏµÇ,
  - ·Î±×´Â ÀÌµ¿·®ÀÌ ¾à 25m ÀÌ»óÀÏ ¶§¸¸ Ãâ·Â

### ±â´ë È¿°ú
- °æ·Î ÁúÀÇ ¼±¹ßÈ­/Áßº¹ ÀÀ´ä ºóµµ Ãß°¡ °¨¼Ò.
- ÄÜ¼Ö À§Ä¡ ·Î±× °ú´Ù Ãâ·Â ¿ÏÈ­.

## 2026-02-14 (Direct audio À¯Áö ÀüÁ¦·Î Áßº¹/¼±¹ßÈ­ ¿ÏÈ­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- STT ºÎÁ¤È®¼º ¶§¹®¿¡ Gemini direct audio ÀÔ·ÂÀº À¯Áö°¡ ÇÊ¿äÇÔ.
- ¹®Á¦´Â direct audio + ÅØ½ºÆ® ÅÏ °­Á¦(complete_turn) º´ÇàÀ¸·Î ÀÎÇÑ ÀÌÁß ÀÀ´ä/¼±¹ßÈ­.

### º¯°æ ³»¿ë
- `GEMINI_DIRECT_AUDIO_INPUT` ±âº»°ªÀ» `true`·Î º¯°æ.
- direct audio È°¼º ½Ã:
  - °æ·Î ÄÁÅØ½ºÆ® ÁÖÀÔÀÇ `complete_turn` °­Á¦¸¦ ºñÈ°¼ºÈ­(º¸Á¶ ÄÁÅØ½ºÆ®·Î¸¸ ÁÖÀÔ)
  - ÇÊ·¯ ¸àÆ® º°µµ ÅÏ °­Á¦ ºñÈ°¼ºÈ­
  - non-routing ÀÏ¹Ý´ëÈ­¿ë `_send_user_text_turn` °­Á¦ È£Ãâ ºñÈ°¼ºÈ­
- °á°úÀûÀ¸·Î direct audio °æ·Î¸¦ ¸ÞÀÎ ÀÀ´ä Ã¤³Î·Î À¯ÁöÇÏ¸é¼­,
  ÅØ½ºÆ® ÅÏ Æ®¸®°Å°¡ Ãß°¡ ÀÀ´äÀ» ¸¸µå´Â °æ·Î¸¦ Â÷´Ü.

### ±â´ë È¿°ú
- "¸ÕÀú ºÒ°¡ ¸àÆ® + µÚ´ÊÀº Á¤´ä"/Áßº¹ ÀÀ´ä ºóµµ °¨¼Ò.
- STT ÀÎ½Ä ¿ÀÂ÷¸¦ º¸¿ÏÇÏ±â À§ÇØ direct audio ÀÔ·ÂÀº ±×´ë·Î À¯Áö.

## 2026-02-14 (°æ·Î ´äº¯ µÚ Ãß°¡ "ºÒ°¡/È®ÀÎ" ¸àÆ® ¾ïÁ¦)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ Â¡ÈÄ
- ¿Ã¹Ù¸¥ °æ·Î ¾È³» ÈÄ °°Àº ÅÏ¿¡¼­ "½Ç½Ã°£ Á¤º¸ Á¦°ø ¾î·Á¿ò" °°Àº »óÃæ ¹®ÀåÀÌ µÚÀÌ¾î Ãâ·Â.

### º¯°æ ³»¿ë
- °æ·Î intent(`subway_route`, `bus_route`, `commute_overview`)ÀÇ per-turn ACTION Áö½Ã °­È­:
  - ÇÑ ¹øÀÇ ÃÖÁ¾ ´äº¯¸¸ Á¦°ø
  - ´äº¯ ÈÄ ºÒÈ®½Ç¼º/Ãß°¡ Áú¹® ¹®Àå ±ÝÁö
  - Á¦°øµÈ ¿ä¾à¿¡ ¸í½ÃÀû µ¥ÀÌÅÍ ´©¶ôÀÌ ¾øÀ¸¸é "½Ç½Ã°£ Á¦°ø ºÒ°¡" ¹®±¸ ±ÝÁö

### ±â´ë È¿°ú
- "Á¤´ä -> °ð¹Ù·Î ºÎÁ¤" ÇüÅÂÀÇ »óÃæ ÀÀ´ä ºóµµ °¨¼Ò.
- °æ·Î ÀÀ´äÀÌ ÇÑ ¹ø¿¡ ¸¶¹«¸®µÇµµ·Ï ¾ÈÁ¤È­.

## 2026-02-14 (°æ·Î ¿ä¾à ¿ì¼± ÀÀ´ä º¸Àå: transit turn gate µµÀÔ)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ Â¡ÈÄ
- `live context built ... summary_ok=True`ÀÎµ¥µµ ¸ðµ¨ÀÌ "¸ð¸¥´Ù/¶óÀÌºê ÄÁÅØ½ºÆ® ¾øÀ½"À» ¸ÕÀú ¸»ÇÏ´Â ÄÉÀÌ½º.

### ¿øÀÎ
- Gemini direct-audio ÀÔ·ÂÀÌ ÄÁÅØ½ºÆ® ÅÏº¸´Ù ¸ÕÀú Ã³¸®µÇ¾î,
  ÄÁÅØ½ºÆ® ¹Ì¹Ý¿µ »óÅÂ ÀÀ´äÀÌ ¸ÕÀú »ý¼ºµÉ ¼ö ÀÖÀ½.

### º¯°æ ³»¿ë
- `transit_turn_gate` »óÅÂ Ãß°¡:
  - °æ·Î intent(`subway_route`,`bus_route`,`commute_overview`) °¨Áö ½Ã gate¸¦ ¾à 2.5ÃÊ ¼³Á¤
- gate È°¼º µ¿¾È:
  - `receive_from_client`¿¡¼­ Gemini direct audio Àü¼Û ÀÏ½Ã º¸·ù
- °æ·Î intent ÄÁÅØ½ºÆ® ÁÖÀÔ:
  - `complete_turn=True`·Î °­Á¦ÇØ ¿ä¾à ÄÁÅØ½ºÆ® ÅÏÀ» ¿ì¼± Ã³¸®
  - ACTION Áö½Ã °­È­: "summary exists¸é ±×°É ¿ì¼± »ç¿ëÇØ Á÷Á¢ ´äº¯"

### ±â´ë È¿°ú
- ¿Ã¹Ù¸¥ °æ·Î ¿ä¾àÀÌ ¸ÕÀú/´ÜÀÏ·Î ¹ßÈ­µÉ È®·ü »ó½Â.
- "Á¤´ä µÚ¿¡ ¸ð¸¥´Ù" ¶Ç´Â "¸ð¸¥´Ù¸¸ ¸»ÇÔ" ÄÉÀÌ½º ¿ÏÈ­.
