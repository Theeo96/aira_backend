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

## 2026-02-13 (Seoul module ë°˜ì˜ ì‘ì—…)

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
- ê¸°ì¡´ `/ws/audio` ì‹¤ì‹œê°„ ìŒì„± ë£¨í”„ë¥¼ ê±´ë“œë¦¬ì§€ ì•Šê³ , `seoul_info_module` ê¸°ëŠ¥ì„ ì¦‰ì‹œ ì‚¬ìš©í•  ìˆ˜ ìˆëŠ” ìµœì†Œ í†µí•© ì§€ì ì„ ë§Œë“¤ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- import ì¶”ê°€:
  - `Body` from `fastapi`
  - `build_seoul_info_packet`, `build_speech_summary` from `modules.seoul_info_module`
- ì‹ ê·œ ì—”ë“œí¬ì¸íŠ¸ ì¶”ê°€:
  - `POST /api/seoul-info/normalize`
  - ìš”ì²­ ë°”ë””ì—ì„œ `voicePayload`, `odsayPayload`ë¥¼ ë°›ì•„ íŒ¨í‚· ì •ê·œí™” ë° ë°œí™” ìš”ì•½ ìƒì„± í›„ ë°˜í™˜
  - ì‘ë‹µ êµ¬ì¡°:
    - `packet`: ì •ê·œí™” ê²°ê³¼
    - `speechSummary`: ì‚¬ìš©ì ë°œí™”ìš© ìš”ì•½ ë¬¸ì¥

### ê¸°ëŠ¥ ëª©ì 
- ì™¸ë¶€/í”„ë¡ íŠ¸ì—ì„œ ìˆ˜ì§‘í•œ ì„œìš¸ ê´€ë ¨ raw payloadë¥¼ ì„œë²„ì—ì„œ ì¼ê´€ëœ ìŠ¤í‚¤ë§ˆë¡œ ì •ê·œí™”
- ì •ê·œí™” ê²°ê³¼ ê¸°ë°˜ TTS/ì‘ë‹µìš© ìš”ì•½ ë¬¸ì¥ì„ ì¦‰ì‹œ ìƒì„± ê°€ëŠ¥í•˜ê²Œ í•¨

## 2026-02-13 (ìŒì„± ì‘ë‹µ ìŠ¤íƒ€ì¼ ì¡°ì •)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ìŒì„± ëª¨ë¸ì´ ì •ë³´ë¥¼ í•„ë“œ ë‚˜ì—´ ë°©ì‹ìœ¼ë¡œ ì½ì§€ ì•Šê³ , ì‚¬ìš©ìì—ê²Œ ì¹œê·¼í•˜ê³  ìš”ì•½ëœ ë°©ì‹ìœ¼ë¡œ ì „ë‹¬ë˜ë„ë¡ ì‘ë‹µ ìŠ¤íƒ€ì¼ì„ ê°•ì œí•˜ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- `system_instruction` ê¸°ë³¸ ë¬¸êµ¬ë¥¼ í™•ì¥:
  - raw ë°ì´í„°/í•„ë“œ ë¤í”„ ê¸ˆì§€
  - ìì—°ìŠ¤ëŸ¬ìš´ í•œêµ­ì–´ êµ¬ì–´ì²´ ìš”ì•½
  - í•µì‹¬ ì •ë³´ ìš°ì„  ì „ë‹¬
  - ì •ë³´ê°€ ë§ìœ¼ë©´ ì§§ì€ ê°œìš” + í›„ì† ì§ˆë¬¸ 1ê°œ

### ê¸°ëŠ¥ ëª©ì 
- ì‹¤ì œ ìŒì„± ì‘ë‹µ í’ˆì§ˆ ê°œì„  (ê°€ë…ì„±/ì²­ì·¨ì„±)
- ë™ì¼ ë°ì´í„°ë¼ë„ ì‚¬ìš©ì ì¹œí™”ì ì¸ ì „ë‹¬ ë°©ì‹ìœ¼ë¡œ ì¼ê´€í™”

## 2026-02-13 (/ws/audio ì„œìš¸ ì»¨í…ìŠ¤íŠ¸ ì—°ê²°)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ì„œìš¸ ì •ë³´ ëª¨ë“ˆ ê²°ê³¼ë¥¼ ì‹¤ì œ ìŒì„± ëŒ€í™” ê²½ë¡œ(`/ws/audio`)ì—ë„ ë°˜ì˜í•˜ê¸° ìœ„í•´.
- ê¸°ì¡´ ì˜¤ë””ì˜¤ ìŠ¤íŠ¸ë¦¬ë° êµ¬ì¡°ë¥¼ ìœ ì§€í•˜ë©´ì„œ ìµœì†Œí•œì˜ ì…ë ¥ í™•ì¥ìœ¼ë¡œ ì—°ê²°í•˜ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- WebSocket ì¿¼ë¦¬ íŒŒë¼ë¯¸í„° `seoul_summary` ìˆ˜ì‹  ì¶”ê°€
- `system_instruction` ìƒì„± ì‹œ, `seoul_summary`ê°€ ìˆìœ¼ë©´ ì»¨í…ìŠ¤íŠ¸ ë¸”ë¡ìœ¼ë¡œ ì£¼ì…:
  - `[SEOUL SUMMARY CONTEXT] ...`
  - ìì—°ìŠ¤ëŸ¬ìš´ ì„¤ëª… ìš°ì„  ì§€ì‹œ

### ê¸°ëŠ¥ ëª©ì 
- ìŒì„± ì‘ë‹µì´ ì„œìš¸ ì •ë³´ ë§¥ë½ì„ ë°˜ì˜í•˜ë„ë¡ ì—°ê²°
- `/api/seoul-info/normalize` ê²°ê³¼ë¥¼ `/ws/audio` ëŒ€í™” í’ˆì§ˆ í–¥ìƒì— ì¬ì‚¬ìš© ê°€ëŠ¥í•˜ê²Œ í•¨

## 2026-02-13 (/ws/audio ì»¨í…ìŠ¤íŠ¸ ëˆ„ë½ ëŒ€ì‘ ê°•í™”)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- í”„ë¡ íŠ¸ì—ì„œ `seoul_summary`ë¥¼ ì „ë‹¬í•˜ì§€ ì•ŠëŠ” ê²½ìš° ëª¨ë¸ì´ ê¸°ëŠ¥ ë¶€ì¬ì²˜ëŸ¼ ë‹µí•˜ëŠ” ë¬¸ì œë¥¼ ì¤„ì´ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- `seoul_summary` ì¿¼ë¦¬ê°’ì´ ì—†ìœ¼ë©´ `.env`ì˜ `SEOUL_SUMMARY`ë¥¼ fallbackìœ¼ë¡œ ì‚¬ìš©
- `system_instruction`ì— ê±°ì ˆí˜• ë‹µë³€ ì–µì œ ê·œì¹™ ì¶”ê°€:
  - "I cannot access that data"ë¥˜ ë¬¸êµ¬ ì§€ì–‘
  - ì»¨í…ìŠ¤íŠ¸ê°€ ë¶€ë¶„ì ì¼ ë•Œë„ ê°€ì • ê¸°ë°˜ìœ¼ë¡œ ë„ì›€ë˜ëŠ” ë‹µë³€ + í™•ì¸ ì§ˆë¬¸ 1ê°œ

### ê¸°ëŠ¥ ëª©ì 
- ì„œìš¸ ì •ë³´ ì»¨í…ìŠ¤íŠ¸ ëˆ„ë½ ìƒí™©ì—ì„œë„ ì‚¬ìš©ì ì²´ê° ì‘ë‹µ í’ˆì§ˆ ìœ ì§€
- ìŒì„± ì‘ë‹µì´ "ëª»í•¨" ìœ„ì£¼ë¡œ ë¹ ì§€ëŠ” í˜„ìƒ ì™„í™”

## 2026-02-13 (ê¸°ë³¸ ì»¨í…ìŠ¤íŠ¸ fallback ì œê±°)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- í…ŒìŠ¤íŠ¸ ëª©í‘œê°€ "ì‚¬ìš©ì ìŒì„± ê¸°ë°˜ ë™ì‘ ê²€ì¦"ì´ë¯€ë¡œ, `.env` ê¸°ë³¸ ì»¨í…ìŠ¤íŠ¸ ì£¼ì…ì´ ê²°ê³¼ë¥¼ ì˜¤ì—¼ì‹œí‚¤ì§€ ì•Šë„ë¡ ì œê±°.

### ë³€ê²½ ë‚´ìš©
- `/ws/audio`ì—ì„œ `seoul_summary` ë¯¸ì „ë‹¬ ì‹œ `.env`ì˜ `SEOUL_SUMMARY`ë¥¼ ì‚¬ìš©í•˜ëŠ” fallback ë¡œì§ ì‚­ì œ.
- ì´ì œ ì„œìš¸ ì»¨í…ìŠ¤íŠ¸ëŠ” í´ë¼ì´ì–¸íŠ¸ê°€ ëª…ì‹œì ìœ¼ë¡œ ì „ë‹¬í•œ ê²½ìš°ì—ë§Œ ì‚¬ìš©ë¨.

### ê¸°ëŠ¥ ëª©ì 
- ìŒì„± ì…ë ¥ ê¸°ë°˜ í…ŒìŠ¤íŠ¸ì˜ ìˆœìˆ˜ì„± í™•ë³´
- ê¸°ë³¸ê°’ ì£¼ì…ìœ¼ë¡œ ì¸í•œ ì˜¤íƒ/ê³¼ì í•© ì‘ë‹µ ë°©ì§€

## 2026-02-13 (ì¢Œí‘œ/ì—´ì°¨ ë„ì°©ì •ë³´ ì‹¤ì—°ë™)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`
- `temp_front/app/page.tsx`

### ë³€ê²½ ì´ìœ 
- ê¸°ì¡´ì—ëŠ” `seoul_info_module` ì •ê·œí™” ë¡œì§ë§Œ ìˆê³ , ì‹¤ì œ ì¢Œí‘œ ìˆ˜ì§‘ ë° ì‹¤ì‹œê°„ ì—´ì°¨ ë„ì°© API í˜¸ì¶œ ê²½ë¡œê°€ ì—°ê²°ë˜ì§€ ì•Šì•„
  "í˜„ì¬ ì¢Œí‘œ/ì—´ì°¨ ë„ì°©ì‹œê°„ì„ ëª» ë°›ëŠ”" ì¦ìƒì´ ë°œìƒí–ˆê¸° ë•Œë¬¸.

### ë³€ê²½ ë‚´ìš©
- `backend/server.py`
  - `GET /api/seoul-info/live` ì‹ ê·œ ì¶”ê°€
  - ì…ë ¥: `lat`, `lng`, `station`(optional)
  - ì²˜ë¦¬:
    - ì¢Œí‘œê°€ ìˆìœ¼ë©´ ODSAY `pointSearch`ë¡œ ì¸ê·¼ ì—­ ì¶”ì •
    - ì¶”ì •/ì…ë ¥ëœ ì—­ëª…ìœ¼ë¡œ ì„œìš¸ì‹œ `realtimeStationArrival` í˜¸ì¶œ
    - ìŒì„± ì „ë‹¬ìš© ìš”ì•½(`speechSummary`) + ì›ë³¸ ë„ì°©ëª©ë¡(`arrivals`) ë°˜í™˜
- `temp_front/app/page.tsx`
  - Connect ì‹œ ë¸Œë¼ìš°ì € geolocationìœ¼ë¡œ í˜„ì¬ ì¢Œí‘œ íšë“ ì‹œë„
  - `/api/seoul-info/live` í˜¸ì¶œí•´ `speechSummary`ë¥¼ ë°›ì•„ `/ws/audio` ì¿¼ë¦¬ì˜ `seoul_summary`ë¡œ ì£¼ì…
  - geolocation/API ì‹¤íŒ¨ ì‹œ ê¸°ì¡´ì²˜ëŸ¼ ë¡œì»¬ ì €ì¥ëœ `seoul_summary` fallback

### ê¸°ëŠ¥ ëª©ì 
- ì‚¬ìš©ì ì‹¤ì œ í˜„ì¬ ìœ„ì¹˜ ê¸°ë°˜ì˜ ì—­/ë„ì°©ì •ë³´ë¥¼ ìŒì„± ëª¨ë¸ ì»¨í…ìŠ¤íŠ¸ë¡œ ìë™ ë°˜ì˜
- "ëª»í•œë‹¤" ì‘ë‹µ ëŒ€ì‹ , ì‹¤ì‹œê°„ ë°ì´í„° ê¸°ë°˜ ì•ˆë‚´ ê°€ëŠ¥ì„± í™•ë³´

## 2026-02-13 (ì‹¤ì‹œê°„ ì‘ë‹µ ì‹¤íŒ¨ ì™„í™”: ì¤‘ë³µ ì—°ê²°/ì»¨í…ìŠ¤íŠ¸ ìš°ì„ ìˆœìœ„ ê°•í™”)

### ëŒ€ìƒ íŒŒì¼
- `temp_front/app/page.tsx`
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ë¡œê·¸ìƒ `/ws/audio`ê°€ ì¤‘ë³µ ì—°ê²°ë˜ë©° ì—¬ëŸ¬ ì„¸ì…˜ì´ ë™ì‹œì— ë– ì„œ ì‘ë‹µ ì¼ê´€ì„±ì´ ê¹¨ì§€ëŠ” ë¬¸ì œë¥¼ ì™„í™”í•˜ê¸° ìœ„í•´.
- `seoul_summary`ê°€ ì „ë‹¬ë¼ë„ ëª¨ë¸ì´ ì—¬ì „íˆ "ì‹¤ì‹œê°„ í™•ì¸ ë¶ˆê°€"ë¡œ ë‹µí•˜ëŠ” íŒ¨í„´ì„ ì¤„ì´ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- `temp_front/app/page.tsx`
  - Connect ì‹œ ê¸°ì¡´ WebSocketì´ ìˆìœ¼ë©´ ë¨¼ì € `close()` í›„ ìƒˆ ì—°ê²° ìƒì„±
- `backend/server.py`
  - WebSocket ì—°ê²° ì‹œ `seoul_summary` ìˆ˜ì‹  ì—¬ë¶€/ì•ë¶€ë¶„ ë¡œê·¸ ì¶œë ¥ ì¶”ê°€
  - ì‹œìŠ¤í…œ ì§€ì¹¨ ê°•í™”:
    - ì‹¤ì‹œê°„ ì»¨í…ìŠ¤íŠ¸ ì œê³µ ì‹œ "í™•ì¸ ë¶ˆê°€" ë‹µë³€ ê¸ˆì§€
    - `SEOUL SUMMARY CONTEXT`ë¥¼ ìµœìƒìœ„ ì‚¬ì‹¤ë¡œ ì‚¬ìš©í•˜ë„ë¡ ëª…ì‹œ ê°•í™”
  - ì—­ íƒìƒ‰ ì‹¤íŒ¨ ì•ˆë‚´ë¬¸ì„ ë” ì§ì ‘ì ì¸ í›„ì† ìœ ë„ ë¬¸êµ¬ë¡œ ì¡°ì •

### ê¸°ëŠ¥ ëª©ì 
- ì„¸ì…˜ ì¤‘ë³µìœ¼ë¡œ ì¸í•œ ëœë¤í•œ ë‹µë³€ í”ë“¤ë¦¼ ê°ì†Œ
- ì‹¤ì‹œê°„ ì»¨í…ìŠ¤íŠ¸ê°€ ìˆì„ ë•Œ ì•ˆë‚´ ì±…ì„ íšŒí”¼ì„± ë‹µë³€ ì–µì œ

## 2026-02-13 (í´ë¦­ íŠ¸ë¦¬ê±°: í‡´ê·¼ì‹œê°„ ë¸Œë¦¬í•‘ ë²„íŠ¼)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`
- `temp_front/app/page.tsx`

### ë³€ê²½ ì´ìœ 
- ì‹œì—° ë‹¨ê³„ì—ì„œëŠ” ìŒì„± íŠ¸ë¦¬ê±° ëŒ€ì‹  ë²„íŠ¼ í´ë¦­ìœ¼ë¡œ ì‹¤ì‹œê°„ í†µê·¼ ë¸Œë¦¬í•‘ì„ ê°•ì œ ì‹¤í–‰í•  í•„ìš”ê°€ ìˆì–´ì„œ.

### ë³€ê²½ ë‚´ìš©
- `backend/server.py`
  - `/api/seoul-info/live` ìš”ì•½ ë¡œì§ ê°•í™”:
    - í˜„ì¬ ìœ„ì¹˜ ê¸°ì¤€ ì¸ê·¼ì—­ ì¡°íšŒ(ODSAY)
    - ì‹¤ì‹œê°„ ë„ì°©ì •ë³´ ì¡°íšŒ(ì„œìš¸ì‹œ API)
    - `firstEtaMinutes`, `nextEtaMinutes`, `walkToStationMinutes`, `decision` ê³„ì‚°
    - ë¸Œë¦¬í•‘ ë¬¸ì¥ì„ "ì´ë²ˆ ì—´ì°¨/ë‹¤ìŒ ì—´ì°¨ + ë„ë³´ ì‹œê°„ + íƒ‘ìŠ¹ íŒë‹¨" í˜•íƒœë¡œ ìƒì„±
- `temp_front/app/page.tsx`
  - `í‡´ê·¼ì‹œê°„ ë¸Œë¦¬í•‘` ë²„íŠ¼ ì¶”ê°€ (ë¹„ì—°ê²°/ì—°ê²° ìƒíƒœ ëª¨ë‘ í‘œì‹œ)
  - ë²„íŠ¼ í´ë¦­ ì‹œ geolocation + `/api/seoul-info/live` í˜¸ì¶œ
  - ìƒì„±ëœ `speechSummary`ë¥¼ `localStorage.seoul_summary`ì— ì €ì¥ í›„ WS ì¬ì—°ê²°
  - ë¸Œë¦¬í•‘ ë¬¸ì¥ì„ ëŒ€í™”ì°½ì—ë„ í‘œì‹œí•´ ì¦‰ì‹œ í™•ì¸ ê°€ëŠ¥

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
- ODSAY ì‘ë‹µ íŒŒì‹± ë¡œì§ í™•ì¥:
  - `result.station` ì™¸ì— `stationInfo`, `stations` ë“± ë³€í˜• í‚¤ ëŒ€ì‘
  - ì—­ëª…/ì¢Œí‘œ í‚¤(`stationName`, `stationNm`, `x/y`, `gpsX/gpsY`) ìœ ì—° íŒŒì‹±
- ODSAY íƒìƒ‰ ì „ëµ í™•ì¥:
  - ë°˜ê²½ 800m -> 1500m -> 3000m ìˆœì°¨ ì¬ì‹œë„
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
  - WebSocket ì´ë²¤íŠ¸ í•¸ë“¤ëŸ¬ì—ì„œ í˜„ì¬ í™œì„± ì†Œì¼“ ì¸ìŠ¤í„´ìŠ¤ì¸ì§€ í™•ì¸ í›„ ìƒíƒœ ê°±ì‹ 
    - êµ¬ ì†Œì¼“ì˜ ì§€ì—° `onclose`ê°€ ì‹ ê·œ ì†Œì¼“ ìƒíƒœë¥¼ ë®ì–´ì“°ì§€ ì•Šë„ë¡ ì²˜ë¦¬
  - `í‡´ê·¼ì‹œê°„ ë¸Œë¦¬í•‘` í´ë¦­ ì‹œ ì´ë¯¸ ì—°ê²° ì¤‘ì´ë©´ ì¬ì—°ê²°í•˜ì§€ ì•Šê³  ë¸Œë¦¬í•‘ë§Œ ê°±ì‹ 
- `backend/server.py`
  - ETA íŒŒì‹± ë³´ì •:
    - `barvlDt > 0` ìš°ì„  ì‚¬ìš©
    - `0ë¶„` ì²˜ë¦¬ëŠ” ì²« ì—´ì°¨ì—ëŠ” í—ˆìš©, ë‹¤ìŒ ì—´ì°¨ì—ëŠ” ë³´ìˆ˜ì ìœ¼ë¡œ ì œí•œ
    - `next_eta <= first_eta`ì¸ ë¹„ì •ìƒ ì¼€ì´ìŠ¤ëŠ” ë¬´íš¨ ì²˜ë¦¬
  - ë‹¤ìŒ ì—´ì°¨ ETAê°€ ë¶ˆí™•ì‹¤í•  ë•Œë„ ë¬¸ì¥ì„ ìì—°ìŠ¤ëŸ½ê²Œ ìƒì„±í•˜ë„ë¡ ë¶„ê¸° ì¶”ê°€

### ê¸°ëŠ¥ ëª©ì 
- ë¸Œë¦¬í•‘ ë²„íŠ¼ í´ë¦­ ì‹œ í†µì‹  ëŠê¹€ ì²´ê° ìµœì†Œí™”
- "ì´ë²ˆ/ë‹¤ìŒ ì—´ì°¨" ë‚¨ì€ ì‹œê°„ ì•ˆë‚´ì˜ í˜„ì‹¤ì„± í–¥ìƒ

## 2026-02-13 (ë²„íŠ¼ ë™ì‘ ë¶„ë¦¬ + ë¸Œë¦¬í•‘ ì¦‰ì‹œ ìŒì„± ì¶œë ¥)

### ëŒ€ìƒ íŒŒì¼
- `temp_front/app/page.tsx`

### ë³€ê²½ ì´ìœ 
- `í‡´ê·¼ì‹œê°„ ë¸Œë¦¬í•‘` í´ë¦­ ì‹œ Connect ë™ì‘ê³¼ ì„ì—¬ ë³´ì´ëŠ” ì²´ê°ì„ ì œê±°í•˜ê¸° ìœ„í•´.
- ë¸Œë¦¬í•‘ ê²°ê³¼ê°€ í…ìŠ¤íŠ¸ë§Œ í‘œì‹œë˜ê³  ìŒì„± ì‘ë‹µì´ ì—†ëŠ” ë¬¸ì œë¥¼ í•´ê²°í•˜ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- `triggerCommuteBriefing`ì—ì„œ WebSocket ì—°ê²°/ì¬ì—°ê²° í˜¸ì¶œ ì œê±°
  - ì´ì œ ë¸Œë¦¬í•‘ ë²„íŠ¼ì€ "ì‹¤ì‹œê°„ ì¡°íšŒ + ìš”ì•½ ìƒì„±"ë§Œ ìˆ˜í–‰
- ë¸Œë¦¬í•‘ ì™„ë£Œ ì‹œ ë¸Œë¼ìš°ì € `speechSynthesis`ë¡œ ì¦‰ì‹œ ìŒì„± ì¶œë ¥ ì¶”ê°€
  - `ko-KR` ì„¤ì •ìœ¼ë¡œ ìš”ì•½ ë¬¸ì¥ì„ ë°”ë¡œ ì½ì–´ì¤Œ

### ê¸°ëŠ¥ ëª©ì 
- ë²„íŠ¼ ê°„ ì—­í•  ë¶„ë¦¬ ëª…í™•í™” (Connect vs Briefing)
- ë¸Œë¦¬í•‘ ë²„íŠ¼ ë‹¨ë… í´ë¦­ ì‹œì—ë„ ìŒì„± í”¼ë“œë°± ë³´ì¥

## 2026-02-13 (ë¸Œë¦¬í•‘ ë²„íŠ¼ ì œê±° + ë¹„í—ˆìš© ì¶”ì • ì‘ë‹µ ì°¨ë‹¨)

### ëŒ€ìƒ íŒŒì¼
- `temp_front/app/page.tsx`
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ìŒì„± í…ŒìŠ¤íŠ¸ íë¦„ ë‹¨ìˆœí™”ë¥¼ ìœ„í•´ `í‡´ê·¼ì‹œê°„ ë¸Œë¦¬í•‘` ë²„íŠ¼ì„ ì œê±°í•˜ê¸° ìœ„í•´.
- ì‚¬ìš©ìê°€ ì§€ì í•œ "ìµœë‹¨ê²½ë¡œ/ë°©í–¥/ë‚ ì”¨/ëŒ€ê¸°ì§ˆì„ ì§€ì–´ë‚´ëŠ” ë‹µë³€"ì„ ì¤„ì´ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- `temp_front/app/page.tsx`
  - `í‡´ê·¼ì‹œê°„ ë¸Œë¦¬í•‘` ë²„íŠ¼ UI ì œê±° (ë¹„ì—°ê²°/ì—°ê²° ìƒíƒœ ëª¨ë‘)
  - ê´€ë ¨ í•¸ë“¤ëŸ¬(`triggerCommuteBriefing`) ì œê±°
  - ìŒì„± í…ŒìŠ¤íŠ¸ëŠ” `Connect` + `Start Speaking` íë¦„ìœ¼ë¡œë§Œ ë™ì‘
- `backend/server.py`
  - ì‹¤ì‹œê°„ ë¸Œë¦¬í•‘ ë¬¸êµ¬ì—ì„œ "ì§‘ìœ¼ë¡œ ê°€ì‹œë ¤ë©´ ... íƒ€ì‹œë©´ ë¼ìš”" ê°™ì€ ì¶”ì •ì„± í‘œí˜„ ì œê±°
  - `system_instruction` ê°•í™”:
    - live contextì— ì—†ëŠ” ì‚¬ì‹¤ì€ ë§í•˜ì§€ ì•Šê¸°
    - ë°ì´í„° ë¶€ì¡± ì‹œ ë¶€ì¡±í•œ í•­ëª©ì„ ëª…ì‹œí•˜ê³  í™•ì¸ ì§ˆë¬¸ 1ê°œ
    - ìµœë‹¨ê²½ë¡œ/ë°©í–¥/ETA/ë‚ ì”¨/ëŒ€ê¸°ì§ˆ ê°’ ì„ì˜ ìƒì„± ê¸ˆì§€

### ê¸°ëŠ¥ ëª©ì 
- ìŒì„± ë°ëª¨ íë¦„ ë‹¨ìˆœí™”
- API ë¯¸ì—°ë™ ë°ì´í„°ì— ëŒ€í•œ í™˜ê°(hallucination) ì‘ë‹µ ì–µì œ

## 2026-02-13 (ë²„ìŠ¤ ì‘ë‹µ ê·œì¹™ ì œí•œ: ì •ë¥˜ì¥ëª…+ë„ë³´ì‹œê°„ë§Œ)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ë²„ìŠ¤ê°€ ë” ë¹ ë¥¸ ìƒí™©ì—ì„œë„ ì§€í•˜ì²  ETA/ë°©ë©´ ì •ë³´ë¥¼ ì„ì–´ ë§í•´ ì˜¤ë‹µì´ ë°œìƒí•˜ëŠ” ë¬¸ì œë¥¼ ì¤„ì´ê¸° ìœ„í•´.
- ì‚¬ìš©ìê°€ ìš”ì²­í•œ ì •ì±…: "ë²„ìŠ¤ê°€ ë‚˜ì˜¤ë©´ ì •ë¥˜ì¥ ì´ë¦„ + ê±¸ì–´ì„œ ëª‡ ë¶„"ë§Œ ì•ˆë‚´.

### ë³€ê²½ ë‚´ìš©
- ODSAY ê·¼ì²˜ í¬ì¸íŠ¸ íƒìƒ‰ í•¨ìˆ˜ í™•ì¥:
  - `stationClass=2`(ì§€í•˜ì² ) ì™¸ì— `stationClass=1`(ë²„ìŠ¤ì •ë¥˜ì¥) ì¡°íšŒ ì¶”ê°€
  - ë²„ìŠ¤ì •ë¥˜ì¥ëª…/ì¢Œí‘œë¥¼ ë°›ì•„ ë„ë³´ ì‹œê°„ ì¶”ì •(`walkToBusStopMinutes`) ê³„ì‚°
- `/api/seoul-info/live` ì‘ë‹µì— ë²„ìŠ¤ í•„ë“œ ì¶”ê°€:
  - `busStopName`
  - `walkToBusStopMinutes`
- ë¸Œë¦¬í•‘ ë¬¸êµ¬ì— ë²„ìŠ¤ ë¬¸ì¥ ì¶”ê°€:
  - ë²„ìŠ¤ ì´ìš© ì‹œ ê°€ì¥ ê°€ê¹Œìš´ ì •ë¥˜ì¥ëª… + ë„ë³´ ë¶„ë§Œ ì•ˆë‚´
- ì‹œìŠ¤í…œ ì§€ì¹¨ ê°•í™”:
  - ë²„ìŠ¤ ê´€ë ¨ ë°œí™” ì‹œ ì •ë¥˜ì¥ëª…/ë„ë³´ì‹œê°„ë§Œ í—ˆìš©
  - ë²„ìŠ¤ ë…¸ì„ /ë²„ìŠ¤ ETA/ë²„ìŠ¤ ë°©ë©´ì€ live contextì— ëª…ì‹œë˜ì§€ ì•Šìœ¼ë©´ ê¸ˆì§€

### ê¸°ëŠ¥ ëª©ì 
- ë²„ìŠ¤/ì§€í•˜ì²  ì»¨í…ìŠ¤íŠ¸ í˜¼í•©ìœ¼ë¡œ ì¸í•œ ì˜ëª»ëœ ì•ˆë‚´ ê°ì†Œ
- ì‚¬ìš©ì ìš”ì²­ ì •ì±…ì— ë§ëŠ” ë³´ìˆ˜ì  ë²„ìŠ¤ ì•ˆë‚´ ê³ ì •

## 2026-02-13 (ë©€í‹°ëª¨ë‹¬ ê²½ë¡œ ìš”ì•½ ê°•í™”: ë²„ìŠ¤ë²ˆí˜¸ + ì§€í•˜ì²  ìƒì„¸ + ë‚ ì”¨/ëŒ€ê¸°ì§ˆ)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ì‚¬ìš©ì ìš”êµ¬ì‚¬í•­ í™•ì¥:
  - ë²„ìŠ¤ëŠ” ì •ë¥˜ì¥+ë„ë³´ë¿ ì•„ë‹ˆë¼ íƒ‘ìŠ¹ ë²„ìŠ¤ ë²ˆí˜¸ê¹Œì§€ í•„ìš”
  - ì§€í•˜ì² ì€ ìµœë‹¨ ê²½ë¡œ ê¸°ì¤€ìœ¼ë¡œ ë°©ë©´/ë„ì°©/ë‹¤ìŒì—´ì°¨/ë„ë³´ íŒë‹¨ê¹Œì§€ í•„ìš”
  - ë‚ ì”¨/ëŒ€ê¸°ì§ˆ ë°˜ì˜ ì¶”ì²œ(ë¹„ ì˜¤ë©´ ë”°ë¦‰ì´ ë¹„ì¶”ì²œ) í•„ìš”

### ë³€ê²½ ë‚´ìš©
- í™˜ê²½ë³€ìˆ˜ ì¶”ê°€ ì‚¬ìš©:
  - `HOME_LAT`, `HOME_LNG` (ëª©ì ì§€ ì¢Œí‘œ; ì—†ìœ¼ë©´ ê²½ë¡œ ê¸°ë°˜ ì•ˆë‚´ ì œí•œ)
- API ì—°ë™ ì¶”ê°€/í™•ì¥:
  - ODSAY `searchPubTransPathT`ë¡œ í˜„ì¬ ìœ„ì¹˜ -> ëª©ì ì§€ ìµœë‹¨ ëŒ€ì¤‘êµí†µ ê²½ë¡œ ì¡°íšŒ
  - ODSAY ê²°ê³¼ì—ì„œ ì²« íƒ‘ìŠ¹ ìˆ˜ë‹¨(ë²„ìŠ¤/ì§€í•˜ì² ), íƒ‘ìŠ¹ ì§€ì , ë°©ë©´, ë²„ìŠ¤ë²ˆí˜¸ ì¶”ì¶œ
  - ì„œìš¸ ì§€í•˜ì²  ì‹¤ì‹œê°„ ë„ì°© APIë¡œ ì¶œë°œì—­ ë„ì°©ì‹œê°„(í˜„ì¬/ë‹¤ìŒ ì—´ì°¨) ê²°í•©
  - Open-Meteo(ë‚ ì”¨), Open-Meteo Air Quality(ëŒ€ê¸°ì§ˆ) ì¡°íšŒ ê²°í•©
- ìš”ì•½ ë¡œì§ ê°•í™” (`_build_live_seoul_summary` ì „ë©´ êµì²´):
  - ë²„ìŠ¤ ì‹œì‘ ê²½ë¡œ: ë²„ìŠ¤ë²ˆí˜¸ + íƒ‘ìŠ¹ì •ë¥˜ì¥ + ë„ë³´ì‹œê°„ ì¤‘ì‹¬ ì•ˆë‚´
  - ì§€í•˜ì²  ì‹œì‘ ê²½ë¡œ: ì¶œë°œì—­/ë°©ë©´/ë„ì°©ì‹œê°„/ë„ë³´ì‹œê°„/í˜„ì¬ì—´ì°¨ vs ë‹¤ìŒì—´ì°¨ íŒë‹¨ ì•ˆë‚´
  - ë¹„ê°€ ì˜¤ë©´ ë”°ë¦‰ì´ ë¹„ì¶”ì²œ, ë¹„ê°€ ì—†ê³  ë„ë³´ê°€ ê¸¸ë©´ ë”°ë¦‰ì´ ëŒ€ì•ˆ ì–¸ê¸‰
- ë°˜í™˜ í•„ë“œ í™•ì¥:
  - `busNumbers`, `firstMode`, `firstDirection`, `weather`, `air`, `homeConfigured` ë“±
- ì‹œìŠ¤í…œ ì§€ì¹¨ ì—…ë°ì´íŠ¸:
  - ì§€í•˜ì² /ë²„ìŠ¤ ì•ˆë‚´ì— í•„ìš”í•œ í•„ìˆ˜ í•­ëª©ì„ ë¼ì´ë¸Œ ì»¨í…ìŠ¤íŠ¸ ê¸°ë°˜ìœ¼ë¡œë§Œ ë°œí™”
  - ê°’ ì„ì˜ ìƒì„± ê¸ˆì§€ ìœ ì§€

### ê¸°ëŠ¥ ëª©ì 
- ìš”ì²­í•œ ì„¤ëª… í¬ë§·(ë²„ìŠ¤ë²ˆí˜¸, ì§€í•˜ì²  ìƒì„¸ íŒë‹¨, ë‚ ì”¨ ë°˜ì˜ ì¶”ì²œ)ì„ ë°ì´í„° ê¸°ë°˜ìœ¼ë¡œ êµ¬í˜„
- í™˜ê°ì„± ì•ˆë‚´ë¥¼ ì¤„ì´ê³ , ì‹¤ì œ API ê°’ ì¤‘ì‹¬ì˜ ì‘ë‹µìœ¼ë¡œ ì •í•©ì„± í–¥ìƒ

## 2026-02-13 (ë§¤ ì§ˆë¬¸ ëª©ì ì§€ ê¸°ì¤€ ì¬ê³„ì‚° + Connect ìë™ ë¡œê·¸ ì œê±°)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`
- `temp_front/app/page.tsx`

### ë³€ê²½ ì´ìœ 
- ì‚¬ìš©ìê°€ ëª…ì‹œí•œ ìš”êµ¬ì‚¬í•­: ëª©ì ì§€ë¥¼ `.env` ê³ ì •ê°’ì´ ì•„ë‹ˆë¼ "ë§¤ ì§ˆë¬¸(ìŒì„± ë°œí™”)ì˜ ëª©ì ì§€" ê¸°ì¤€ìœ¼ë¡œ ê³„ì‚°í•´ì•¼ í•¨.
- Connect ì‹œ ìë™ìœ¼ë¡œ ëŒ€í™”ì°½ì— í‡´ê·¼ê¸¸ ë¡œê·¸ê°€ ì°íˆëŠ” ë¶€ì‘ìš© ì œê±° í•„ìš”.

### ë³€ê²½ ë‚´ìš©
- `temp_front/app/page.tsx`
  - Connect ì‹œ ì´ˆê¸° `/api/seoul-info/live` í˜¸ì¶œ ê²°ê³¼ë¥¼ ë” ì´ìƒ ëŒ€í™”ì°½(`setTranscripts`)ì— ìë™ ê¸°ë¡í•˜ì§€ ì•Šë„ë¡ ì œê±°.
  - WebSocket ì—°ê²° ì‹œ `lat`, `lng`ë¥¼ ì¿¼ë¦¬ íŒŒë¼ë¯¸í„°ë¡œ ì „ë‹¬í•´ ì„œë²„ê°€ í„´ë³„ ì¬ê³„ì‚°ì— í™œìš© ê°€ëŠ¥í•˜ë„ë¡ í™•ì¥.
- `backend/server.py`
  - ì‚¬ìš©ì STT í…ìŠ¤íŠ¸ì—ì„œ ëª©ì ì§€ í›„ë³´ë¥¼ ì¶”ì¶œí•˜ëŠ” í—¬í¼ ì¶”ê°€ (`_extract_destination_from_text`)
  - ëª©ì ì§€ ì—­ëª… -> ì¢Œí‘œ í•´ì„ í—¬í¼ ì¶”ê°€ (`_resolve_destination_coords_from_name`)
  - `/ws/audio` ì„¸ì…˜ì—ì„œ ì‚¬ìš©ì ë°œí™”ê°€ ë“¤ì–´ì˜¬ ë•Œë§ˆë‹¤:
    - ëª©ì ì§€ ìƒíƒœ ê°±ì‹ 
    - ìµœì‹  ìœ„ì¹˜+ëª©ì ì§€ ê¸°ì¤€ ì‹¤ì‹œê°„ ìš”ì•½ ì¬ê³„ì‚°
    - Gemini ì„¸ì…˜ì— ë™ì  ì»¨í…ìŠ¤íŠ¸ ì—…ë°ì´íŠ¸ íë¡œ ì£¼ì…
  - ëª©ì ì§€ ì¢Œí‘œë¥¼ ìš°ì„  ì‚¬ìš©í•˜ê³ , ì—†ì„ ë•Œë§Œ ê¸°ì¡´ fallbackìœ¼ë¡œ ë™ì‘í•˜ë„ë¡ ê²½ë¡œ ê³„ì‚° ìš°ì„ ìˆœìœ„ ì¡°ì •

### ê¸°ëŠ¥ ëª©ì 
- ë™ì¼ í†µí™” ì„¸ì…˜ ë‚´ì—ì„œë„ ì§ˆë¬¸ë§ˆë‹¤ ëª©ì ì§€ê°€ ë°”ë€Œë©´ ì¦‰ì‹œ ë°˜ì˜
- Connect ì§í›„ ë¶ˆí•„ìš”í•œ "í‡´ê·¼ê¸¸ ì•ˆë‚´ ë¡œê·¸" ìë™ ì¶œë ¥ ì œê±°

## 2026-02-13 (gpt-4o-mini ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´í„° ì¶”ê°€: intent_router + tool_executor)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ë‹¨ì¼ ëª¨ë¸ ì¶”ë¡ ë§Œìœ¼ë¡œ íŠ¸ë¦¬ê±°ë¥¼ ì²˜ë¦¬í•˜ë©´ API í˜¸ì¶œ íƒ€ì´ë°/ë²”ìœ„ê°€ í”ë“¤ë ¤ ì •í™•ë„ê°€ ë–¨ì–´ì ¸,
  "ì˜ë„ ë¶„ë¥˜ -> í•„ìš”í•œ APIë§Œ í˜¸ì¶œ -> ê²°ê³¼ ì •ê·œí™” í›„ ë‹µë³€" êµ¬ì¡°ê°€ í•„ìš”í–ˆê¸° ë•Œë¬¸.

### ë³€ê²½ ë‚´ìš©
- `IntentRouter` ì¶”ê°€:
  - Azure OpenAI ê¸°ë°˜ intent ë¼ìš°í„° í´ë˜ìŠ¤ êµ¬í˜„
  - ê¸°ë³¸ ëª¨ë¸: `INTENT_ROUTER_MODEL` (ê¸°ë³¸ê°’ `gpt-4o-mini`)
  - ì¶œë ¥ ìŠ¤í‚¤ë§ˆ: `intent`, `destination`
  - ë¼ìš°í„° ì‹¤íŒ¨ ì‹œ í‚¤ì›Œë“œ ê¸°ë°˜ fallback ë¼ìš°íŒ…
- `Tool Executor` ì¶”ê°€:
  - `_execute_tools_for_intent(intent, lat, lng, destination)` êµ¬í˜„
  - intentë³„ë¡œ í•„ìš”í•œ live ë°ì´í„°ë¥¼ ì„ ë³„/ê°€ê³µ
    - `subway_route`, `bus_route`, `weather`, `air_quality`, `commute_overview`
- WebSocket í„´ ì²˜ë¦¬ ì—°ë™:
  - ì‚¬ìš©ì STT í…ìŠ¤íŠ¸ë§ˆë‹¤ intent ë¼ìš°íŒ… ì‹¤í–‰
  - ëª©ì ì§€ ìƒíƒœ ê°±ì‹  í›„ tool executor ì‹¤í–‰
  - ê²°ê³¼ë¥¼ Gemini ì„¸ì…˜ ì»¨í…ìŠ¤íŠ¸ ì—…ë°ì´íŠ¸(`send_client_content`) íë¡œ ì£¼ì…

### ê¸°ëŠ¥ ëª©ì 
- ë§¤ ì§ˆë¬¸ ì˜ë„ì— ë§ëŠ” API íŠ¸ë¦¬ê±° ìë™í™”
- ì‘ë‹µ ê·¼ê±°ë¥¼ live ë°ì´í„°ë¡œ ì œí•œí•´ í™˜ê°ì„± ì‘ë‹µ ê°ì†Œ

## 2026-02-13 (ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´ì…˜ ë‹¨ì¼í™” ì •ë¦¬)

### ëŒ€ìƒ íŒŒì¼
- `temp_front/app/page.tsx`
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- í˜¼í•© ìƒíƒœ(êµ¬ë°©ì‹ `seoul_summary` + ì‹ ë°©ì‹ ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´ì…˜)ê°€ ì¶©ëŒì„ ë§Œë“¤ ìˆ˜ ìˆì–´,
  ì‹ ë°©ì‹ë§Œ ì‚¬ìš©í•˜ë„ë¡ ê²½ë¡œë¥¼ ë‹¨ì¼í™”í•˜ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- `temp_front/app/page.tsx`
  - Connect ì‹œ êµ¬ë°©ì‹ live prefetch/`seoul_summary` ìƒì„±/ë³´ê´€ ë¡œì§ ì œê±°
  - WebSocket ì—°ê²° íŒŒë¼ë¯¸í„°ë¥¼ `user_id + lat/lng` ì¤‘ì‹¬ìœ¼ë¡œ ë‹¨ìˆœí™”
- `backend/server.py`
  - `/ws/audio`ì—ì„œ `seoul_summary` ì¿¼ë¦¬ íŒŒë¼ë¯¸í„° ì²˜ë¦¬ ì œê±°
  - ì´ˆê¸° ì‹œìŠ¤í…œ ì§€ì¹¨ì— `SEOUL SUMMARY CONTEXT`ë¥¼ ë¶™ì´ëŠ” êµ¬ë°©ì‹ ì£¼ì… ì œê±°
  - í„´ë³„ ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´ì…˜ ì»¨í…ìŠ¤íŠ¸ ì£¼ì… ê²½ë¡œë§Œ ìœ ì§€

### ê¸°ëŠ¥ ëª©ì 
- ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´ì…˜ ì „ìš© ìš´ì˜(ë‹¨ì¼ ì†ŒìŠ¤ ì˜¤ë¸Œ íŠ¸ë£¨ìŠ¤) í™•ë³´
- Connect ì‹œì  ë¶ˆí•„ìš”í•œ ì„ í–‰ ì»¨í…ìŠ¤íŠ¸/ë¡œê·¸ ë¶€ì‘ìš© ì œê±°

## 2026-02-13 (ìœ„ì¹˜ í•„ìˆ˜ ì—°ê²° ê°•ì œ + ì¢Œí‘œ ìˆ˜ì‹  ë¡œê·¸ ì¶”ê°€)

### ëŒ€ìƒ íŒŒì¼
- `temp_front/app/page.tsx`
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ì‚¬ìš©ì í…ŒìŠ¤íŠ¸ì—ì„œ ìœ„ì¹˜ì •ë³´ ëˆ„ë½ìœ¼ë¡œ ODSAY ê¸°ë°˜ ê²½ë¡œê°€ ì‹¤íŒ¨í•˜ëŠ” ë¬¸ì œê°€ ë°˜ë³µë˜ì–´,
  ìœ„ì¹˜ ê¶Œí•œì´ ì—†ìœ¼ë©´ ì—°ê²°ì„ ì§„í–‰í•˜ì§€ ì•Šë„ë¡ ëª…í™•íˆ ì œì–´í•  í•„ìš”ê°€ ìˆì—ˆìŒ.

### ë³€ê²½ ë‚´ìš©
- `temp_front/app/page.tsx`
  - Connect ì‹œ geolocation ì‹¤íŒ¨í•˜ë©´ WebSocket ì—°ê²° ì¤‘ë‹¨
  - ìƒíƒœ ë©”ì‹œì§€ë¡œ ìœ„ì¹˜ ê¶Œí•œ í•„ìš” ì•ˆë‚´ (`localhost` + ìœ„ì¹˜ í—ˆìš©)
- `backend/server.py`
  - WebSocket ì—°ê²° ì‹œ `lat/lng` ìˆ˜ì‹  ì—¬ë¶€ ë¡œê·¸ ì¶”ê°€
    - ì¢Œí‘œ ìˆìŒ: ìˆ˜ì‹  ê°’ ì¶œë ¥
    - ì¢Œí‘œ ì—†ìŒ: ODSAY ì‹¤ì‹œê°„ ë¼ìš°íŒ… ë¶ˆê°€ ê²½ê³  ì¶œë ¥

### ê¸°ëŠ¥ ëª©ì 
- ìœ„ì¹˜ ëˆ„ë½ ìƒíƒœì—ì„œ ì˜ëª»ëœ ê²½ë¡œ ì‘ë‹µì„ ë°©ì§€
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
  - ì´í›„ í‚¤ì›Œë“œ fallback ë¼ìš°íŒ…ìœ¼ë¡œ ìë™ ì „í™˜

### ê¸°ëŠ¥ ëª©ì 
- ë°°í¬ëª… ì˜¤ì„¤ì • ìƒíƒœì—ì„œë„ ëŒ€í™” íë¦„ ì§€ì†
- ë™ì¼ 404 ë¡œê·¸ ë°˜ë³µ ë°©ì§€ ë° fallback ì•ˆì •ì„± í™•ë³´

## 2026-02-13 (í„´ ì‘ë‹µ ì•ˆì •í™”: ì¦‰ì‹œ ì»¨í…ìŠ¤íŠ¸ ì£¼ì… + ì¬ì§ˆë¬¸ ê·œì¹™)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ìœ„ì¹˜ ì¢Œí‘œê°€ ì´ë¯¸ ìˆìŒì—ë„ ëª¨ë¸ì´ ìœ„ì¹˜ë¥¼ ë‹¤ì‹œ ë¬»ëŠ” ì‘ë‹µì´ ë°œìƒí•˜ê³ ,
  í„´ ì»¨í…ìŠ¤íŠ¸ ì£¼ì… íƒ€ì´ë° ì§€ì—°ìœ¼ë¡œ ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´ì…˜ ë°˜ì˜ì´ ëŠ¦ì–´ì§€ëŠ” ë¬¸ì œë¥¼ ì™„í™”í•˜ê¸° ìœ„í•´.

### ë³€ê²½ ë‚´ìš©
- ì‚¬ìš©ì STT í™•ì •(`on_recognized`, role=user) ì‹œì ì— ì»¨í…ìŠ¤íŠ¸ë¥¼ ì¦‰ì‹œ `send_client_content`ë¡œ ì£¼ì…
  - ì„¸ì…˜ ì¤€ë¹„ ì „ì—ëŠ” í ì ì¬, ì„¸ì…˜ ì¤€ë¹„ í›„ ì¦‰ì‹œ ì£¼ì…
- ì‹œìŠ¤í…œ ì§€ì¹¨ ê°•í™”:
  - `lat/lng` ìˆ˜ì‹  ì‹œ "í˜„ì¬ ìœ„ì¹˜ ì¬ì§ˆë¬¸ ê¸ˆì§€" ëª…ì‹œ
- ëª©ì ì§€ ë¯¸ì§€ì • ì¬ì§ˆë¬¸ ì •ì±… ì¶”ê°€:
  - êµí†µ ì˜ë„(`subway_route`, `bus_route`, `commute_overview`)ì—ì„œ ëª©ì ì§€ê°€ ì—†ìœ¼ë©´ ëª©ì ì§€ ì§ˆë¬¸ 1íšŒë§Œ í—ˆìš©
  - ë™ì¼ ì„¸ì…˜ì—ì„œ ë°˜ë³µ ì§ˆë¬¸ ê¸ˆì§€
- ì„¸ì…˜ ì¢…ë£Œ ì‹œ `session_ref` í•´ì œ ì²˜ë¦¬ ì¶”ê°€

### ê¸°ëŠ¥ ëª©ì 
- ì˜¤ì¼€ìŠ¤íŠ¸ë ˆì´ì…˜ ì»¨í…ìŠ¤íŠ¸ê°€ ì²« ì‘ë‹µ ì „ì— ë°˜ì˜ë  í™•ë¥  ê°œì„ 
- "í˜„ì¬ ìœ„ì¹˜ê°€ ì–´ë””ëƒ" ë°˜ë³µ ì§ˆì˜ ê°ì†Œ
- ëª©ì ì§€ ì¬ì§ˆë¬¸ ë°˜ë³µ ë£¨í”„ ë°©ì§€

## 2026-02-13 (ì—°ê²° ì§í›„ ìœ„ì¹˜ ì»¨í…ìŠ¤íŠ¸ ì„ ì£¼ì…)

### ëŒ€ìƒ íŒŒì¼
- `backend/server.py`

### ë³€ê²½ ì´ìœ 
- ìœ„ì¹˜ ì¢Œí‘œê°€ WS ì¿¼ë¦¬ë¡œ ìˆ˜ì‹ ë˜ë”ë¼ë„, ëª¨ë¸ ì„¸ì…˜ ì‹œì‘ ì§í›„ì—ëŠ” í•´ë‹¹ ë§¥ë½ì„ ëª…ì‹œì ìœ¼ë¡œ ì „ë‹¬í•˜ì§€ ì•Šì•„
  ì²« ì‘ë‹µì—ì„œ "í˜„ì¬ ìœ„ì¹˜ë¥¼ ëª¨ë¥´ê² ë‹¤"ëŠ” ë°œí™”ê°€ ë°œìƒí•  ìˆ˜ ìˆì—ˆê¸° ë•Œë¬¸.

### ë³€ê²½ ë‚´ìš©
- Gemini Live ì„¸ì…˜ ì—°ê²° ì§í›„(`Connected to Live API`) ì¦‰ì‹œ:
  - í˜„ì¬ `lat/lng` ê¸°ë°˜ `commute_overview` ì»¨í…ìŠ¤íŠ¸ ìƒì„±
  - `send_client_content`ë¡œ ëª¨ë¸ì— ì„ ì£¼ì…
- ì£¼ì… ì‹¤íŒ¨ ì‹œ ë¡œê·¸ ì¶œë ¥:
  - `[SeoulInfo] initial location context injection failed: ...`

### ê¸°ëŠ¥ ëª©ì 
- ì—°ê²° ì‹œì‘ ì‹œì ë¶€í„° ëª¨ë¸ì´ ì‚¬ìš©ì í˜„ì¬ ìœ„ì¹˜ ë§¥ë½ì„ ì¸ì§€
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

## 2026-02-14 (Åğ±Ù±æ ±âº» ÀÀ´äÀ» ÁöÇÏÃ¶ Àü¿ëÀ¸·Î °íÁ¤)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- "Åğ±Ù±æ ¾Ë·ÁÁà" ±âº» ¿äÃ»¿¡¼­ ¹ö½º °æ·Î°¡ ¸ÕÀú ¾È³»µÇ¾î »ç¿ëÀÚ ¿ä±¸(ÁöÇÏÃ¶ ±âÁØ Ãâ¹ß¿ª/¹æ¸é/µµÂøºĞ/Å¾½ÂÆÇ´Ü)¿Í ºÒÀÏÄ¡.
- Ä³½Ã°¡ ¹ö½º ¿ä¾àÀ¸·Î ³²¾Æ ÀÌÈÄ ÁöÇÏÃ¶ ¿äÃ»¿¡µµ ¼¯¿© ³ª¿À´Â ¹®Á¦ Á¸Àç.

### º¯°æ ³»¿ë
- ±âº» ¸ñÀûÁö(`COMMUTE_DEFAULT_DESTINATION`)¿¡ ´ëÇÑ `commute_overview`´Â ÁöÇÏÃ¶ ¿ì¼± ¸ğµå·Î ½ÇÇàÇÏµµ·Ï º¯°æ.
  - ODSAY Á¶È¸ ½Ã `SearchPathType=1`(subway) ¿ì¼± ½Ãµµ.
  - ½ÇÆĞ ½Ã ÀÏ¹İ °æ·Î(`SearchPathType=0`)·Î º¸Á¶ Á¶È¸.
- ÁöÇÏÃ¶ ¾È³» ¹®±¸¸¦ °­Á¦:
  - Ãâ¹ß¿ª, ³ë¼±/¹æ¸é, ÇöÀç¿ª¡æÃâ¹ß¿ª µµº¸ºĞ, ÀÌ¹ø ¿­Â÷ ETA, ´ÙÀ½ ¿­Â÷ ETA Áß½ÉÀ¸·Î ±¸¼º.
- ¿­Â÷ Å¾½Â ÆÇ´Ü ±âÁØ Á¶Á¤:
  - `µµº¸ºĞ >= ÀÌ¹ø¿­Â÷ ETA` ÀÌ¸é "ÀÌ¹ø ¿­Â÷ ³õÄ¥ °¡´É¼º ³ôÀ½, ´ÙÀ½ ¿­Â÷ ±ÇÀå".
- ETA ¹İ¿Ã¸² ±ÔÄ¢ Á¶Á¤:
  - 3ºĞ 30ÃÊ¸¦ 4ºĞÀ¸·Î ¿Ã¸®Áö ¾Ê°í "¾à 3ºĞ"À¸·Î º¸¼öÀûÀ¸·Î °è»ê(1ºĞ ¹Ì¸¸Àº 1ºĞ Ã³¸®).
- Ä³½Ã »ç¿ë ¹üÀ§ Ãà¼Ò:
  - `cached_summary`´Â `commute_overview`¿¡¼­¸¸ »ç¿ë.
  - `subway_route`/`bus_route`´Â ¸Å¹ø ÃÖ½Å µµ±¸ ½ÇÇà °á°ú¸¦ »ç¿ëÇØ È¥¼± ¹æÁö.

### ±â´ë È¿°ú
- "Åğ±Ù±æ ¾Ë·ÁÁà" ½Ã ÁöÇÏÃ¶ Áß½ÉÀ¸·Î ÀÏ°üµÈ ÀÀ´ä.
- "Áö±İ Å¸¸é µÇ´ÂÁö / ´ÙÀ½ ¿­Â÷ Å¸¾ß ÇÏ´ÂÁö" ÆÇ´Ü Á¤È®µµ Çâ»ó.
- ÁöÇÏÃ¶ ¿äÃ» ½Ã ÀÌÀü ¹ö½º Ä³½Ã°¡ ¼¯ÀÌ´Â ¹®Á¦ ¿ÏÈ­.

## 2026-02-14 (Åğ±Ù±æ ¾È³» ±ÔÄ¢ Á¤±³È­: ETA/Å¾½ÂÆÇ´Ü/ºÒÇÊ¿ä Á¤º¸ Á¦°Å)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- 1~2ºĞ ³²Àº ¿­Â÷¸¦ "È¥ÀâÇØ¼­ ³õÄ¡±â ½±´Ù"Ã³·³ °úµµÇÏ°Ô ÇØ¼®ÇÏ´Â ¹®Á¦°¡ ÀÖ¾úÀ½.
- µµº¸ 11ºĞ vs ´ÙÀ½ ¿­Â÷ 4ºĞ °°Àº ºÒ°¡´É ÄÉÀÌ½º¿¡¼­µµ "´ÙÀ½ ¿­Â÷ ±ÇÀå" ¹®±¸°¡ ³ª¿À´Â ¹®Á¦ Á¸Àç.
- Åğ±Ù±æ ÀÀ´ä¿¡ ´ë±âÁú/³¯¾¾/µû¸ªÀÌ ¹®±¸°¡ ¼¯¿© ÇÙ½É ¾È³»¸¦ Èå¸².

### º¯°æ ³»¿ë
- ETA Ç¥Çö ±ÔÄ¢ Ãß°¡(`_format_eta_phrase`):
  - 1~2ºĞ: "°ğ µµÂø"
  - 3ºĞ ÀÌ»ó: "¾à NºĞ"
- ÁöÇÏÃ¶ Å¾½Â ÆÇ´Ü ·ÎÁ÷ ¼¼ºĞÈ­:
  - `first`: µµº¸½Ã°£ < ÀÌ¹ø ¿­Â÷ ETA
  - `next`: ÀÌ¹øÀº ¾î·Æ°í µµº¸½Ã°£ < ´ÙÀ½ ¿­Â÷ ETA
  - `after_next`: ÀÌ¹ø/´ÙÀ½ ¸ğµÎ ¾î·Á¿ò (´ÙÀ½ ¿­Â÷ ±ÇÀå ¹®±¸ ±İÁö)
- Åğ±Ù±æ/°æ·Î ¿ä¾à¿¡¼­ ´ë±âÁú/³¯¾¾/µû¸ªÀÌ ¹®±¸ Á¦°Å.
- ½Ã½ºÅÛ ÁöÄ§ °­È­:
  - ½Çµ¥ÀÌÅÍ ¾øÀ¸¸é È¥Àâ/±ºÁß(È¥Àâµµ) ¾ğ±Ş ±İÁö.

### ±â´ë È¿°ú
- "1ºĞ ³²À½" ÄÉÀÌ½º¿¡¼­ °úµµÇÑ °æ°í ´ë½Å ÀÚ¿¬½º·¯¿î "°ğ µµÂø" ¾È³».
- ¹°¸®ÀûÀ¸·Î ºÒ°¡´ÉÇÑ "´ÙÀ½ ¿­Â÷ ±ÇÀå" ¿À·ù °¨¼Ò.
- Åğ±Ù±æ ÀÀ´äÀÌ Ãâ¹ß¿ª/¹æ¸é/ETA/µµº¸/Å¾½ÂÆÇ´Ü Áß½ÉÀ¸·Î °£°áÈ­.

## 2026-02-14 (ºñ±âº» ¸ñÀûÁö ÁöÇÏÃ¶ »ó¼¼ °æ·Î/È¯½Â ¾È³» °­È­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- ±âº» Åğ±Ù±æ(Áı) ¿Ü ¸ñÀûÁö¸¦ ¹°À» ¶§´Â ´Ü¼ø ¿ä¾àÀÌ ¾Æ´Ï¶ó
  - ¾î´À ¿ª/¸î È£¼±/¾î´À ¹æ¸é Å¾½Â,
  - ¾îµğ¼­ ³»·Á È¯½Â,
  - È¯½Â ÈÄ ¾îµğ¼­ ÇÏÂ÷
  ±îÁö ´Ü°èÇü ¾È³»°¡ ÇÊ¿äÇÔ.

### º¯°æ ³»¿ë
- ODSAY °æ·Î ÆÄ½Ì È®Àå:
  - `subPath`ÀÇ ¸ğµç ÁöÇÏÃ¶ ±¸°£À» `subwayLegs`·Î ¼öÁı
  - °¢ ±¸°£º° `line`, `start`, `end`, `direction` ÀúÀå
- ºñ±âº» ¸ñÀûÁö + (`commute_overview` ¶Ç´Â `subway_route`)ÀÏ ¶§ `detailed_subway` È°¼ºÈ­.
- ÀÀ´ä »ı¼º °­È­:
  - ±âÁ¸ Ãâ¹ß¿ª ¿­Â÷ µµÂøÁ¤º¸(ÀÌ¹ø/´ÙÀ½ ETA, µµº¸ ºñ±³)´Â À¯Áö
  - Ãß°¡·Î ÁöÇÏÃ¶ ±¸°£ »ó¼¼ ¹®±¸¸¦ ¼øÂ÷ Á¦°ø
    - 1±¸°£: ¾îµğ ¿ª¿¡¼­ ¸î È£¼±/¹æ¸é Å¾½Â, ¾îµğ¼­ ÇÏÂ÷
    - 2±¸°£ ÀÌ»ó: nÂ÷ È¯½Â¿ª, È¯½Â ³ë¼±/¹æ¸é, ÇÏÂ÷¿ª

### ±â´ë È¿°ú
- ºñ±âº» ¸ñÀûÁö Áú¹® ½Ã ÁöÇÏÃ¶ Áß½ÉÀÇ ´Ü°èº° È¯½Â ¾È³»°¡ Á¦°øµÇ¾î ½ÇÁ¦ ÀÌµ¿¿¡ ¹Ù·Î »ç¿ë °¡´É.

## 2026-02-14 (´Ù¸¥ ¸ñÀûÁö ÀÚµ¿ ÀÎ½Ä/À§Ä¡ ÀçÁú¹® ¹æÁö º¸°­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- "¼º¼ö¿¡¼­ ¾à¼Ó", "¼º¼ö ÂÊ" °°Àº ¹ßÈ­¿¡¼­ ¸ñÀûÁö°¡ ÃßÃâµÇÁö ¾Ê¾Æ °æ·Î ÀÀ´äÀÌ ºñ°Å³ª ¹İº¹ È®ÀÎ Áú¹®ÀÌ ¹ß»ı.
- ¶óÀÌºê ¿ä¾à »ı¼º ½ÇÆĞ ½Ã ¸ğµ¨ÀÌ À§Ä¡¸¦ ´Ù½Ã ¹°¾îº¸´Â ÄÉÀÌ½º°¡ ³²¾Æ ÀÖ¾úÀ½.

### º¯°æ ³»¿ë
- ¸ñÀûÁö ÃßÃâ ÆĞÅÏ È®Àå:
  - `...¿¡¼­ ¾à¼Ó`, `...ÂÊ(À¸·Î)`, `...¿¡/¿¡¼­ °¡` ÇüÅÂ ÀÎ½Ä
  - ¹®Àå ³¡ `...À¸·Î/·Î` ´Ü¹®(¿¹: "¼º¼ö·Î") ÀÎ½Ä
  - ÈÄÃ³¸®·Î `ÂÊ/±ÙÃ³/ºÎ±Ù/¹æÇâ` Á¢¹Ì Á¤¸®
- ¸ñÀûÁö ÁÂÇ¥ ÇØ¼® º¸°­:
  - `searchStation(name)` ½ÇÆĞ ½Ã `searchStation(name + "¿ª")` ÀÚµ¿ Àç½Ãµµ
  - ¿¹: `¼º¼ö` -> `¼º¼ö¿ª` ÀÚµ¿ º¸Á¤
- µ¿Àû ÄÁÅØ½ºÆ® ÁÖÀÔ º¸°­:
  - µµ±¸ ¿ä¾àÀÌ ºñ¾îµµ ÃÖ¼Ò ÄÁÅØ½ºÆ®¸¦ Ç×»ó ÁÖÀÔ
  - ÁÂÇ¥°¡ ÀÖ´Â °æ¿ì: "ÇöÀç À§Ä¡ ÁÂÇ¥´Â ÀÌ¹Ì ¼ö½Å" ¸Ş½ÃÁö °­Á¦
  - °¡ÀÌµå·Î "»ç¿ëÀÚ ÇöÀç À§Ä¡ ÀçÁú¹® ±İÁö"¸¦ Ç×»ó µ¿ºÀ

### ±â´ë È¿°ú
- ´Ù¸¥ ¸ñÀûÁö Áú¹® ½Ã ¸ñÀûÁö ÀÚµ¿ ÀÎ½Ä ¼º°ø·ü »ó½Â.
- À§Ä¡¸¦ ÀÌ¹Ì ¹Ş¾Ò´Âµ¥µµ ´Ù½Ã ¹¯´Â Çö»ó °¨¼Ò.

## 2026-02-14 (´Ù¸¥ ¸ñÀûÁö ¿äÃ» ½Ã ±¤È­¹®À¸·Î µÇµ¹¾Æ°¡´Â ¹®Á¦ ¼öÁ¤)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ ¿øÀÎ
- »ç¿ëÀÚ°¡ ´Ù¸¥ ¸ñÀûÁö¸¦ ¸í½ÃÇß´Âµ¥ ¸ñÀûÁö ÁÂÇ¥ ÇØ¼®ÀÌ ½ÇÆĞÇÏ¸é, ·ÎÁ÷ÀÌ ±âº» ¸ñÀûÁö(±¤È­¹®) ÁÂÇ¥·Î Æú¹éµÇ¾î Àß¸øµÈ °æ·Î¸¦ ¾È³»ÇÔ.

### º¯°æ ³»¿ë
- ¸ñÀûÁö Æú¹é ±ÔÄ¢ ¼öÁ¤:
  - »ç¿ëÀÚ°¡ ¸ñÀûÁö¸¦ ¸í½ÃÇÑ °æ¿ì(`destination_requested=True`) ÁÂÇ¥ ÇØ¼® ½ÇÆĞ ½Ã **±âº» ¸ñÀûÁö·Î Æú¹éÇÏÁö ¾ÊÀ½**.
  - ±âº» ¸ñÀûÁö Æú¹éÀº »ç¿ëÀÚ°¡ ¸ñÀûÁö¸¦ ¸í½ÃÇÏÁö ¾Ê¾ÒÀ» ¶§¸¸ Çã¿ë.
- ¸ñÀûÁö ÃßÃâ °­È­:
  - `...°¡´Â ±æ`, `...°¡´Â±æ` ÆĞÅÏ Ãß°¡ ÀÎ½Ä.
- ¸ñÀûÁö ¹ÌÇØ¼® ½Ã ¾È³» °³¼±:
  - `'<¸ñÀûÁö>' ¸ñÀûÁö¸¦ ¿ª ±âÁØÀ¸·Î Ã£Áö ¸øÇß¾î¿ä. ¿¹: ¼º¼ö¿ª` ÇüÅÂ·Î ¸íÈ®È÷ ¾È³».
  - µ¿½Ã¿¡ ÇöÀç ±âÁØ °¡±î¿î ¿ªµµ ÇÔ²² Á¦°ø.
- ÀÇµµ º¸Á¤:
  - `intent=general`ÀÌ¶óµµ ¸ñÀûÁö°¡ ÃßÃâµÇ°í ¹®Àå¿¡ `±æ/°æ·Î/°¡´Â`ÀÌ ÀÖÀ¸¸é `commute_overview`·Î °­Á¦ º¸Á¤.

### ±â´ë È¿°ú
- "¼º¼ö °¡´Â ±æ" ¿äÃ»¿¡¼­ ±¤È­¹® °æ·Î°¡ ´Ù½Ã ³ª¿À´Â ¿Àµ¿ÀÛ ¹æÁö.
- ¸ñÀûÁö°¡ ¾Ö¸ÅÇÒ ¶§µµ ÀÚµ¿À¸·Î °æ·Î ÀÇµµ·Î Ã³¸®ÇÏ°í, ÇÊ¿äÇÑ ÃÖ¼Ò ÀçÁú¹®¸¸ ¼öÇà.

## 2026-02-14 (¼º¼ö/´Ü¹® ¸ñÀûÁö ÀÎ½Ä ½ÇÆĞ Ãß°¡ º¸°­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- "¼º¼ö °¡´Â ¹æ¹ı" °°Àº ¹ßÈ­¿¡¼­ STT º¯Çü(¿¹: °¡´É/¹æ¹ı/°æ·Î) ¶§¹®¿¡ ¸ñÀûÁö ¹®ÀÚ¿­ÀÌ Èçµé·Á ¿ª °Ë»ö ½ÇÆĞ °¡´É¼ºÀÌ ³²¾Æ ÀÖ¾úÀ½.

### º¯°æ ³»¿ë
- ¸ñÀûÁö ÃßÃâ ÆĞÅÏ Ãß°¡:
  - `... (°¡´Â|°¥|°¡´É) ¹æ¹ı`
  - `... ¹æ¹ı`, `... °æ·Î` ´Ü¹® ÆĞÅÏ
- ¸ñÀûÁö ÈÄº¸ Á¤±ÔÈ­ ÇÔ¼ö Ãß°¡(`_build_destination_candidates`):
  - Á¶»ç/ÀâÀ½(`À¸·Î/·Î/¿¡/¿¡¼­/ÂÊ/±ÙÃ³/¹æÇâ/°¡´Â/¹æ¹ı/°æ·Î`) Á¦°Å
  - °ø¹é Á¦°Å º¯Çü Ãß°¡
  - `¿ª` ¹ÌÆ÷ÇÔ ½Ã `...¿ª` ÀÚµ¿ È®Àå
- ÁÂÇ¥ ÇØ¼® ½Ã À§ ÈÄº¸±ºÀ» ¼øÂ÷ Àç½ÃµµÇÏµµ·Ï º¯°æ.

### ±â´ë È¿°ú
- "¼º¼ö °¡´Â ¹æ¹ı", "¼º¼ö °æ·Î" °°Àº ¹®Àå¿¡¼­µµ `¼º¼ö¿ª`À¸·Î ¾ÈÁ¤ÀûÀ¸·Î ¸ÅÇÎµÉ È®·ü Çâ»ó.

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
- fallback °³ÀÔ ½ÃÁ¡ÀÌ ¸íÈ®ÇØÁ® µğ¹ö±ë ¿ëÀÌ.

## 2026-02-14 (±âÁ¸ ±¤È­¹® ÄÁÅØ½ºÆ® ¿À¿°À¸·Î ÀÎÇÑ ¸ñÀûÁö È¥¼± ¿ÏÈ­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ ¿øÀÎ
- ¿¬°á ½ÃÁ¡¿¡ ±âº» ¸ñÀûÁö(±¤È­¹®) °æ·Î ¿ä¾àÀ» ½Ã½ºÅÛ/ÃÊ±â ÄÁÅØ½ºÆ®¿¡ °­ÇÏ°Ô ÁÖÀÔÇØ,
  ÀÌÈÄ »ç¿ëÀÚ°¡ ´Ù¸¥ ¸ñÀûÁö(¿¹: ¼º¼ö)¸¦ ¸»ÇØµµ ÀÌÀü ¸ñÀûÁö ¸Æ¶ôÀÌ ´äº¯¿¡ ¼¯ÀÏ ¼ö ÀÖ¾úÀ½.
- `intent=general` ÅÏ¿¡µµ ¶óÀÌºê °æ·Î ÄÁÅØ½ºÆ®¸¦ °è¼Ó ÁÖÀÔÇØ ¹®¸Æ ¿À¿°ÀÌ ´©ÀûµÉ ¼ö ÀÖ¾úÀ½.

### º¯°æ ³»¿ë
- ½Ã½ºÅÛ ÇÁ·ÒÇÁÆ®¿¡¼­ preloaded °æ·Î ¿ä¾à °íÁ¤ ÁÖÀÔ Á¦°Å.
- ¿¬°á Á÷ÈÄ ÃÊ±â ÁÖÀÔÀº "À§Ä¡ ÀÎÁö" Á¤º¸¸¸ Àü´Ş(Æ¯Á¤ ¸ñÀûÁö °æ·Î ¹ÌÁÖÀÔ).
- »ç¿ëÀÚ ¹ßÈ­ Ã³¸®¿¡¼­ ¶óÀÌºê ÄÁÅØ½ºÆ® ÁÖÀÔ ¹üÀ§ Á¦ÇÑ:
  - `subway_route`, `bus_route`, `commute_overview`, `weather`, `air_quality`¿¡¸¸ ÁÖÀÔ
  - `general` ÅÏ¿¡´Â °æ·Î ÄÁÅØ½ºÆ® ÁÖÀÔÇÏÁö ¾ÊÀ½
- °æ·Î ÅÏ °¡ÀÌµå °­È­:
  - "ÀÌ¹ø ÅÏ ¸ñÀûÁö(destination_state)¸¦ ¿ì¼± »ç¿ëÇÏ°í ÀÌÀü ¸ñÀûÁö ¸Æ¶ô ¹«½Ã" Áö½Ã Ãß°¡

### ±â´ë È¿°ú
- ¼º¼ö ¿äÃ» ½Ã ±¤È­¹® °æ·Î°¡ ÀçÃâ·ÂµÇ´Â È¥¼± °¨¼Ò.
- ºñ°æ·Î ¹ßÈ­°¡ µé¾î¿Íµµ °æ·Î ¸Æ¶ô ¿À¿°ÀÌ ´©ÀûµÇÁö ¾ÊÀ½.

## 2026-02-14 (¼º¼ö °æ·Î ÄÁÅØ½ºÆ® ¹İ¿µ Å¸ÀÌ¹Ö º¸°­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ Â¡ÈÄ
- LLM ¶ó¿ìÅÍ ·Î±×¿¡¼­ `intent=subway_route, destination=¼º¼ö`°¡ È®ÀÎµÇ´Âµ¥,
  ½ÇÁ¦ À½¼º ÀÀ´äÀº À§Ä¡ ÀçÁú¹®/¿À´äÀ¸·Î ÀÌ¾îÁü.

### ¿øÀÎ ÃßÁ¤
- ¶óÀÌºê ÄÁÅØ½ºÆ® ÁÖÀÔÀÌ ºñµ¿±â Å¸ÀÌ¹Ö¿¡¼­ ÀÀ´äº¸´Ù ´Ê°Ô ¹İ¿µµÇ¾î,
  ¸ğµ¨ÀÌ ÄÁÅØ½ºÆ® ¾ø´Â »óÅÂ·Î ¸ÕÀú ´äº¯ÇÏ´Â °æ¿ì ¹ß»ı.

### º¯°æ ³»¿ë
- ¶óÀÌºê ÄÁÅØ½ºÆ® ÁÖÀÔ ÇÔ¼ö È®Àå:
  - `_inject_live_context_now(..., complete_turn: bool)` Ãß°¡
  - ³»ºÎ `send_client_content`¿¡ `turn_complete=complete_turn` ¹İ¿µ
- °æ·Î ÀÇµµ(`subway_route`,`bus_route`,`commute_overview`)¿¡¼­´Â
  - ÄÁÅØ½ºÆ® ÁÖÀÔ ½Ã `complete_turn=True`·Î Áï½Ã ÀÀ´ä ÅÏÀ» °­Á¦
  - `[ACTION] Respond to the user's latest request now using this context.` °¡ÀÌµå Ãß°¡
- °üÃø ·Î±× º¸°­:
  - `[SeoulInfo] live context built: intent=..., destination=..., summary_ok=...`

### ±â´ë È¿°ú
- "¼º¼ö" ¸ñÀûÁö ÄÁÅØ½ºÆ®°¡ ¸ğµ¨ ÀÀ´ä Àü¿¡ ¹İ¿µµÉ È®·ü »ó½Â.
- À§Ä¡ ÀçÁú¹® ºóµµ °¨¼Ò ¹× ¸ñÀûÁö ¸ÂÃã ÀÀ´ä ÀÏ°ü¼º °³¼±.

## 2026-02-14 (½Ç½Ã°£ °æ·Î Á¶È¸ Áö¿¬ ½Ã À½¼º ÇÊ·¯ ¸àÆ® Ãß°¡)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- ODSAY/½Ç½Ã°£ API Á¶È¸ Áß ¹«À½ ±¸°£ÀÌ ¹ß»ıÇØ »ç¿ëÀÚ Ã¼°¨ Áö¿¬ÀÌ Å­.

### º¯°æ ³»¿ë
- »ç¿ëÀÚ ¿äÃ»ÀÌ ½Ç½Ã°£ °æ·Î Á¶È¸°¡ ÇÊ¿äÇÑ ÀÇµµ(`subway_route`, `bus_route`, `commute_overview`)ÀÌ°í
  Ä³½ÃµÈ Áï½Ã ÀÀ´äÀÌ ¾ø´Â °æ¿ì:
  - º» Á¶È¸ Àü¿¡ `INTENT:loading` ÄÁÅØ½ºÆ®¸¦ ¸ÕÀú ÁÖÀÔ
  - ¸ğµ¨ÀÌ ÂªÀº ÇÑ±¹¾î ÇÊ·¯ ¸àÆ®(¿¹: "À½, Àá½Ã¸¸¿ä. Áö±İ È®ÀÎÇØº¼°Ô¿ä.")¸¦ ¸ÕÀú ¸»ÇÏµµ·Ï À¯µµ
- ÀÌÈÄ ±âÁ¸´ë·Î API Á¶È¸ °á°ú ÄÁÅØ½ºÆ®¸¦ ÁÖÀÔÇØ º» ´äº¯À» ÀÌ¾î¼­ Á¦°ø.

### ±â´ë È¿°ú
- Á¶È¸ Áö¿¬ ±¸°£¿¡¼­ »ç¿ëÀÚ¿¡°Ô ÁøÇàÁßÀÓÀ» ÀÚ¿¬½º·´°Ô Àü´Ş.
- ¹«ÀÀ´äÃ³·³ ´À²¸Áö´Â Ã¼°¨ ¹®Á¦ ¿ÏÈ­.

## 2026-02-14 (Åğ±Ù µµÂøÁ¤º¸ Ä³½Ã Á¦°Å: ¿äÃ» ½ÃÁ¡ ½Ç½Ã°£ ÀçÁ¶È¸)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- ÁöÇÏÃ¶ µµÂøÁ¤º¸´Â ºĞ ´ÜÀ§·Î º¯ÇÏ¹Ç·Î, Á¢¼Ó ½Ã ¼±Ä³½Ã/Àç»ç¿ëÇÏ¸é ¾È³»°¡ ½±°Ô stale(¿À·¡µÈ Á¤º¸) »óÅÂ°¡ µÊ.

### º¯°æ ³»¿ë
- ¼¼¼Ç »óÅÂ¿¡¼­ `cached_summary` Á¦°Å.
- websocket ¿¬°á ½Ã `commute_overview` ¼±Á¶È¸(preload) Á¦°Å.
- `commute_overview` Æ÷ÇÔ ±³Åë ÀÇµµ´Â ¸Å ¿äÃ» ½Ã `_execute_tools_for_intent(...)`·Î ½Ç½Ã°£ ÀçÁ¶È¸.
- ¸ñÀûÁö º¯°æ ½Ã Ä³½Ã ¹«È¿È­ ·ÎÁ÷µµ Á¦°Å(Ä³½Ã ÀÚÃ¼ ¾øÀ½).

### ±â´ë È¿°ú
- Åğ±Ù ¿­Â÷ ETA/´ÙÀ½ ¿­Â÷ ÆÇ´ÜÀÌ Ç×»ó ¿äÃ» ½ÃÁ¡ ±âÁØÀ¸·Î °è»êµÊ.
- Á¢¼Ó Á÷ÈÄ ¿À·¡µÈ °æ·Î/µµÂøÁ¤º¸°¡ ¹İº¹µÇ´Â ¹®Á¦ ¿ÏÈ­.

## 2026-02-14 (Start Speaking ¹öÆ° ¹İÀÀ ºÒ°¡ ÀÌ½´ ´ëÀÀ)

### ´ë»ó ÆÄÀÏ
- `temp_front/app/page.tsx`

### ¹®Á¦ Â¡ÈÄ
- Start Speaking ¹öÆ°ÀÌ ´­¸®Áö ¾Ê°Å³ª, WebSocket Àç¿¬°á/Á¾·á ÈÄ UI »óÅÂ°¡ ²¿¿© À½¼º ½ÃÀÛÀÌ ½ÇÆĞ.

### º¯°æ ³»¿ë
- ¿¬°á »óÅÂ °ü¸® °­È­:
  - `isConnecting` »óÅÂ Ãß°¡, ¿¬°á Áß Áßº¹ Connect ¹æÁö
  - Connect ¹öÆ°¿¡ `Connecting...` ¹× ºñÈ°¼º ½ºÅ¸ÀÏ Àû¿ë
- WebSocket Á¾·á/¿À·ù Á¤¸® °­È­:
  - `onclose`/`onerror`¿¡¼­ `websocketRef` Á¤¸®
  - ³ìÀ½ ¸®¼Ò½º Áï½Ã Á¤¸®(`stopAudioProcessing`) ÈÄ »óÅÂ º¹±¸
- ¿Àµğ¿À ½ÃÀÛ °¡µå Ãß°¡:
  - WS°¡ OPENÀÌ ¾Æ´Ï¸é ½ÃÀÛ Â÷´Ü + `Connect first` »óÅÂ Ç¥½Ã
  - ÀÌ¹Ì ³ìÀ½ ÁßÀÌ¸é Áßº¹ ½ÃÀÛ Â÷´Ü
  - AudioContext `suspended` »óÅÂ¸é `resume()` È£Ãâ
- ¸¶ÀÌÅ© ¸®¼Ò½º ÇØÁ¦ °­È­:
  - `MediaStream` Æ®·¢ `stop()` Ã³¸® Ãß°¡
  - processor/source/context ref¸¦ null·Î ÃÊ±âÈ­

### ±â´ë È¿°ú
- Start Speaking Å¬¸¯ ½Ã »óÅÂ ²¿ÀÓÀ¸·Î ¹İÀÀ ¾ø´Â ¹®Á¦ ¿ÏÈ­.
- ¿¬°á ²÷±è/Àç¿¬°á ÀÌÈÄ¿¡µµ À½¼º ½ÃÀÛ ¹öÆ° µ¿ÀÛ ÀÏ°ü¼º °³¼±.

## 2026-02-14 (»ç¿ëÀÚ Áı ¸ñÀûÁö ÇÁ·ÎÇÊ DB ÀúÀå/¾÷µ¥ÀÌÆ® µµÀÔ)

### ´ë»ó ÆÄÀÏ
- `backend/modules/cosmos_db.py`
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- Åğ±Ù ºĞ±â ±âº» ¸ñÀûÁö´Â »ç¿ëÀÚº°·Î ´Ş¶ó¾ß ÇÏ¸ç, ¼¼¼Ç Àç½ÃÀÛ ÈÄ¿¡µµ À¯ÁöµÇ¾î¾ß ÇÔ.
- µµÂø ETA´Â ½Ç½Ã°£ ÀçÁ¶È¸°¡ ¸ÂÁö¸¸, "Áı ¸ñÀûÁö" ÀÚÃ¼´Â ¿µ±¸ ÀúÀåÀÌ ÇÊ¿äÇÔ.

### º¯°æ ³»¿ë
- CosmosDB ÇÁ·ÎÇÊ API Ãß°¡:
  - `get_user_profile(user_id)`
  - `upsert_user_profile(user_id, profile_updates)`
  - ÇÁ·ÎÇÊ ¹®¼­ Å°: `id = profile:{user_id}`, `doc_type = profile`
- ¸Ş¸ğ¸® ¹®¼­¿¡ `doc_type = memory` Ãß°¡ ¹× Á¶È¸ ÇÊÅÍ º¸°­:
  - `get_all_memories`°¡ profile ¹®¼­¸¦ ¸Ş¸ğ¸® ¸ñ·ÏÀ¸·Î ¼¯¾î ÀĞÁö ¾Êµµ·Ï ºĞ¸®.
- WebSocket ¿¬°á ½Ã »ç¿ëÀÚ ÇÁ·ÎÇÊ ·Îµå:
  - `home_destination`°¡ ÀÖÀ¸¸é ±âº» ¸ñÀûÁö·Î ¿ì¼± »ç¿ë
  - ¾øÀ¸¸é `.env`ÀÇ `COMMUTE_DEFAULT_DESTINATION` »ç¿ë
- ´ëÈ­ Áß Áı º¯°æ °¨Áö/¾÷µ¥ÀÌÆ®:
  - `ÀÌ»ç`, `ÁıÀº`, `¿ì¸®Áı`, `Áı ÁÖ¼Ò` µî È¨ ¾÷µ¥ÀÌÆ® ¹ßÈ­ °¨Áö
  - ¸ñÀûÁö°¡ ÃßÃâµÇ¸é ¼¼¼Ç ¸ñÀûÁö °»½Å + `upsert_user_profile`·Î DB ¹İ¿µ

### ±â´ë È¿°ú
- »ç¿ëÀÚ Áı ¸ñÀûÁö°¡ ¼¼¼Ç °£ À¯ÁöµÊ.
- "ÀÌ»çÇß¾î/ÁıÀº ~" ¹ßÈ­·Î ÃÖ½Å Áı ¸ñÀûÁö Áï½Ã °»½Å °¡´É.
- Åğ±Ù ¾È³»´Â ÃÖ½Å ÀúÀå Áı ¸ñÀûÁö¸¦ ±âº» µµÂøÁö·Î »ç¿ë.

## 2026-02-14 (Áı º¯°æ ¿©ºÎ¸¦ LLMÀÌ ÆÇÁ¤ÇÏµµ·Ï ÀüÈ¯)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- Áı º¯°æ/ÀÌ»ç ¿©ºÎ´Â ±ÔÄ¢ Å°¿öµåº¸´Ù ´ëÈ­ ¸Æ¶ô ±â¹İ ÆÇ´ÜÀÌ ÇÊ¿äÇÔ.
- Ä£±¸ Áı ¹æ¹®/¿ÜÃâ ¸ñÀûÁö¿Í ½ÇÁ¦ Áı º¯°æÀ» ±¸ºĞÇÏ·Á¸é LLM ÆÇÁ¤ÀÌ ÀûÇÕ.

### º¯°æ ³»¿ë
- IntentRouter Ãâ·Â ½ºÅ°¸¶ È®Àå:
  - ±âÁ¸: `intent`, `destination`
  - º¯°æ: `intent`, `destination`, `home_update`
- ¶ó¿ìÅÍ ½Ã½ºÅÛ ÇÁ·ÒÇÁÆ® °­È­:
  - `home_update=true`´Â »ç¿ëÀÚ ¹ßÈ­°¡ "ÁıÀÌ ¹Ù²î¾ú´Ù/ÀÌ»çÇß´Ù/Áı À§Ä¡ º¯°æ"À» ¸í½ÃÇÒ ¶§¸¸ Çã¿ë
  - ´Ü¼ø °æ·ÎÁú¹®(Ä£±¸ Áı/³î·¯°¨/¹æ¹®)Àº `home_update=false` °­Á¦
- »ç¿ëÀÚ ¹ßÈ­ Ã³¸® ·ÎÁ÷ º¯°æ:
  - DB Áı ¸ñÀûÁö upsert´Â `home_update=true`ÀÏ ¶§¸¸ ¼öÇà
  - fallback ¸ğµå¿¡¼­¸¸ ±âÁ¸ Å°¿öµå º¸Á¶ ÆÇ´Ü Çã¿ë
- ¶ó¿ìÅÍ ·Î±× È®Àå:
  - `[IntentRouter] ... home_update=...` Ãâ·Â

### ±â´ë È¿°ú
- "¼º¼ö °¡´Â ±æ" °°Àº ÀÏÈ¸¼º ¸ñÀûÁö Áú¹®À¸·Î Áı Á¤º¸°¡ Àß¸ø µ¤¾î½áÁö´Â ¹®Á¦ ¿ÏÈ­.
- ½ÇÁ¦ ÀÌ»ç/Áı º¯°æ ¹ßÈ­¿¡¼­¸¸ »ç¿ëÀÚ È¨ ¸ñÀûÁö°¡ ¾÷µ¥ÀÌÆ®µÊ.

## 2026-02-14 (WebSocket 1008 policy violation ¿ÏÈ­: ÀÔ·Â ÇÁ·¹ÀÓ Ã³¸® ¾ÈÁ¤È­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ Â¡ÈÄ
- °æ·Î ÁúÀÇ ÈÄ °£ÇæÀûÀ¸·Î `[Server] Error processing input: received 1008 (policy violation)` ¹ß»ıÇÏ¸ç ¿¬°á Á¾·á.

### º¯°æ ³»¿ë
- `receive_from_client` ÀÔ·Â ·çÇÁ¸¦ `ws.receive_bytes()` -> `ws.receive()` ±â¹İÀ¸·Î ÀüÈ¯.
- ¼ö½Å ÇÁ·¹ÀÓ Å¸ÀÔ ºĞ±â Ã³¸®:
  - `websocket.disconnect` Áï½Ã Á¾·á
  - `websocket.receive` Áß `bytes`¸¸ ¿Àµğ¿À ÀÔ·ÂÀ¸·Î Ã³¸®
  - text/control/non-binary ÇÁ·¹ÀÓÀº ¹«½Ã

### ±â´ë È¿°ú
- ÇÁ·¹ÀÓ Å¸ÀÔ ºÒÀÏÄ¡·Î ÀÎÇÑ policy violation(1008) ºóµµ °¨¼Ò.
- Start/Stop ¶Ç´Â ºê¶ó¿ìÀú Á¦¾î ÇÁ·¹ÀÓÀÌ ¼¯¿©µµ ¼¼¼Ç ¾ÈÁ¤¼º Çâ»ó.

## 2026-02-14 (°æ·Î ÁúÀÇ ¼±ÀÀ´ä¿¡¼­ À§Ä¡ ÀçÁú¹® ¹æÁö °­È­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ Â¡ÈÄ
- °æ·Î ´äº¯ ÀÚÃ¼´Â ¸ÂÁö¸¸, Ã¹ ¹®ÀåÀ¸·Î "ÇöÀç À§Ä¡ ¾Ë·Á´Ş¶ó"´Â ¹ßÈ­°¡ ¸ÕÀú ³ª¿À´Â ÄÉÀÌ½º Á¸Àç.

### ¿øÀÎ
- ½Ç½Ã°£ À½¼º ÀÀ´ä Å¸ÀÌ¹Ö °æÀïÀ¸·Î, µµ±¸ ÄÁÅØ½ºÆ® ¹İ¿µ Àü¿¡ ¸ğµ¨ÀÌ ¼±ÀÀ´äÇÒ ¼ö ÀÖÀ½.

### º¯°æ ³»¿ë
- ½Ã½ºÅÛ ÁöÄ§ °­È­:
  - ÇÑ±¹¾î ±³Åë ÁúÀÇ¿¡¼­´Â »ç¿ëÀÚ À§Ä¡¸¦ Àı´ë ÀçÁú¹®ÇÏÁö ¾Êµµ·Ï ¸í½Ã.
  - ¼¼¼Ç ½ÃÀÛ ½Ã ¼­¹ö°¡ Àü´ŞÇÑ `lat/lng`¸¦ ½Ã½ºÅÛ ÁöÄ§¿¡ ¸í½ÃÀûÀ¸·Î ÁÖÀÔ.
- °æ·Î intent Ã³¸® ½ÃÀÛ ½Ã ¼±ÁÖÀÔ °¡µå Ãß°¡:
  - `[INTENT:location_guard] Device location is already known ... Do not ask user location.`
- Áö¿¬ ÇÊ·¯ Áö½Ã °­È­:
  - ÇÊ·¯ ¸àÆ® ´Ü°è¿¡¼­µµ À§Ä¡ Áú¹® ±İÁö ¹®±¸ Ãß°¡.

### ±â´ë È¿°ú
- Ã¹ ÀÀ´ä¿¡¼­ "À§Ä¡ ¾Ë·ÁÁÖ¼¼¿ä" ¼±¹ßÈ­ ºóµµ °¨¼Ò.
- °æ·Î ¾È³»°¡ À§Ä¡ Áú¹® ¾øÀÌ ¹Ù·Î º»·ĞÀ¸·Î ½ÃÀÛµÉ °¡´É¼º Çâ»ó.

## 2026-02-14 (¼¼¼Ç Áß »ç¿ëÀÚ À§Ä¡ º¯°æ ¹İ¿µ)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`
- `temp_front/app/page.tsx`

### º¯°æ ÀÌÀ¯
- ±âÁ¸¿¡´Â WebSocket ¿¬°á ½ÃÁ¡ÀÇ `lat/lng`¸¸ »ç¿ëÇØ, ÀÌµ¿ Áß À§Ä¡ º¯°æÀÌ °æ·Î °è»ê¿¡ ¹İ¿µµÇÁö ¾ÊÀ½.

### º¯°æ ³»¿ë
- ÇÁ·ĞÆ®(`temp_front/app/page.tsx`)
  - `location_update` ¸Ş½ÃÁö Àü¼Û ÇÔ¼ö Ãß°¡
  - WebSocket ¿¬°á Á÷ÈÄ 1È¸ À§Ä¡ Àü¼Û
  - ¿¬°á Áß 15ÃÊ ÁÖ±â À§Ä¡ Àü¼Û Å¸ÀÌ¸Ó Ãß°¡
  - `Start Speaking` Á÷Àü À§Ä¡ 1È¸ °»½Å Àü¼Û
  - ¿¬°á Á¾·á/¿À·ù/¾ğ¸¶¿îÆ® ½Ã À§Ä¡ Å¸ÀÌ¸Ó Á¤¸®
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
- WebSocket ¿¬°á Áß ÁÖ±â À§Ä¡ ¾÷µ¥ÀÌÆ® °£°İÀ» `15ÃÊ`¿¡¼­ `60ÃÊ(1ºĞ)`·Î º¯°æ.
- ¿¬°á Á÷ÈÄ 1È¸ Àü¼Û, Start Speaking Á÷Àü 1È¸ Àü¼Û ·ÎÁ÷Àº À¯Áö.

### ±â´ë È¿°ú
- À§Ä¡ API È£Ãâ ºóµµ °¨¼Ò·Î Å¬¶óÀÌ¾ğÆ®/¹èÅÍ¸® ºÎ´ã ¿ÏÈ­.
- ¿©ÀüÈ÷ ´ëÈ­ ½ÃÀÛ Á÷Àü À§Ä¡´Â ÃÖ½Å »óÅÂ·Î ¹İ¿µ.

## 2026-02-14 (¼±¹ßÈ­/Áßº¹ ÀÀ´ä ¿ÏÈ­: ÇÊ·¯ ¿É¼ÇÈ­ + STT Áßº¹ µğµàÇÁ)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ Â¡ÈÄ
- °æ·Î ÁúÀÇ ½Ã ¸ğµ¨ÀÌ ¸ÕÀú "Á¤º¸ ¾øÀ½/À§Ä¡ ÇÊ¿ä" °°Àº ¼±¹ßÈ­¸¦ ÇÏ°Å³ª,
  À¯»çÇÑ °æ·Î ´äº¯ÀÌ 2È¸ Ãâ·ÂµÇ´Â ÄÉÀÌ½º°¡ °£Çæ ¹ß»ı.

### º¯°æ ³»¿ë
- ÇÊ·¯ ¸àÆ® ¿É¼ÇÈ­:
  - `ENABLE_TRANSIT_FILLER` È¯°æº¯¼ö Ãß°¡(±âº» `false`)
  - ±âº»°ª¿¡¼­ ÇÊ·¯ º°µµ ÅÏÀ» ºñÈ°¼ºÈ­ÇØ ÀÌÁß ÀÀ´ä °¡´É¼º Ãà¼Ò
  - ÇÊ¿ä ½Ã `.env`¿¡¼­ `ENABLE_TRANSIT_FILLER=true`·Î ÀçÈ°¼º °¡´É
- STT »ç¿ëÀÚ ÅÏ µğµàÇÁ Ãß°¡:
  - Azure STTÀÇ ±ÙÁ¢ Áßº¹ final chunk¸¦ 1.5ÃÊ À©µµ¿ì¿¡¼­ ½ºÅµ
  - ·Î±×: `[IntentRouter] skip duplicate user turn: ...`

### ±â´ë È¿°ú
- °°Àº Áú¹®¿¡ ´ëÇÑ Áßº¹ °æ·Î ¾È³» ºóµµ °¨¼Ò.
- ÄÁÅØ½ºÆ® ¹İ¿µ Àü ¼±ÀÀ´ä(ºÒÈ®½Ç ¸àÆ®) ¹ß»ı ºóµµ ¿ÏÈ­.

## 2026-02-14 (¼±¹ßÈ­/Áßº¹ ÀÀ´ä Ãß°¡ ¿ÏÈ­: Gemini Á÷Á¢ ¿Àµğ¿À ÀÔ·Â OFF ±âº»)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ Â¡ÈÄ
- °æ·Î ÁúÀÇ¿¡¼­ ¸ğµ¨ÀÌ ¸ÕÀú "ºÒ°¡/Á¤º¸ ¾øÀ½"À» ¸»ÇÑ µÚ, µÚ´Ê°Ô ¿Ã¹Ù¸¥ Á¤º¸¸¦ ÀçÀÀ´ä.
- À§Ä¡ ¾÷µ¥ÀÌÆ® ·Î±×°¡ ´Ù¼ö ¹İº¹ Ãâ·Â.

### ¿øÀÎ
- ¸¶ÀÌÅ© ¿Àµğ¿À°¡ Gemini·Î Á÷Á¢ µé¾î°¡´Â °æ·Î¿Í Azure STT ±â¹İ ÄÁÅØ½ºÆ® °æ·Î°¡ µ¿½Ã¿¡ Á¸ÀçÇØ,
  ÄÁÅØ½ºÆ® ¹İ¿µ Àü ¼±ÀÀ´ä/Áßº¹ ÅÏÀÌ ¹ß»ıÇÒ ¼ö ÀÖÀ½.

### º¯°æ ³»¿ë
- ÀÔ·Â °æ·Î ´Ü¼øÈ­:
  - `GEMINI_DIRECT_AUDIO_INPUT` È¯°æº¯¼ö µµÀÔ(±âº» `false`)
  - ±âº»°ª¿¡¼­ Gemini `send_realtime_input(audio=...)` ºñÈ°¼ºÈ­
  - Azure STT ÅØ½ºÆ®¸¦ ´ÜÀÏ ÀÔ·Â °æ·Î·Î »ç¿ë
- ÀÏ¹İ ´ëÈ­ ÀÀ´ä À¯Áö:
  - non-routing intent´Â `_send_user_text_turn(text)`·Î ÅØ½ºÆ® ÅÏÀ» Á÷Á¢ Àü´Ş
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
  - non-routing ÀÏ¹İ´ëÈ­¿ë `_send_user_text_turn` °­Á¦ È£Ãâ ºñÈ°¼ºÈ­
- °á°úÀûÀ¸·Î direct audio °æ·Î¸¦ ¸ŞÀÎ ÀÀ´ä Ã¤³Î·Î À¯ÁöÇÏ¸é¼­,
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
  - ´äº¯ ÈÄ ºÒÈ®½Ç¼º/Ãß°¡ Áú¹® ¹®Àå ±İÁö
  - Á¦°øµÈ ¿ä¾à¿¡ ¸í½ÃÀû µ¥ÀÌÅÍ ´©¶ôÀÌ ¾øÀ¸¸é "½Ç½Ã°£ Á¦°ø ºÒ°¡" ¹®±¸ ±İÁö

### ±â´ë È¿°ú
- "Á¤´ä -> °ğ¹Ù·Î ºÎÁ¤" ÇüÅÂÀÇ »óÃæ ÀÀ´ä ºóµµ °¨¼Ò.
- °æ·Î ÀÀ´äÀÌ ÇÑ ¹ø¿¡ ¸¶¹«¸®µÇµµ·Ï ¾ÈÁ¤È­.

## 2026-02-14 (°æ·Î ¿ä¾à ¿ì¼± ÀÀ´ä º¸Àå: transit turn gate µµÀÔ)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### ¹®Á¦ Â¡ÈÄ
- `live context built ... summary_ok=True`ÀÎµ¥µµ ¸ğµ¨ÀÌ "¸ğ¸¥´Ù/¶óÀÌºê ÄÁÅØ½ºÆ® ¾øÀ½"À» ¸ÕÀú ¸»ÇÏ´Â ÄÉÀÌ½º.

### ¿øÀÎ
- Gemini direct-audio ÀÔ·ÂÀÌ ÄÁÅØ½ºÆ® ÅÏº¸´Ù ¸ÕÀú Ã³¸®µÇ¾î,
  ÄÁÅØ½ºÆ® ¹Ì¹İ¿µ »óÅÂ ÀÀ´äÀÌ ¸ÕÀú »ı¼ºµÉ ¼ö ÀÖÀ½.

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
- "Á¤´ä µÚ¿¡ ¸ğ¸¥´Ù" ¶Ç´Â "¸ğ¸¥´Ù¸¸ ¸»ÇÔ" ÄÉÀÌ½º ¿ÏÈ­.

## 2026-02-15 (Ä«¸Ş¶ó ¿Â¿ÀÇÁ + Gemini ºñÀü ÀÔ·Â ¿¬µ¿)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`
- `temp_front/app/page.tsx`

### º¯°æ ÀÌÀ¯
- »ç¿ëÀÚ ¿äÃ»: ÇÁ·ĞÆ®¿¡¼­ Ä«¸Ş¶ó È­¸é ¿Â¿ÀÇÁ¸¦ Á¦°øÇÏ°í, Gemini À½¼º ´ëÈ­¿¡ Ä«¸Ş¶ó ½Ã°¢ ÄÁÅØ½ºÆ®¸¦ ÇÔ²² Àü´ŞÇÒ ¼ö ÀÖ°Ô ¿¬µ¿.

### º¯°æ ³»¿ë
- `backend/server.py`
  - ¼³Á¤ Ãß°¡: `CAMERA_FRAME_MIN_INTERVAL_SEC` (±âº» 1.0ÃÊ)
  - `/ws/audio` ÅØ½ºÆ® ¸Ş½ÃÁö Ã³¸® È®Àå:
    - `camera_state` (`enabled: true/false`) ¼ö½Å
    - `camera_frame_base64` (`mime_type`, `data`) ¼ö½Å
  - Ä«¸Ş¶ó ÇÁ·¹ÀÓ Àü¼Û ÇïÆÛ Ãß°¡:
    - Gemini Live ¼¼¼Ç¿¡ `send_realtime_input(media={...})`·Î ÀÌ¹ÌÁö ÁÖÀÔ
    - ÃÖ¼Ò Àü¼Û °£°İ(±âº» 1ÃÊ) Àû¿ë
  - ½Ã½ºÅÛ Áö½Ã¹®¿¡ Ä«¸Ş¶ó ÄÁÅØ½ºÆ® »ç¿ë Áö½Ã Ãß°¡
- `temp_front/app/page.tsx`
  - Ä«¸Ş¶ó Á¦¾î »óÅÂ/ÂüÁ¶ Ãß°¡:
    - `isCameraOn`, `video/canvas/stream/timer` ref
  - Ä«¸Ş¶ó ¿Â¿ÀÇÁ ¹öÆ° Ãß°¡ (`Camera On/Off`)
  - Ä«¸Ş¶ó ¹Ì¸®º¸±â ¿µ¿ª Ãß°¡
  - Ä«¸Ş¶ó ON ½Ã:
    - `getUserMedia(video)` ½ÃÀÛ
    - ¼­¹ö¿¡ `camera_state` Àü¼Û
    - 3ÃÊ °£°İÀ¸·Î JPEG ÇÁ·¹ÀÓ Ä¸Ã³ ÈÄ `camera_frame_base64` Àü¼Û
  - Ä«¸Ş¶ó OFF/¿¬°áÁ¾·á/·Î±×¾Æ¿ô/¾ğ¸¶¿îÆ® ½Ã:
    - Å¸ÀÌ¸Ó Á¤¸®, Æ®·¢ Á¾·á, `camera_state:false` Àü¼Û

### ±â´É ¸ñÀû
- À½¼º ´ëÈ­ Áß ÇöÀç Ä«¸Ş¶ó Àå¸éÀ» ÇÔ²² ¹İ¿µÇÑ ¸ÖÆ¼¸ğ´Ş ÀÀ´ä °¡´É ±â¹İ È®º¸.
- »ç¿ëÀÚ Á¦¾î(ON/OFF)·Î ¹èÅÍ¸®/Æ®·¡ÇÈ/ÇÁ¶óÀÌ¹ö½Ã¸¦ ¸í½ÃÀûÀ¸·Î °ü¸®.

## 2026-02-15 (Ä«¸Ş¶ó UX/ºñÀü ÀÀ´ä º¸°­)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`
- `temp_front/app/page.tsx`

### º¯°æ ÀÌÀ¯
- »ç¿ëÀÚ ÇÇµå¹é: Ä«¸Ş¶ó ¹Ì¸®º¸±â°¡ ³³ÀÛÇÏ°Ô º¸ÀÌ°í, ¸ğµ¨ÀÌ È­¸éÀ» ¸ø º»´Ù°í ´äÇÏ´Â ºóµµ°¡ ³ôÀ½.

### º¯°æ ³»¿ë
- `backend/server.py`
  - Ä«¸Ş¶ó »óÅÂ¿¡ `frames_sent` Ä«¿îÅÍ Ãß°¡.
  - Ã¹ ÇÁ·¹ÀÓ ¼ö½Å ½Ã Gemini ¼¼¼Ç¿¡ ºñÀü ÄÁÅØ½ºÆ® ÁÖÀÔ:
    - "Ä«¸Ş¶ó°¡ ÄÑÁ® ÀÖ°í ¶óÀÌºê ÇÁ·¹ÀÓÀ» ÃÖ¼Ò 1°³ ¹Ş¾Ò´Ù"´Â Á¤º¸ Àü´Ş.
  - Ä«¸Ş¶ó ON ½Ã ÃÊ±â ºñÀü ÄÁÅØ½ºÆ® ÈùÆ® ÁÖÀÔ.
  - 5ÇÁ·¹ÀÓ¸¶´Ù ¼­¹ö ·Î±× Ãâ·Â:
    - `[Vision] camera frames sent to Gemini: N`
- `temp_front/app/page.tsx`
  - Ä«¸Ş¶ó ¹öÆ° ¹®±¸¸¦ `Turn Camera On/Off`·Î º¯°æ (»óÅÂ È¥µ¿ ¿ÏÈ­)
  - Ä«¸Ş¶ó »óÅÂ ÅØ½ºÆ® Ãß°¡ (`ON/OFF`, Àü¼Û ÁÖ±â Ç¥½Ã)
  - ºñµğ¿À ¹Ì¸®º¸±â ºñÀ² °³¼±:
    - `h-40` °íÁ¤ ³ôÀÌ Á¦°Å
    - `aspect-video max-h-80 object-cover`·Î º¯°æ

### ±â´É ¸ñÀû
- »ç¿ëÀÚ°¡ Ä«¸Ş¶ó È°¼º »óÅÂ¸¦ ¸íÈ®È÷ ÀÎÁöÇÏ°í, ¹Ì¸®º¸±â ¿Ö°î ¾øÀÌ È®ÀÎ °¡´ÉÇÏ°Ô °³¼±.
- ¸ğµ¨ÀÌ ½ÇÁ¦ ÇÁ·¹ÀÓ ¼ö½Å ÀÌÈÄ¿¡´Â ½Ã°¢ ÄÁÅØ½ºÆ® ±â¹İÀ¸·Î ÀÀ´äÇÒ È®·ü Çâ»ó.

## 2026-02-15 (Ä«¸Ş¶ó ÇÁ·¹ÀÓ µğÄÚµå ¿À·ù ¼öÁ¤)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- ·±Å¸ÀÓ ·Î±×: `[Vision] camera frame decode failed: name 'base64' is not defined`
- Ä«¸Ş¶ó ÇÁ·¹ÀÓ(base64) µğÄÚµå °æ·Î¿¡¼­ import ´©¶ôÀ¸·Î ºñÀü ÀÔ·ÂÀÌ ÀüºÎ ½ÇÆĞÇÏ´ø ¹®Á¦ ¼öÁ¤.

### º¯°æ ³»¿ë
- `import base64` Ãß°¡.

### ±â´É ¸ñÀû
- Ä«¸Ş¶ó ÇÁ·¹ÀÓ µğÄÚµå Á¤»óÈ­·Î Gemini Live ºñÀü ÀÔ·Â °æ·Î º¹±¸.

## 2026-02-15 (Ä«¸Ş¶ó ¹Ì¸®º¸±â ¿µ¿ª È®´ë)

### ´ë»ó ÆÄÀÏ
- `temp_front/app/page.tsx`

### º¯°æ ÀÌÀ¯
- »ç¿ëÀÚ ÇÇµå¹é: Ä«¸Ş¶ó È­¸éÀÌ ³Ê¹« ÀÛ°í ³³ÀÛÇÏ°Ô º¸¿© ½ÃÀÎ¼ºÀÌ ³·À½.

### º¯°æ ³»¿ë
- ·¹ÀÌ¾Æ¿ô Æø È®Àå:
  - »ó´Ü/Ã¤ÆÃ ¿µ¿ª `max-w-4xl` -> `max-w-5xl`
  - ¸¶ÀÌÅ©/Ä«¸Ş¶ó ÄÁÆ®·Ñ ¿µ¿ª `max-w-4xl` -> `max-w-6xl`
- Ä«¸Ş¶ó ÇÁ¸®ºä ÄÁÅ×ÀÌ³Ê ÆĞµù È®´ë: `p-2` -> `p-3`
- Ä«¸Ş¶ó ºñµğ¿À Ç¥½Ã Å©±â È®´ë:
  - `aspect-video` À¯Áö
  - `min-h-[320px] md:min-h-[420px] max-h-[70vh]` Ãß°¡
  - ±âÁ¸ `max-h-80` Á¦°Å

### ±â´É ¸ñÀû
- µ¥½ºÅ©Åé¿¡¼­ Ä«¸Ş¶ó ÇÁ¸®ºä¸¦ ´õ Å©°Ô Ç¥½ÃÇØ È­¸é °øÀ¯Çü ´ëÈ­ ½ÃÀÎ¼º °³¼±.

## 2026-02-15 (ºê¶ó¿ìÀú È­¸é °øÀ¯ On/Off Ãß°¡)

### ´ë»ó ÆÄÀÏ
- `temp_front/app/page.tsx`

### º¯°æ ÀÌÀ¯
- »ç¿ëÀÚ ¿äÃ»: ºê¶ó¿ìÀú È­¸é °øÀ¯¸¦ ÄÑ°í ²ø ¼ö ÀÖ°Ô Ãß°¡.

### º¯°æ ³»¿ë
- »óÅÂ/¸®¼Ò½º Ãß°¡:
  - `isScreenOn`
  - `screenStreamRef`, `screenTimerRef`
  - `clearScreenTimer`, `stopScreenProcessing`
- ½Å±Ô ·ÎÁ÷:
  - `startScreenProcessing()`
    - `getDisplayMedia`·Î È­¸é °øÀ¯ ½ÃÀÛ
    - ¹Ì¸®º¸±â(video)¿¡ È­¸é ½ºÆ®¸² ¿¬°á
    - 2ÃÊ °£°İÀ¸·Î JPEG ÇÁ·¹ÀÓ Ä¸Ã³ ÈÄ ±âÁ¸ ¸Ş½ÃÁö ½ºÅ°¸¶(`camera_frame_base64`)·Î Àü¼Û
  - `toggleScreenShare()` Ãß°¡
- »óÈ£ ¹èÅ¸ Ã³¸®:
  - È­¸é °øÀ¯ ½ÃÀÛ ½Ã Ä«¸Ş¶ó ½ºÆ®¸² Á¾·á
  - Ä«¸Ş¶ó ½ÃÀÛ ½Ã È­¸é °øÀ¯ Á¾·á
- Á¤¸® °æ·Î º¸°­:
  - disconnect/error/logout/unmount ½Ã È­¸é °øÀ¯ ½ºÆ®¸²/Å¸ÀÌ¸Ó Á¤¸®
- UI Ãß°¡:
  - `Start/Stop Screen Share` ¹öÆ°
  - »óÅÂ ¶óº§¿¡ `Screen ON/OFF` Ç¥½Ã

### ±â´É ¸ñÀû
- Ä«¸Ş¶ó ¿Ü¿¡µµ ºê¶ó¿ìÀú ÅÇ/Ã¢/ÀüÃ¼ È­¸éÀ» Gemini ºñÀü ÀÔ·ÂÀ¸·Î Àü´Ş °¡´ÉÇÏ°Ô È®Àå.

## 2026-02-15 (È­¸é°øÀ¯ Áß À½¼º ²÷±è ¿ÏÈ­ Æ©´×)

### ´ë»ó ÆÄÀÏ
- `temp_front/app/page.tsx`

### º¯°æ ÀÌÀ¯
- »ç¿ëÀÚ ÇÇµå¹é: È­¸é °øÀ¯ Áß AI ´äº¯ÀÌ Áß°£¿¡ ²÷±â´Â Çö»ó.
- ¿øÀÎ °¡¼³: µ¿ÀÏ WS¿¡¼­ ÀÌ¹ÌÁö ÇÁ·¹ÀÓ ¾÷·Îµå°¡ ¿Àµğ¿À Àç»ı/ÀÀ´ä ½ºÆ®¸²°ú °æÇÕ.

### º¯°æ ³»¿ë
- AI ¹ßÈ­ Áß ÇÁ·¹ÀÓ Àü¼Û ÀÏ½Ã ÁßÁö ·ÎÁ÷ Ãß°¡:
  - ¼­¹ö¿¡¼­ ¿Àµğ¿À Blob ¼ö½Å ½Ã `aiSpeaking` »óÅÂ¸¦ ¾à 900ms À¯Áö
  - `aiSpeaking` »óÅÂ¿¡¼­´Â Ä«¸Ş¶ó/È­¸é°øÀ¯ ÇÁ·¹ÀÓ ¾÷·Îµå skip
- ÇÁ·¹ÀÓ ÆäÀÌ·Îµå °æ·®È­:
  - Ä«¸Ş¶ó: 640x360@Q0.65 -> 512x288@Q0.45
  - È­¸é°øÀ¯: 960x540@Q0.7 -> 640x360@Q0.5
- Àü¼Û ÁÖ±â ¿ÏÈ­:
  - Ä«¸Ş¶ó 3ÃÊ -> 4ÃÊ
  - È­¸é°øÀ¯ 2ÃÊ -> 5ÃÊ

### ±â´É ¸ñÀû
- ½Ç½Ã°£ À½¼º ÀÀ´ä ¿ì¼±¼øÀ§¸¦ º¸ÀåÇÏ¸é¼­ ºñÀü ÄÁÅØ½ºÆ®´Â ÀúºÎÇÏ·Î À¯Áö.
- ´äº¯ Áß°£ ²÷±è ºóµµ °¨¼Ò.

## 2026-02-15 (ºñÀü Àü¼Û Á¤Ã¥ ÀüÈ¯: ¿¬¼Ó ÇÁ·¹ÀÓ -> ¹ßÈ­ ½Ã ½º³À¼¦)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`
- `temp_front/app/page.tsx`

### º¯°æ ÀÌÀ¯
- »ç¿ëÀÚ ¿äÃ»: ½Ç»ç¿ë ¹æ½ÄÃ³·³ È­¸é ON »óÅÂ¿¡¼­µµ Áö¿¬À» ÁÙÀÌ±â À§ÇØ, »ç¿ëÀÚ°¡ ¸»ÇÒ ¶§ Ä¸Ã³º»À» º¸³»°í ºñÀü Áú¹®ÀÏ ¶§¸¸ »ç¿ëÇÏµµ·Ï ÀüÈ¯.

### º¯°æ ³»¿ë
- `backend/server.py`
  - ¼³Á¤ Ãß°¡: `VISION_SNAPSHOT_TTL_SEC` (±âº» 20ÃÊ)
  - ºñÀü Áú¹® °¨Áö ÇÔ¼ö `_is_vision_related_query()` Ãß°¡
  - ¼¼¼Ç »óÅÂ¿¡ ÃÖ½Å ½º³À¼¦ ÀúÀå:
    - `camera_snapshot_base64` ¼ö½Å ½Ã `latest_snapshot`, `snapshot_ts` °»½Å
  - »ç¿ëÀÚ ¹ßÈ­ Ã³¸® ½Ã:
    - ºñÀü °ü·Ã Áú¹®ÀÌ¸é ÃÖ½Å ½º³À¼¦(À¯È¿±â°£ ³»)¸¸ Gemini·Î ÁÖÀÔ
    - ºñÀü ¹«°ü Áú¹®Àº ½º³À¼¦ ¹Ì»ç¿ë
- `temp_front/app/page.tsx`
  - Ä«¸Ş¶ó/È­¸é°øÀ¯ÀÇ ¿¬¼Ó Å¸ÀÌ¸Ó Àü¼Û Á¦°Å
  - `sendVisionSnapshot()` Ãß°¡:
    - ¹ßÈ­ ½ÃÀÛ(`Start Speaking`) ½Ã ÇöÀç ¹Ì¸®º¸±â 1Àå Ä¸Ã³ÇØ `camera_snapshot_base64` Àü¼Û
  - »óÅÂ ¹®±¸¸¦ ½º³À¼¦ ¸ğµå·Î º¯°æ:
    - `ON (snapshot on speak)`

### ±â´É ¸ñÀû
- À½¼º ÀÀ´ä Áö¿¬/²÷±èÀ» ÁÙÀÌ¸é¼­µµ, ÇÊ¿ä ½Ã ºñÀü ÄÁÅØ½ºÆ®¸¦ È°¿ëÇÏ´Â ½Ç¹«Çü(on-demand) ¸ÖÆ¼¸ğ´Ş µ¿ÀÛ Á¦°ø.

## 2026-02-15 (STT Áö¿¬/Á¤È®µµ °³¼±: 16k ¸®»ùÇÃ + ºĞÀı Å¸ÀÓ¾Æ¿ô Æ©´×)

### ´ë»ó ÆÄÀÏ
- `temp_front/app/page.tsx`
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- »ç¿ëÀÚ ÇÇµå¹é: STT ¹Ş¾Æ¾²±â Áö¿¬ ¹× ÀÎ½Ä Á¤È®µµ ÀúÇÏ.
- ¿øÀÎ ÃßÁ¤: ºê¶ó¿ìÀú ½ÇÁ¦ »ùÇÃ·¹ÀÌÆ®(´ë°³ 48k)¸¦ 16k·Î °¡Á¤ÇØ ±×´ë·Î Àü¼ÛÇÏ´ø ±¸Á¶.

### º¯°æ ³»¿ë
- `temp_front/app/page.tsx`
  - ¸¶ÀÌÅ© ÀÔ·Â ¸®»ùÇÃ ÇÔ¼ö `resampleTo16k()` Ãß°¡.
  - ÀÔ·Â AudioContext¸¦ ÇÏµå¿ş¾î ±âº» »ùÇÃ·¹ÀÌÆ®·Î »ı¼º ÈÄ, `onaudioprocess`¿¡¼­ 16k·Î º¯È¯ÇØ Àü¼Û.
  - ScriptProcessor ¹öÆÛ Å©±â 4096 -> 2048·Î ³·Ãç Áö¿¬ ¿ÏÈ­.
- `backend/server.py`
  - STT ºĞÀı Å¸ÀÓ¾Æ¿ôÀ» °íÁ¤ 100ms¿¡¼­ È¯°æº¯¼ö ±â¹İÀ¸·Î º¯°æ:
    - `STT_SEGMENTATION_SILENCE_TIMEOUT_MS` (±âº» 280)

### ±â´É ¸ñÀû
- »ùÇÃ·¹ÀÌÆ® ºÒÀÏÄ¡·Î ÀÎÇÑ ÀÎ½Ä Ç°Áú ÀúÇÏ¸¦ ÁÙÀÌ°í,
- ³Ê¹« ÂªÀº ºĞÀı·Î ¹®ÀåÀÌ ²÷±â´Â ¹®Á¦¸¦ ¿ÏÈ­ÇØ STT Ç°Áú/ÀÀ´ä Ã¼°¨ °³¼±.

## 2026-02-15 (ºñÀü ½º³À¼¦ °¡¿ë¼º º¸°­: Àç½Ãµµ + TTL È®Àå)

### ´ë»ó ÆÄÀÏ
- `temp_front/app/page.tsx`
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- »ç¿ëÀÚ ÇÇµå¹é: Ä«¸Ş¶ó ON »óÅÂ¿¡¼­µµ °£ÇæÀûÀ¸·Î "È­¸éÀ» ¸ø º»´Ù" ÀÀ´ä ¹ß»ı.
- ¿øÀÎ: ¹ßÈ­ ½ÃÁ¡¿¡ ºñµğ¿À ÇÁ·¹ÀÓ ÁØºñ°¡ ´Ê¾î ½º³À¼¦ÀÌ ºñ¾î ÀÖ´Â ÅÏÀÌ Á¸Àç.

### º¯°æ ³»¿ë
- `temp_front/app/page.tsx`
  - `sendVisionSnapshot()`¸¦ ¼º°ø ¿©ºÎ ¹İÈ¯À¸·Î º¯°æ.
  - `sendVisionSnapshotWithRetry()` Ãß°¡:
    - Ä¸Ã³ ½ÇÆĞ ½Ã 250ms °£°İ, ÃÖ´ë 6È¸ Àç½Ãµµ.
  - ½º³À¼¦ Æ®¸®°Å È®´ë:
    - Ä«¸Ş¶ó ON Á÷ÈÄ 1È¸ Àç½Ãµµ Ä¸Ã³
    - È­¸é°øÀ¯ ON Á÷ÈÄ 1È¸ Àç½Ãµµ Ä¸Ã³
    - `Start Speaking` ½Ã Àç½Ãµµ Ä¸Ã³
- `backend/server.py`
  - ½º³À¼¦ À¯È¿½Ã°£ ±âº»°ª È®´ë:
    - `VISION_SNAPSHOT_TTL_SEC`: 20 -> 120
  - ºñÀü Áú¹®ÀÎµ¥ ½º³À¼¦ÀÌ ¾øÀ» ¶§ ¼­¹ö ·Î±× Ãß°¡:
    - `[Vision] vision query detected but no fresh snapshot available`

### ±â´É ¸ñÀû
- ÇÁ·¹ÀÓ ÁØºñ Å¸ÀÌ¹Ö ÀÌ½´·Î ½º³À¼¦ÀÌ ºñ¾î "¸ø º½" ÀÀ´äÀÌ ³ª¿À´Â ºóµµ °¨¼Ò.
- ÃÖ±Ù Ä¸Ã³º»À» ´õ ¿À·¡ Àç»ç¿ëÇØ ºñÀü ÁúÀÇ ¾ÈÁ¤¼º Çâ»ó.

## 2026-02-15 (ÇÏÀÌºê¸®µå ºñÀü ¸ğµå: ¹ßÈ­ ½Ã + ÀúÁÖ±â ¾÷µ¥ÀÌÆ®)

### ´ë»ó ÆÄÀÏ
- `temp_front/app/page.tsx`

### º¯°æ ÀÌÀ¯
- »ç¿ëÀÚ ¿äÃ»: Ä«¸Ş¶ó/ºê¶ó¿ìÀú È­¸é °øÀ¯°¡ ÄÑÁ® ÀÖÀ» ¶§¸¸ ºñÀü ·ÎÁ÷À» µ¿ÀÛ½ÃÅ°°í, ¹ßÈ­ ½Ã ½º³À¼¦ ±â¹İ µ¿ÀÛ¿¡ ´õÇØ ÀúÁÖ±â °»½ÅÀ» ÇÔ²² »ç¿ë.

### º¯°æ ³»¿ë
- ºñÀü ÇÏÆ®ºñÆ® Å¸ÀÌ¸Ó Ãß°¡:
  - `visionHeartbeatTimerRef`
  - 10ÃÊ °£°İÀ¸·Î ½º³À¼¦ Àü¼Û ½Ãµµ (`sendVisionSnapshotWithRetry`)
  - AI°¡ ¸»ÇÏ´Â Áß(`aiSpeakingRef=true`)¿¡´Â Àü¼Û ½ºÅµ
- Ä«¸Ş¶ó/È­¸é °øÀ¯ ½ÃÀÛ ½Ã:
  - ±âÁ¸ÀÇ Áï½Ã ½º³À¼¦ 1È¸ + Àç½Ãµµ ·ÎÁ÷ À¯Áö
  - ÇÏÆ®ºñÆ® Å¸ÀÌ¸Ó ½ÃÀÛ
- Ä«¸Ş¶ó/È­¸é °øÀ¯ Á¾·á ¹× ¾ğ¸¶¿îÆ® ½Ã:
  - ÇÏÆ®ºñÆ® Å¸ÀÌ¸Ó Á¤¸®
- »óÅÂ ¹®±¸ ¾÷µ¥ÀÌÆ®:
  - `snapshot on speak` -> `speak + 10s update`

### ±â´É ¸ñÀû
- Æò¼Ò¿¡´Â ¿Àµğ¿À Áö¿¬À» ÁÙÀÌ±â À§ÇØ °úµµÇÑ ¿¬¼Ó ÇÁ·¹ÀÓÀ» ÇÇÇÏ°í,
- Ä«¸Ş¶ó/È­¸é °øÀ¯ ON »óÅÂ¿¡¼­¸¸ ÃÖ½Å ½Ã°¢ ÄÁÅØ½ºÆ®¸¦ À¯ÁöÇÏ´Â ÇÏÀÌºê¸®µå ¸ğµå Á¦°ø.

## 2026-02-15 (ºñÀü ½º³À¼¦ Àü¼Û ½ÇÆĞ ¼öÁ¤)

### ´ë»ó ÆÄÀÏ
- `temp_front/app/page.tsx`

### º¯°æ ÀÌÀ¯
- ·Î±×¿¡¼­ `camera_state: enabled=true`´Â µé¾î¿À´Âµ¥ `camera_snapshot_base64`°¡ °»½ÅµÇÁö ¾Ê¾Æ
  `[Vision] vision query detected but no fresh snapshot available`°¡ ¹İº¹ ¹ß»ı.
- ¿øÀÎ: ½º³À¼¦ Àü¼Û ÇÔ¼ö°¡ React »óÅÂ Å¬·ÎÀú(`isCameraOn/isScreenOn`) Á¶°Ç¿¡ ¸·Çô Àü¼ÛÀÌ ½ºÅµµÉ ¼ö ÀÖ¾úÀ½.

### º¯°æ ³»¿ë
- `sendVisionSnapshot()`¿¡¼­ »óÅÂ°ª °¡µå Á¦°Å:
  - Á¦°Å: `if (!(isCameraOn || isScreenOn)) return;`
  - À¯Áö: WebSocket OPEN, video/canvas Á¸Àç, `videoWidth/videoHeight > 0` °¡µå
- `sendVisionSnapshotWithRetry()` Àç½Ãµµ ¹üÀ§ È®´ë:
  - ÃÖ´ë 6È¸(¾à 1.5ÃÊ) -> ÃÖ´ë 20È¸(¾à 5ÃÊ)

### ±â´É ¸ñÀû
- Ä«¸Ş¶ó/È­¸é ON Á÷ÈÄ ÇÁ·¹ÀÓ ÁØºñ Áö¿¬ÀÌ ÀÖ¾îµµ ½º³À¼¦ÀÌ ½ÇÁ¦·Î ¼­¹ö¿¡ µµ´ŞÇÏµµ·Ï º¸Àå.
- ºñÀü ÁúÀÇ ½Ã "fresh snapshot ¾øÀ½" ¿À·ù ºóµµ °¨¼Ò.

## 2026-02-15 (ºñÀü ¿¬¼Ó ½ºÆ®¸®¹Ö ¸ğµå º¹±Í)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`
- `temp_front/app/page.tsx`
- `temp_front/out/_next/static/chunks/791d6006ec8e18fd.js` (Á¤Àû ¹èÆ÷ ÇÖÇÈ½º)

### º¯°æ ÀÌÀ¯
- ½º³À¼¦ ±â¹İ ÇÏÀÌºê¸®µå ¸ğµå¿¡¼­ `no fresh snapshot available`°¡ ¹İº¹µÇ¾î ½Ç½Ã°£ ºñÀü ÁúÀÇ°¡ ½ÇÆĞ.
- »ç¿ëÀÚ ¿äÃ»¿¡ µû¶ó ÃÊ±â ¹æ½Ä(Ä«¸Ş¶ó/È­¸é ON µ¿¾È ¿¬¼Ó Àü¼Û)À¸·Î º¹±Í.

### º¯°æ ³»¿ë
- `backend/server.py`
  - `camera_snapshot_base64` ¼ö½Å ½Ã ÀúÀå¸¸ ÇÏ´ø ·ÎÁ÷À» º¯°æ:
    - `latest_snapshot/snapshot_ts` °»½Å + Áï½Ã Gemini·Î ÇÁ·¹ÀÓ Àü¼Û(`_send_camera_frame_to_gemini`)
  - ºñÀü ÁúÀÇ ½Ã ½º³À¼¦ÀÌ ¾øÀ» ¶§ °­Á¦ ºÎÁ¤ ÄÁÅØ½ºÆ®(`No recent snapshot...`) ÁÖÀÔ Á¦°Å.
- `temp_front/app/page.tsx`
  - ºñÀü heartbeat¸¦ 10ÃÊ¿¡¼­ 1.2ÃÊ·Î Á¶Á¤ÇÏ¿© »ç½Ç»ó ¿¬¼Ó ½ºÆ®¸®¹ÖÀ¸·Î º¹±Í.
  - AI ¹ßÈ­ Áß ½ºÅµ Á¶°Ç Á¦°Å(¿¬¼Ó Àü¼Û À¯Áö).
  - »óÅÂ ¹®±¸¸¦ `continuous stream`À¸·Î º¯°æ.
- `temp_front/out/...js`
  - Á¤Àû ¼­ºù °æ·Î ¹İ¿µÀ» À§ÇØ ¿¬¼Ó Àü¼Û µ¿ÀÛÀÌ Áï½Ã Àû¿ëµÇµµ·Ï ÇÖÇÈ½º ¹İ¿µ.

### ±â´É ¸ñÀû
- Ä«¸Ş¶ó/È­¸é °øÀ¯ ON »óÅÂ¿¡¼­ ºñÀü ÄÁÅØ½ºÆ®¸¦ ¾ÈÁ¤ÀûÀ¸·Î °è¼Ó °ø±ŞÇØ,
- ¸ğµ¨ÀÌ "È­¸é ¸ø º½"À¸·Î ºüÁö´Â Çö»óÀ» ÁÙÀÌ°í ½Ç½Ã°£ ÁúÀÇ ÀÀ´äÀ» º¹±¸.

## 2026-02-15 (ºñÀü ·Î±× Ãà¼Ò + ½Ç½Ã°£ È­¸é ¸»Åõ °íÁ¤)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- ¿¬¼Ó ºñÀü ½ºÆ®¸®¹Ö¿¡¼­ `snapshot updated` ·Î±×°¡ °ú´Ù Ãâ·ÂµÇ¾î ÄÜ¼Ö °¡µ¶¼ºÀÌ ¶³¾îÁü.
- »ç¿ëÀÚ Ã¼°¨Àº ½Ç½Ã°£ È­¸é ´ëÈ­ÀÎµ¥, ¸ğµ¨ÀÌ "º¸³»ÁÖ½Å ÀÌ¹ÌÁö/»çÁø" °°Àº Ç¥ÇöÀ» »ç¿ëÇØ ¾î»öÇÔ ¹ß»ı.

### º¯°æ ³»¿ë
- ºñÀü ·Î±× Ãà¼Ò:
  - `camera_state`¿¡ `snapshot_updates` Ä«¿îÅÍ Ãß°¡
  - ½º³À¼¦ ·Î±×¸¦ ¸Å¹ø Ãâ·ÂÇÏÁö ¾Ê°í `1È¸Â÷` ¹× `20È¸ ´ÜÀ§`·Î¸¸ Ãâ·Â
  - Ä«¸Ş¶ó OFF ½Ã `snapshot_updates` Ä«¿îÅÍ ¸®¼Â
- ¸»Åõ/Ç¥Çö ÁöÄ§ °­È­:
  - ½Ã½ºÅÛ Áö½Ã¹®¿¡ "½Ã°¢ ÄÁÅØ½ºÆ®°¡ ÀÖÀ» ¶§ 'º¸³»ÁÖ½Å ÀÌ¹ÌÁö/»çÁø¿¡¼­/½Ç½Ã°£ È­¸é ¸ø º»´Ù' Ç¥Çö ±İÁö" Ãß°¡
  - "Áö±İ È­¸é¿¡¼­ ..."Ã³·³ ½Ç½Ã°£ È­¸é ±âÁØÀ¸·Î ´äº¯ÇÏµµ·Ï ¸í½Ã
- ³»ºÎ ºñÀü ÄÁÅØ½ºÆ® ¹®±¸ Á¤¸®:
  - `[VISION] A recent user-side snapshot ...` -> `[VISION] Recent visual context ...`

### ±â´É ¸ñÀû
- ¿î¿µ ·Î±× ³ëÀÌÁî¸¦ ÁÙÀÌ¸é¼­ µğ¹ö±ë¿¡ ÇÊ¿äÇÑ ÇÙ½É Ä«¿îÆ®´Â À¯Áö.
- »ç¿ëÀÚ¿¡°Ô ½Ç½Ã°£ È­¸é ´ëÈ­Ã³·³ ÀÚ¿¬½º·´°Ô µé¸®´Â ÀÀ´ä Åæ ÀÏ°ü¼º È®º¸.

## 2026-02-15 (weather/air intent¿¡¼­ ODSay È£Ãâ Â÷´Ü)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- `weather`/`air_quality` ÁúÀÇ¿¡¼­µµ °øÅë live ºô´õ¸¦ ÅëÇØ ODSay(¿ª/°æ·Î)°¡ È£ÃâµÇ¾î,
  ODSay IP ¹Ìµî·Ï È¯°æ¿¡¼­ ºÒÇÊ¿äÇÑ ÀÎÁõ ¿¡·¯ ·Î±×°¡ ¹İº¹ ¹ß»ı.

### º¯°æ ³»¿ë
- `_execute_tools_for_intent()` ÃÊ±â¿¡ intent ºĞ±â Ãß°¡:
  - `intent in {"weather", "air_quality"}`ÀÏ ¶§
    - ODSay/¿ª Å½»ö/°æ·Î °è»êÀ» ÀüºÎ ¿ìÈ¸
    - `_get_weather_and_air(lat, lng)`¸¸ È£ÃâÇØ °á°ú ±¸¼º
    - ÇØ´ç intent Àü¿ë `speechSummary`¸¦ Áï½Ã »ı¼ºÇØ ¹İÈ¯
- ±âÁ¸ ±³Åë intent(`subway_route`, `bus_route`, `commute_overview`)´Â ±âÁ¸ °æ·Î À¯Áö.

### ±â´É ¸ñÀû
- ³¯¾¾/´ë±âÁú ÁúÀÇ¿¡¼­ ODSay ÀÇÁ¸ Á¦°Å.
- ODSay Å°/Çã¿ë IP ÀÌ½´°¡ ÀÖ¾îµµ ³¯¾¾/´ë±âÁú ÀÀ´äÀº Á¤»ó Á¦°ø.

## 2026-02-15 (weather/air ÄÁÅØ½ºÆ® ¿ì¼± ÀÀ´ä °­Á¦)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- `intent=weather`/`air_quality`¿¡¼­ `summary_ok=True`ÀÎµ¥µµ ¸ğµ¨ÀÌ "¶óÀÌºê ÄÁÅØ½ºÆ® ¾øÀ½"Ã³·³ ÀÀ´äÇÏ´Â ÄÉÀÌ½º ¹ß»ı.
- ¿øÀÎ: ÇØ´ç intent´Â `ACTION` Áö½Ã/`complete_turn` °­Á¦°¡ ºüÁ® ÄÁÅØ½ºÆ® ÁÖÀÔ ¿ì¼±¼øÀ§°¡ ³·¾ÒÀ½.

### º¯°æ ³»¿ë
- µ¿Àû ÄÁÅØ½ºÆ® ÁÖÀÔ ·ÎÁ÷¿¡¼­ ¿ì¼±Ã³¸® intent ÁıÇÕ È®Àå:
  - ±âÁ¸: `subway_route`, `bus_route`, `commute_overview`
  - º¯°æ: `subway_route`, `bus_route`, `commute_overview`, `weather`, `air_quality`
- À§ intentµé¿¡ ´ëÇØ:
  - `[ACTION]` Áö½Ã¹® Ãß°¡ Àû¿ë
  - `complete_turn=True`·Î ÄÁÅØ½ºÆ® ÅÏ ¿ì¼± Ã³¸®
  - direct audio ÀÔ·Â °ÔÀÌÆ®(2.5ÃÊ) µ¿ÀÏ Àû¿ë

### ±â´É ¸ñÀû
- ³¯¾¾/´ë±âÁú ÁúÀÇ¿¡¼­µµ »ı¼ºµÈ live summary¸¦ ¿ì¼± »ç¿ëÇØ Áï´ä.
- "µ¥ÀÌÅÍ ¾øÀ½/ÄÁÅØ½ºÆ® ¾øÀ½" ¿ÀÀÀ´ä ºóµµ °¨¼Ò.

## 2026-02-15 (¼±Çà "¸ğ¸§" ÀÀ´ä Â÷´Ü: °ÔÀÌÆ® ½ÃÁ¡ ¾Õ´ç±è)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- weather/air ÁúÀÇ¿¡¼­ live context(`summary_ok=True`)°¡ ¸¸µé¾îÁ³´Âµ¥µµ
  direct-audio °æ·Î ÀÀ´äÀÌ ¸ÕÀú ³ª°¡ "¾Ë ¼ö ¾øÀ½" ¹ßÈ­°¡ ¼±ÇàµÇ´Â ¹®Á¦ ¹ß»ı.

### º¯°æ ³»¿ë
- `should_inject_live` ºĞ±â ÁøÀÔ Áï½Ã direct-audio °ÔÀÌÆ®¸¦ ¼±Àû¿ë:
  - `transit_turn_gate["until"] = now + 4.0s` (max ¹æ½Ä)
  - À§Ä¡/Åø È£Ãâ/ÄÁÅØ½ºÆ® ÁÖÀÔº¸´Ù ¸ÕÀú Àû¿ë
- ±âÁ¸ ACTION ±¸°£ÀÇ °ÔÀÌÆ® °»½ÅÀº À¯ÁöÇÏµÇ `max` ¹æ½ÄÀ¸·Î ´©Àû ¿¬Àå.

### ±â´É ¸ñÀû
- ¶ó¿ìÆÃ intent(weather/air Æ÷ÇÔ)¿¡¼­ raw audio ¼±ÀÀ´äÀ» ¸·°í,
- live context ±â¹İ ÃÖÁ¾ ´äº¯ÀÌ ¸ÕÀú ³ª¿Àµµ·Ï ¼ø¼­ º¸Àå °­È­.

## 2026-02-15 (¼±¹ßÈ­ Â÷´Ü 2Â÷: Ãâ·Â ¿Àµğ¿À °ÔÀÌÆ® Ãß°¡)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- ÀÔ·Â °ÔÀÌÆ®¸¦ ¾Õ´ç°Üµµ, ÀÌ¹Ì Gemini¿¡¼­ »ı¼ºµÈ ¼±ÀÀ´ä ¿Àµğ¿À°¡ ¸ÕÀú »ç¿ëÀÚ¿¡°Ô Ãâ·ÂµÇ´Â ÄÉÀÌ½º°¡ ³²À½.

### º¯°æ ³»¿ë
- `send_to_client()` Ãâ·Â ·çÇÁ¿¡ ¿Àµğ¿À °ÔÀÌÆ® Ãß°¡:
  - `time.monotonic() < transit_turn_gate['until']` µ¿¾ÈÀº `part.inline_data` ¿Àµğ¿À¸¦ `ws.send_bytes`·Î Àü´ŞÇÏÁö ¾Ê°í Æó±â.
- ±âÁ¸ ÀÔ·Â °ÔÀÌÆ®(¼ö½Å ¿Àµğ¿À `send_realtime_input` Â÷´Ü)¿Í ÇÔ²² µ¿ÀÛÇÏ¿©
  ¶ó¿ìÆÃ intent(weather/air Æ÷ÇÔ)ÀÇ ¼±ÀÀ´ä °¡´É¼ºÀ» ÀÌÁßÀ¸·Î Â÷´Ü.

### ±â´É ¸ñÀû
- "¾Ë ¼ö ¾øÀ½" °°Àº ¼±Çà ¹ßÈ­¸¦ »ç¿ëÀÚ¿¡°Ô µé¸®Áö ¾Ê°Ô Â÷´Ü.
- live context ±â¹İ ÃÖÁ¾ ´äº¯¸¸ ¿ì¼± Ãâ·ÂµÇµµ·Ï ¼ø¼­ ¾ÈÁ¤È­.

## 2026-02-15 (³¯¾¾/´ë±âÁú ÀÀ´ä Áö¿¬ ¿ÏÈ­: °ÔÀÌÆ® Å¸ÀÌ¹Ö Æ©´×)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- ¼±¹ßÈ­´Â »ç¶óÁ³Áö¸¸, °ÔÀÌÆ® ½Ã°£ÀÌ ±æ¾î ÃÖÁ¾ ´äº¯ ½ÃÀÛ Áö¿¬ÀÌ Ä¿Áü.

### º¯°æ ³»¿ë
- ¶ó¿ìÆÃ intent ÁøÀÔ ½Ã ÃÊ±â °ÔÀÌÆ® Ãà¼Ò:
  - `+4.0s` -> `+1.2s`
- ACTION ´Ü°è ¿¬Àå °ÔÀÌÆ® Ãà¼Ò:
  - `+2.5s` -> `+0.8s`
- `injected_context`¸¦ ½ÇÁ¦ ¼¼¼Ç¿¡ Àü¼ÛÇÑ Á÷ÈÄ °ÔÀÌÆ® Á¶±â ÇØÁ¦ ·ÎÁ÷ Ãß°¡:
  - `transit_turn_gate['until']`¸¦ `now+0.15s` ¼öÁØÀ¸·Î ºü¸£°Ô ´ç±è(`min` »ç¿ë)

### ±â´É ¸ñÀû
- ¼±Çà "¸ğ¸§" ¹ßÈ­ Â÷´ÜÀº À¯ÁöÇÏ¸é¼­,
- live context ÁÖÀÔ ¿Ï·á ÈÄ ´äº¯ ½ÃÀÛ Áö¿¬À» ÃÖ¼ÒÈ­.

## 2026-02-15 (weather/air¿¡¼­ ¸ñÀûÁö ÄÁÅØ½ºÆ® È¥ÀÔ Â÷´Ü)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- `intent=weather`ÀÎµ¥µµ ¸ñÀûÁö(¿¹: ±¤È­¹®) °¡ÀÌµå°¡ ÇÔ²² ÁÖÀÔµÇ¾î,
  "±¤È­¹®/ÀÌÅÂ¿ø ÀÌµ¿ °èÈ¹" °°Àº ±³Åë¼º ¹®ÀåÀÌ ³¯¾¾ ´äº¯ ¾Õ¿¡ ¼¯ÀÌ´Â Çö»ó ¹ß»ı.

### º¯°æ ³»¿ë
- µ¿Àû guidance »ı¼º ·ÎÁ÷¿¡ `transit_intents` ºĞ¸® Ãß°¡:
  - `transit_intents = {"subway_route", "bus_route", "commute_overview"}`
- ¸ñÀûÁö °ü·Ã guidance/Áú¹® À¯µµ´Â transit intent¿¡¼­¸¸ Àû¿ë:
  - `Use destination ...` ¹®±¸
  - ¸ñÀûÁö ÀçÁú¹®(`Ask destination exactly once ...`)
- weather/air intent´Â À§Ä¡ ±â¹İ ³¯¾¾/´ë±âÁú Á¤º¸¸¸ ÁÖÀÔÇÏµµ·Ï Á¤¸®.

### ±â´É ¸ñÀû
- ³¯¾¾/´ë±âÁú ÁúÀÇ¿¡¼­ ¸ñÀûÁö ÁÖÁ¦ È¥ÀÔ Á¦°Å.
- Áú¹® intent¿¡ ¸Â´Â ´ÜÀÏ ÁÖÁ¦ ´äº¯ ¾ÈÁ¤È­.

## 2026-02-15 (weather/air¿¡¼­ destination Àü´Ş/·Î±× ¿ÏÀü Á¦°Å)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- `intent=weather`ÀÎµ¥µµ `live context built` ·Î±×¿¡ `destination=±¤È­¹®`ÀÌ ÂïÇô
  ¹®¸Æ È¥ÀÔÃ³·³ º¸ÀÌ°í ½ÇÁ¦ ÀÀ´ä¿¡µµ ±³Åë¼º ¹®ÀåÀÌ ¼¯ÀÏ ¿©Áö°¡ ÀÖ¾úÀ½.

### º¯°æ ³»¿ë
- live context ±¸¼º Á÷Àü¿¡ `context_destination` µµÀÔ:
  - `intent in {subway_route, bus_route, commute_overview}`ÀÏ ¶§¸¸ `destination_state['name']` »ç¿ë
  - `weather`, `air_quality`, `general`Àº `None` »ç¿ë
- `_execute_tools_for_intent(... destination_name=...)`¿¡ `context_destination` Àü´Ş
- ·Î±×µµ `destination={context_destination}`·Î Ãâ·Â

### ±â´É ¸ñÀû
- ³¯¾¾/´ë±âÁú ÁúÀÇ¿¡¼­ ¸ñÀûÁö ÄÁÅØ½ºÆ® Àü´ŞÀ» ¿ÏÀüÈ÷ Â÷´Ü.
- ·Î±×¿Í ½ÇÁ¦ ÄÁÅØ½ºÆ®¸¦ µ¿ÀÏÇÏ°Ô ¸ÂÃç µğ¹ö±ë È¥¼± Á¦°Å.

## 2026-02-15 (¼±¹ßÈ­ Àç¹ß ¹æÁö 3Â÷: ¼±ÀÀ´ä ÅÏ Æó±â °¡µå)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- `intent=weather`, `summary_ok=True` ÀÌÈÄ¿¡µµ °£ÇæÀûÀ¸·Î "¾Ë ¼ö ¾øÀ½" ¼±ÀÀ´äÀÌ ¸ÕÀú Ãâ·ÂµÇ´Â ·¹ÀÌ½º°¡ Àç¹ß.
- ¿øÀÎ: live context Àû¿ë Àü »ı¼ºµÈ ¿Àµğ¿À ÅÏÀÌ Ãâ·Â´Ü¿¡¼­ ¸ÕÀú Àü´ŞµÇ´Â °æ¿ì°¡ Á¸Àç.

### º¯°æ ³»¿ë
- `response_guard` »óÅÂ Ãß°¡:
  - `active`, `context_sent`, `suppressed_audio_seen`
- ¶ó¿ìÆÃ intent Ã³¸® ½ÃÀÛ ½Ã °¡µå È°¼ºÈ­.
- live context ÁÖÀÔ ¿¹¾à ÈÄ `context_sent=True` ¼³Á¤.
- Ãâ·Â ·çÇÁ(`send_to_client`)¿¡¼­:
  - °ÔÀÌÆ® ±¸°£ ¿Àµğ¿À´Â Æó±â + `suppressed_audio_seen=True` ±â·Ï
  - ±¸Çü ÅÏÀ¸·Î ÆÇ´ÜµÇ´Â ¿Àµğ¿À´Â `turn_complete` Àü±îÁö °è¼Ó Æó±â
- `turn_complete` ½Ã °¡µå ÇØÁ¦:
  - stale turn Á¾·á ÈÄ ´ÙÀ½ ÅÏºÎÅÍ Á¤»ó Ãâ·Â Çã¿ë

### ±â´É ¸ñÀû
- ÄÁÅØ½ºÆ® ÀÌÀü¿¡ »ı¼ºµÈ ¼±Çà "¸ğ¸§" ¹ßÈ­¸¦ »ç¿ëÀÚ¿¡°Ô Àü´ŞÇÏÁö ¾Êµµ·Ï Â÷´Ü.
- ÃÖÁ¾ live context ±â¹İ ´äº¯¸¸ ¿ì¼± Ãâ·ÂµÇµµ·Ï ¾ÈÁ¤È­.

## 2026-02-15 (¼±¹ßÈ­ Àç¹ß 4Â÷: ÄÁÅØ½ºÆ® ¿ì¼± ÅÏ direct-audio ÇÏµå Â÷´Ü)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- Ãâ·Â °ÔÀÌÆ®¸¸À¸·Î´Â ¼±ÀÀ´äÀÌ ¿ÏÀüÈ÷ »ç¶óÁöÁö ¾Ê°í,
  weather/air ÁúÀÇ¿¡¼­ "¾ø´Ù/¸ğ¸¥´Ù" ¼±¹ßÈ­ ÈÄ Á¤´äÀÌ µÚµû¸£´Â ·¹ÀÌ½º°¡ Àç¹ß.

### º¯°æ ³»¿ë
- `response_guard` È®Àå:
  - `block_direct_audio`
  - `block_direct_audio_until`
- `should_inject_live` ÁøÀÔ ½Ã:
  - direct-audio ÀÔ·ÂÀ» Áï½Ã ÇÏµå Â÷´Ü(`block_direct_audio=True`)
  - ¾ÈÀü Å¸ÀÓ¾Æ¿ô(`+6s`) ¼³Á¤
- ÀÔ·Â ·çÇÁÀÇ Gemini direct-audio Àü¼Û Á¶°Ç °­È­:
  - `block_direct_audio=False`ÀÏ ¶§¸¸ Àü¼Û
  - `block_direct_audio_until` °æ°ú ÈÄ¿¡¸¸ Àü¼Û
- `turn_complete`¿¡¼­ °¡µå ÇØÁ¦:
  - stale/normal guarded turn Á¾·á ½Ã direct-audio Â÷´Ü ÇØÁ¦

### ±â´É ¸ñÀû
- ÄÁÅØ½ºÆ® ¿ì¼± ÅÏ¿¡¼­ raw audio ¼±ÀÀ´ä ÀÚÃ¼¸¦ ÀÔ·Â´Ü¿¡¼­ ¿øÃµ Â÷´Ü.
- "¼±¹ßÈ­ -> Á¤´ä" ÀÌÁß ÀÀ´äÀ» ±¸Á¶ÀûÀ¸·Î ¾ïÁ¦.

## 2026-02-15 (weather/air Áö¿¬ Ã¼°¨ ¿ÏÈ­: ¼±Çà È®ÀÎ ¸àÆ® Ãß°¡)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- ³¯¾¾/´ë±âÁú °ª Á¶È¸ Àü ÂªÀº °ø¹é ±¸°£¿¡¼­ »ç¿ëÀÚ Ã¼°¨ÀÌ ³ªºüÁü.
- »ç¿ëÀÚ ¿äÃ»: "Á¦°¡ È®ÀÎÇØº¼°Ô¿ä" °°Àº ÂªÀº Áö¿¬ ¸àÆ® ¼±Çà.

### º¯°æ ³»¿ë
- `should_inject_live` ºĞ±â¿¡¼­ `intent in {weather, air_quality}`ÀÏ ¶§,
  live °ª ÀÀ´ä Àü¿¡ º°µµ filler ÅÏ ÁÖÀÔ:
  - `_inject_live_context_now(..., complete_turn=True)`
  - Áö½Ã: ÇÑ ¹®Àå È®ÀÎ ¸àÆ®¸¸ ¹ßÈ­
  - Áö½Ã: °ª/ÈÄ¼ÓÁú¹®Àº filler ÅÏ¿¡¼­ ±İÁö

### ±â´É ¸ñÀû
- ³¯¾¾/´ë±âÁú Á¶È¸ Áö¿¬ µ¿¾È ´ëÈ­ Èå¸§À» ÀÚ¿¬½º·´°Ô À¯Áö.
- »ç¿ëÀÚ ÀÔÀå¿¡¼­ "¸ØÃá ´À³¦"À» ÁÙÀÌ°í ÀÀ´ä ¿¹Ãø °¡´É¼º Çâ»ó.

## 2026-02-15 (¼±¹ßÈ­ °­Á¦ Â÷´Ü 5Â÷: ÄÁÅØ½ºÆ® ÅÏ µ¿¾È direct-audio ¿ÏÀü Â÷´Ü)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- weather/air ÁúÀÇ¿¡¼­ ¿©ÀüÈ÷ "Á¤º¸¸¦ ¸ø °¡Á®¿Â´Ù" ¼±¹ßÈ­°¡ ¸ÕÀú Ãâ·ÂµÇ´Â ÄÉÀÌ½º Áö¼Ó.
- ¿ä±¸»çÇ×: ¼±¹ßÈ­¸¦ °­Á¦·Î Áö¿¬ ¸àÆ®/ÄÁÅØ½ºÆ® ±â¹İ ÀÀ´äÀ¸·Î ´ëÃ¼.

### º¯°æ ³»¿ë
- `response_guard` »óÅÂ È®Àå:
  - `forced_intent_turn` Ãß°¡
- `should_inject_live` ÁøÀÔ ½Ã (weather/air Æ÷ÇÔ ÄÁÅØ½ºÆ® ¿ì¼± ÅÏ):
  - `block_direct_audio=True` °­Á¦
  - `block_direct_audio_until=now+8s` ¾ÈÀü Å¸ÀÓ¾Æ¿ô
  - `forced_intent_turn=intent` ±â·Ï
- ÀÔ·Â ·çÇÁÀÇ Gemini direct-audio Àü¼Û Á¶°ÇÀº ±âÁ¸´ë·Î
  - `block_direct_audio=False`ÀÏ ¶§¸¸ Çã¿ë
- Ãâ·Â turn_complete¿¡¼­ guarded turn Á¾·á ½Ã:
  - `block_direct_audio` ÇØÁ¦
  - `forced_intent_turn` ÃÊ±âÈ­

### ±â´É ¸ñÀû
- ÄÁÅØ½ºÆ® ¿ì¼± ÅÏ¿¡¼­ raw audio ¼±ÀÀ´äÀ» ÀÔ·Â´Ü¿¡¼­ ¿øÃµ Â÷´Ü.
- "¼±¹ßÈ­(¸ğ¸§) -> ½ÇÁ¦°ª" ÀÌÁßÀÀ´äÀ» ±¸Á¶ÀûÀ¸·Î ¾ïÁ¦.

## 2026-02-15 (weather/air ¼±¹ßÈ­ °­Á¦ Æó±â: Ã¹ ÅÏ µå·Ó + ÄÁÅØ½ºÆ® ÀçÁÖÀÔ)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- weather/air¿¡¼­ direct-audio ·¹ÀÌ½º·Î ¼±Çà "¸ğ¸§" ÅÏÀÌ ³²¾Æ, ±âÁ¸ °ÔÀÌÆ®/Â÷´Ü¸¸À¸·Î ¿ÏÀü Á¦°ÅµÇÁö ¾ÊÀ½.

### º¯°æ ³»¿ë
- `response_guard` È®Àå:
  - `drop_first_turn`, `reinject_context_text`
- `should_inject_live` ÁøÀÔ ½Ã( weather/air + direct-audio ): 
  - `drop_first_turn=True` ¼³Á¤
- ÄÁÅØ½ºÆ® »ı¼º ÈÄ(weather/air):
  - `reinject_context_text=ctx_text` ÀúÀå
- Ãâ·Â ·çÇÁ:
  - `drop_first_turn=True` µ¿¾È Ã¹ ¸ğµ¨ ¿Àµğ¿À ÅÏÀ» ÀüºÎ Æó±â
  - ÇØ´ç ÅÏÀÇ `turn_complete` ¼ö½Å ½Ã:
    - `drop_first_turn=False`
    - ÀúÀåµÈ `reinject_context_text`¸¦ `complete_turn=True`·Î ÀçÁÖÀÔ

### ±â´É ¸ñÀû
- weather/air ÁúÀÇ¿¡¼­ ¼±Çà "Á¤º¸ ¾øÀ½" ÅÏÀ» ±¸Á¶ÀûÀ¸·Î Á¦°Å.
- ÀÌÈÄ live context ±â¹İ ÃÖÁ¾ ´äº¯ ÅÏ¸¸ »ç¿ëÀÚ¿¡°Ô Ãâ·Â.

## 2026-02-15 (weather/air ¾ÈÁ¤È­: Áï½Ã ·Îµù¸àÆ® + Áßº¹/²÷±è °æ·Î Á¤¸®)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- »ç¿ëÀÚ ÀÌ½´ 3Á¾ µ¿½Ã ¹ß»ı:
  1) ·Îµù¸àÆ®°¡ ´ÊÀ½
  2) °°Àº ´äº¯ Áßº¹ ¹ßÈ­
  3) ¹Ì¼¼¸ÕÁö ÁúÀÇ ½Ã 1008 ¿¬°á Á¾·á

### º¯°æ ³»¿ë
- Áï½Ã ·Îµù¸àÆ®:
  - ¶ó¿ìÅÍ È£Ãâ Àü¿¡ Å°¿öµå(³¯¾¾/±â¿Â/°­¼ö/¹Ì¼¼¸ÕÁö/´ë±âÁú/aqi) °¨Áö ½Ã
  - `loading_weather_fast` ÅÏÀ» Áï½Ã `complete_turn=True`·Î ÁÖÀÔ
- Áßº¹ ¿ÏÈ­:
  - STT µğµàÇÁ Á¤±ÔÈ­ °­È­: °ø¹é¸¸ Á¦°Å -> °ø¹é/¹®ÀåºÎÈ£/Æ¯¼ö¹®ÀÚ Á¦°Å
  - `weather_filler_text` Áßº¹ ÁÖÀÔ ¹æÁö(`pre_weather_filler_sent` µµÀÔ)
- 1008 ¾ÈÁ¤È­:
  - Ãâ·Â ·çÇÁÀÇ `drop_first_turn/reinject_context_text` ±â¹İ ÀçÁÖÀÔ °æ·Î Á¦°Å
  - ÇØ´ç °æ·Î´Â Ãâ·Â task ³»ºÎ¿¡¼­ Ãß°¡ `send_client_content` È£ÃâÀ» ¸¸µé¾î ºÒ¾ÈÁ¤ ¿øÀÎÀÌ µÉ ¼ö ÀÖ¾î Á¦°Å
- direct-audio Â÷´Ü Å¸ÀÓ¾Æ¿ô Á¶Á¤:
  - `block_direct_audio_until` 8ÃÊ -> 4ÃÊ

### ±â´É ¸ñÀû
- Áú¹® Á÷ÈÄ Ã¼°¨ °¡´ÉÇÑ ·Îµù ¸àÆ® Á¦°ø.
- µ¿ÀÏ ´äº¯ 2È¸ ¹ßÈ­ °¨¼Ò.
- ¹Ì¼¼¸ÕÁö ÁúÀÇ ½Ã Ãâ·Â ·çÇÁ °ü·Ã 1008 ²÷±è ¸®½ºÅ© ¿ÏÈ­.

## 2026-02-15 (weather/air ÀÀ´ä Ã¼°¨ °³¼±: ÇÊ·¯ ¼±¹ßÈ­ µ¿±â º¸Àå + Á¶È¸ ºĞ¸®)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- »ç¿ëÀÚ ÇÇµå¹é:
  - weather ÈÄ air_quality¿¡¼­ ¼±¹ßÈ­ Àç¹ß
  - ´äº¯ Áö¿¬ Å­
  - ÇÊ·¯ ¸àÆ®°¡ Á¶È¸ ¿Ï·á ÈÄ ´Ê°Ô ³ª¿À´Â Ã¼°¨

### º¯°æ ³»¿ë
- ÇÊ·¯ ¼ø¼­ º¸Àå:
  - weather/air intent¿¡¼­ live Á¶È¸ Àü¿¡ filler ÅÏÀ» ÁÖÀÔ
  - `run_coroutine_threadsafe(...).result(timeout=1.0)`·Î Á¦Ãâ ¿Ï·á¸¦ µ¿±â º¸Àå
  - ÇÊ·¯ ¹®±¸´Â °ª/ÈÄ¼ÓÁú¹® ±İÁö
- Áßº¹ ÇÊ·¯ °æ·Î Á¤¸®:
  - Å°¿öµå ±â¹İ »çÀü ÇÊ·¯ °æ·Î Á¦°Å
  - weather/air Àü¿ë ´ÜÀÏ ÇÊ·¯ °æ·Î·Î ÅëÇÕ
- ¼Óµµ °³¼±:
  - `weather`´Â `_get_weather_only()`¸¸ È£Ãâ
  - `air_quality`´Â `_get_air_only()`¸¸ È£Ãâ
  - ±âÁ¸Ã³·³ µÎ API¸¦ ¸Å¹ø ¸ğµÎ È£ÃâÇÏ´ø ±¸Á¶ Á¦°Å

### ±â´É ¸ñÀû
- Áú¹® Á÷ÈÄ Áï½Ã ÇÊ·¯°¡ ¸ÕÀú ³ª¿À°í, °ª ÀÀ´äÀº ±× ´ÙÀ½À¸·Î ÀÏ°üµÇ°Ô Ãâ·Â.
- ³¯¾¾/´ë±âÁú ÀÀ´ä Áö¿¬ °¨¼Ò.
- weather -> air_quality ¿¬¼Ó ÁúÀÇ ½Ã ¼±¹ßÈ­ Àç¹ß °¡´É¼º ¿ÏÈ­.

## 2026-02-15 (weather/air Àü¿ë ÀÀ´ä °æ·Î ´Ü¼øÈ­: ÇÊ·¯ Áï½Ã ¹ßÈ­ ¿ì¼±)

### ´ë»ó ÆÄÀÏ
- `backend/server.py`

### º¯°æ ÀÌÀ¯
- weather -> air_quality ¿¬¼Ó ÁúÀÇ¿¡¼­ ¼±¹ßÈ­ Àç¹ß ¹× Ã¼°¨ Áö¿¬ ¹ß»ı.
- ¿øÀÎ: transit¿ë Ãâ·Â °ÔÀÌÆ® ·ÎÁ÷°ú env intent°¡ ÇÔ²² Àû¿ëµÇ¸ç ÇÊ·¯ Å¸ÀÌ¹ÖÀÌ ¹Ğ¸± ¼ö ÀÖÀ½.

### º¯°æ ³»¿ë
- `should_inject_live`¿¡¼­ env intent(`weather`, `air_quality`) ºĞ±â ºĞ¸®:
  - env intent´Â `response_guard.active=False` (Ãâ·Â suppress ·ÎÁ÷ ºñÈ°¼º)
  - env intent´Â `transit_turn_gate`¸¦ ÇöÀç½Ã°¢À¸·Î ¼³Á¤ÇØ Ãâ·Â °ÔÀÌÆ®¸¦ »ç½Ç»ó ºñÈ°¼º
  - direct-audio´Â env Ã³¸® Áß¿¡¸¸ Àá±ñ Â÷´Ü(`block_direct_audio_until=+5s`)
- env intent ÄÁÅØ½ºÆ® ÁÖÀÔ ¿Ï·á Á÷ÈÄ:
  - `block_direct_audio` Áï½Ã ÇØÁ¦
  - forced intent °¡µå ÃÊ±âÈ­

### ±â´É ¸ñÀû
- weather/air¿¡¼­ ÇÊ·¯ ¸àÆ®¸¦ Áï½Ã µé¸®°Ô ÇÏ°í,
- °ª ÀÀ´äÀº ÇÑ ¹ø¸¸ ºü¸£°Ô ÀÌ¾îÁöµµ·Ï °æ·Î ´Ü¼øÈ­.

## 2026-02-15 - È¯°æ(³¯¾¾/´ë±âÁú) »ó¼¼ Ä³½Ã ¼±ÀûÀç °³¼±
- ¼öÁ¤ ÆÄÀÏ: `backend/server.py`
- ¸ñÀû: Á¢¼Ó Á÷ÈÄ ³¯¾¾/´ë±âÁú µ¥ÀÌÅÍ¸¦ ¹Ì¸® °¡Á®¿Í ¼¼¼Ç Ä³½Ã¿¡ ÀúÀåÇÏ°í, Áú¹® ½Ã Áï½Ã ÀÀ´äÇÒ ¼ö ÀÖµµ·Ï °³¼±.

### º¯°æ ³»¿ë
1. ¼¼¼Ç È¯°æ Ä³½Ã Ãß°¡
- `audio_websocket` ¼¼¼Ç »óÅÂ¿¡ `env_cache`¸¦ Ãß°¡Çß½À´Ï´Ù.
- ±¸Á¶: `weather`, `air`, `lat`, `lng`, `ts(monotonic)`.

2. Á¢¼Ó ½Ã ¼±ÀûÀç(preload)
- Gemini Live ¼¼¼Ç ¿¬°á Á÷ÈÄ `_preload_env_cache(force=True)`¸¦ È£ÃâÇØ ÇöÀç ÁÂÇ¥ ±âÁØ ³¯¾¾/´ë±âÁúÀ» ¹Ì¸® ÀúÀåÇÏµµ·Ï Çß½À´Ï´Ù.
- ·Î±×: `[SeoulInfo] Env cache refreshed: weather=..., air=...`.

3. À§Ä¡ º¯°æ ½Ã ¹é±×¶ó¿îµå °»½Å
- `location_update` ¼ö½Å ½Ã ÀÌµ¿ °Å¸®(`>=80m`)°¡ È®ÀÎµÇ¸é ¹é±×¶ó¿îµå·Î Ä³½Ã °»½Å ÀÛ¾÷À» Æ®¸®°ÅÇÏµµ·Ï Çß½À´Ï´Ù.
- °úµµÇÑ È£ÃâÀ» ÁÙÀÌ±â À§ÇØ TTL/°Å¸® Á¶°ÇÀ» ÇÔ²² »ç¿ëÇÕ´Ï´Ù.

4. Ä³½Ã ½Å¼±µµ ÆÇº° ÇÔ¼ö Ãß°¡
- `_is_env_cache_fresh(env_cache, lat, lng)` Ãß°¡.
- TTL(`ENV_CACHE_TTL_SEC`)°ú ÁÂÇ¥ ÀÌµ¿ °Å¸®(<200m) ±âÁØÀ¸·Î Ä³½Ã À¯È¿¼º ÆÇ´Ü.

5. weather/air intent¿¡¼­ Ä³½Ã ¿ì¼± »ç¿ë
- `_execute_tools_for_intent(..., env_cache=...)`¿¡¼­ `weather`, `air_quality` ÀÇµµ Ã³¸® ½Ã Ä³½Ã¸¦ ¿ì¼± »ç¿ëÇÕ´Ï´Ù.
- Ä³½Ã°¡ ¿À·¡µÇ¾ú°Å³ª ÁÂÇ¥°¡ ¸¹ÀÌ ¹Ù²ï °æ¿ì `_get_weather_and_air`·Î ÇÑ ¹ø¿¡ ÀçÁ¶È¸ÇÏ°í Ä³½Ã °»½ÅÇÕ´Ï´Ù.

6. »ó¼¼ ÇÊµå ÀúÀå + À½¼º ¿ä¾à È®Àå
- ³¯¾¾ ÀúÀå ÇÊµå: ÇöÀç±â¿Â, °­¼ö·®, ºñ, ±¸¸§·®, ÄÚµå, ÇÏ´Ã»óÅÂ, ÃÖ°í/ÃÖÀú, °­¼öÈ®·ü.
- ´ë±âÁú ÀúÀå ÇÊµå: US AQI, PM2.5, PM10, µî±Ş.
- À½¼º ¿ä¾àÀº °£°áÇÏ°Ô À¯ÁöÇÏµÇ(ÇöÀç/ÃÖ°íÃÖÀú/°­¼öÈ®·ü/ÇÏ´Ã»óÅÂ µî), »ó¼¼ µ¥ÀÌÅÍ´Â Ä³½Ã¿¡ À¯ÁöÇÕ´Ï´Ù.

### ÃÖ¼Ò ¼öÁ¤ ¿øÄ¢
- `server.py`, `run_server.py` ±¸Á¶´Â À¯ÁöÇÏ°í, ±âÁ¸ ¶ó¿ìÆÃ/À½¼º ÆÄÀÌÇÁ¶óÀÎÀ» °Çµå¸®Áö ¾Ê´Â ¹üÀ§¿¡¼­ Ä³½Ã °æ·Î¸¸ º¸°­Çß½À´Ï´Ù.
- Ãß°¡ Á¶Á¤: `weather/air_quality` ÀÇµµÀÇ °­Á¦ ÇÊ·¯ ¸àÆ® ÁÖÀÔ ºí·ÏÀ» Á¦°ÅÇß½À´Ï´Ù. (Á¢¼Ó ½Ã ¼±ÀûÀç Ä³½Ã »ç¿ë ÀüÁ¦·Î Áï´ä)
- Ãß°¡ ¼öÁ¤(¼±¹ßÈ­ Â÷´Ü): `weather/air_quality`¸¦ Æ÷ÇÔÇÑ ¸ğµç ¶óÀÌºê ÀÇµµ¿¡¼­ ÀÀ´ä °ÔÀÌÆ®¸¦ µ¿ÀÏÇÏ°Ô È°¼ºÈ­Çß½À´Ï´Ù.
- Ãß°¡ ¼öÁ¤(ÇÙ½É): ¶óÀÌºê ÄÁÅØ½ºÆ®°¡ ½ÇÁ¦·Î ÁÖÀÔ(`context_sent=True`)µÇ±â Àü ¸ğµ¨ ¿Àµğ¿À´Â °­Á¦·Î µå·ÓÇÏµµ·Ï Ã³¸®Çß½À´Ï´Ù.
- ±â´ë È¿°ú: Ä³½Ã°¡ ÀÖ¾îµµ ¸ÕÀú ³ª°¡´ø "È®ÀÎ ºÒ°¡" ¼±¹ßÈ­¸¦ Â÷´ÜÇÏ°í, ÄÁÅØ½ºÆ® ±â¹İ ÃÖÁ¾ ´äº¯¸¸ Ãâ·Â.

## 2026-02-15 - ³×ÀÌ¹ö ´º½º ±â´É(ºê·£Ä¡ feature/news_phy) ÃÖ¼Ò °áÇÕ
- ¼öÁ¤ ÆÄÀÏ: `backend/server.py`
- ¸ñÀû: ±âÁ¸ À½¼º ´ëÈ­ ÆÄÀÌÇÁ¶óÀÎÀ» À¯ÁöÇÑ Ã¤ ´º½º ÁúÀÇ¸¦ ¸ğµâ ¹æ½ÄÀ¸·Î Ã³¸®.

### º¯°æ ³»¿ë
1. ´º½º ¸ğµâ ¿¬°á
- `from modules.news_agent import NewsAgent` Ãß°¡.
- ¼­¹ö ½ÃÀÛ ½Ã `NEWS_AGENT` ÃÊ±âÈ­(½ÇÆĞ ½Ã ¾ÈÀüÇÏ°Ô `None` Ã³¸®).

2. Intent Router È®Àå
- fallback Å°¿öµå¿¡ `´º½º/Çìµå¶óÀÎ/¼Óº¸/±â»ç` Ãß°¡.
- LLM intent Çã¿ë ÁıÇÕ¿¡ `news` Ãß°¡.

3. ´º½º Á¶È¸ ÇïÆÛ Ãß°¡
- `_extract_news_topic_from_text(text)`: ¹ßÈ­¿¡¼­ ´º½º ÅäÇÈ ÃßÃâ.
- `_get_news_headlines(topic, limit)`: `NewsAgent._search_naver_news` È£Ãâ ÈÄ Çìµå¶óÀÎ ¸ñ·Ï ¹İÈ¯.

4. ÀÇµµ ½ÇÇà ºĞ±â Ãß°¡
- `_execute_tools_for_intent(..., user_text=...)`¿¡ `news` ºĞ±â Ãß°¡.
- ¹İÈ¯ ±¸Á¶¿¡ `news.topic`, `news.headlines` Æ÷ÇÔ.
- À½¼º¿ë `speechSummary`´Â Âª°Ô ±¸¼º.

5. ¶óÀÌºê ÀÀ´ä °æ·Î ¿¬°á
- `routing_intents` / `context_priority_intents`¿¡ `news` Ãß°¡.
- `_execute_tools_for_intent` È£Ãâ ½Ã `user_text` Àü´Ş.

### Âü°í
- ÀÌ¹ø Ä¿¹ÔÀº `server.py` ÃÖ¼Ò °áÇÕ¸¸ ¼öÇàÇß½À´Ï´Ù.
- ±âÁ¸ ±³Åë/³¯¾¾/´ë±âÁú ·ÎÁ÷Àº À¯ÁöÇÏ°í, ´º½º ÁúÀÇ¸¸ Ãß°¡ È®ÀåÇß½À´Ï´Ù.

## 2026-02-15 - Gmail ±ä±Ş ¸ŞÀÏ ¾Ë¸²(ÇÁ·Î¾×Æ¼ºê) Ãß°¡
- ¼öÁ¤ ÆÄÀÏ: `backend/modules/gmail_alert_module.py`, `backend/server.py`
- ¸ñÀû: Gmail ¸ŞÀÏ Áß ±ä±Ş Å°¿öµå°¡ Æ÷ÇÔµÈ ¸ŞÀÏ¸¸ »ç¿ëÀÚ¿¡°Ô ¼±Á¦ÀûÀ¸·Î À½¼º ¾È³».

### º¯°æ ³»¿ë
1. ½Å±Ô ¸ğµâ Ãß°¡: `backend/modules/gmail_alert_module.py`
- Gmail IMAP(ssl)·Î `UNSEEN` ¸ŞÀÏ Á¶È¸.
- Á¦¸ñ/º»¹®/º¸³½»ç¶÷ ±â¹İ ±ä±Ş Å°¿öµå ¸ÅÄª.
- Áßº¹ ¾Ë¸² ¹æÁö¸¦ À§ÇØ `Message-ID` ±â¹İ delivered set À¯Áö.
- ¾Ë¸² ¹®±¸ ¿ä¾à(`summary`) »ı¼º.

2. ¼­¹ö ¿¬°á (`backend/server.py`)
- `GmailAlertModule` ÃÊ±âÈ­ ¹× ¼¼¼Ç ³» ¹é±×¶ó¿îµå ·çÇÁ(`gmail_alert_loop`) Ãß°¡.
- ¿¬°á Áß ÁÖ±â(`GMAIL_POLL_INTERVAL_SEC`)¸¶´Ù ±ä±Ş ¸ŞÀÏ È®ÀÎ.
- »ç¿ëÀÚ ¹ßÈ­ Á÷ÈÄ/ÀÀ´ä ÁßÀÎ ÅÏÀº °Ç³Ê¶Ù¾î ´ëÈ­ ¹æÇØ ÃÖ¼ÒÈ­.
- Å½Áö ½Ã Gemini¿¡ ¶óÀÌºê ÄÁÅØ½ºÆ®·Î ÁÖÀÔÇÏ¿© ÇÑ ¹®Àå ÇÁ·Î¾×Æ¼ºê ¾È³».

3. È¯°æº¯¼ö Ãß°¡
- `GMAIL_IMAP_USER`: Gmail ÁÖ¼Ò
- `GMAIL_IMAP_APP_PASSWORD`: Gmail ¾Û ºñ¹Ğ¹øÈ£(2´Ü°è ÀÎÁõ ±â¹İ)
- `GMAIL_IMAP_MAILBOX`: ±âº» `INBOX`
- `GMAIL_URGENT_KEYWORDS`: ÄŞ¸¶ ±¸ºĞ Å°¿öµå ¸ñ·Ï
- `GMAIL_POLL_INTERVAL_SEC`: Æú¸µ ÁÖ±â(ÃÊ), ±âº» 60
- `GMAIL_ALERT_BIND_USER`: websocket user_id¿Í Gmail °èÁ¤ ÀÏÄ¡ ½Ã¸¸ ¾Ë¸²(±âº» true)

## 2026-02-15 - Gmail ±ä±Ş¸ŞÀÏ 2´Ü°è ºĞ·ù(Å°¿öµå + LLM) Àû¿ë
- ¼öÁ¤ ÆÄÀÏ: `backend/modules/gmail_alert_module.py`
- ¸ñÀû: ´Ü¼ø Å°¿öµå ¿ÀÅ½À» ÁÙÀÌ±â À§ÇØ 2´Ü°è ÆÇÁ¤À¸·Î °íµµÈ­.

### 2´Ü°è ÆÇÁ¤
1. 1Â÷: Å°¿öµå ÈÄº¸ ÇÊÅÍ
- Á¦¸ñ/º»¹®/¹ß½ÅÀÚ ÅØ½ºÆ®¿¡ `GMAIL_URGENT_KEYWORDS` Æ÷ÇÔ ½Ã ÈÄº¸·Î Ã¤ÅÃ.

2. 2Â÷: LLM ÀçÆÇÁ¤
- Azure OpenAI·Î `urgent`, `confidence`, `reason` JSON ÆÇÁ¤.
- `confidence >= GMAIL_URGENT_LLM_CONFIDENCE` ÀÏ ¶§¸¸ ÃÖÁ¾ ±ä±ŞÀ¸·Î Åë°ú.

### ½Å±Ô/Ãß°¡ env
- `GMAIL_URGENT_USE_LLM` (default: true)
- `GMAIL_URGENT_REQUIRE_LLM` (default: false)
- `GMAIL_URGENT_LLM_MODEL` (default: `AZURE_OPENAI_DEPLOYMENT_NAME` ¶Ç´Â `gpt-4o-mini`)
- `GMAIL_URGENT_LLM_CONFIDENCE` (default: 0.55)

### µ¿ÀÛ ¸Ş¸ğ
- LLMÀÌ ºÒ°¡ÇÒ ¶§:
  - `GMAIL_URGENT_REQUIRE_LLM=false`¸é Å°¿öµå ±â¹İ fallback Çã¿ë
  - `GMAIL_URGENT_REQUIRE_LLM=true`¸é ¾Ë¸² Â÷´Ü
- Ãß°¡ ¼öÁ¤: Gmail ±ä±Ş ºĞ·ù ±âº» ¸ğµå¸¦ `llm_only`·Î ÀüÈ¯Çß½À´Ï´Ù. (`GMAIL_URGENT_CLASSIFY_MODE`)
- Ãß°¡ ¼öÁ¤: `GMAIL_URGENT_REQUIRE_LLM` ±âº»°ªÀ» true·Î ¹Ù²ã LLM ÆÇÁ¤ ½ÇÆĞ ½Ã ¾Ë¸²À» ¸·µµ·Ï Çß½À´Ï´Ù.
- Ãß°¡ ¼öÁ¤: Gmail ¾Ë¸² ·çÇÁ°¡ ¿¬°á Á÷ÈÄ Ã¹ Á¶È¸¸¦ ¹Ù·Î ¼öÇàÇÏµµ·Ï º¯°æÇß½À´Ï´Ù. (±âÁ¸ Ã¹ 60ÃÊ ´ë±â Á¦°Å)
- Ãß°¡ ¼öÁ¤: ÁÖ±â Á¶È¸¸¶´Ù µğ¹ö±× ·Î±×(`[GmailAlert] polled: no urgent unread mail`)¸¦ Ãâ·ÂÇØ µ¿ÀÛ ¿©ºÎ È®ÀÎ °¡´É.

## 2026-02-15 - Gmail ¾Ë¸² ½ÃÁ¡ ·ÎÁ÷ °³¼± (ÀÌÀü Á¾·á~ÇöÀç Á¢¼Ó + Á¢¼ÓÁß ½Ç½Ã°£)
- ¼öÁ¤ ÆÄÀÏ: `backend/modules/gmail_alert_module.py`, `backend/server.py`
- ¸ñÀû: ¿äÃ»»çÇ× ¹İ¿µ
  - Á¢¼Ó ½Ã: ÀÌÀü ¸¶Áö¸· Á¾·á ½Ã°¢ ~ ÇöÀç Á¢¼Ó ½Ã°¢ »çÀÌ ¸ŞÀÏ Áß ±ä±Ş°Ç¸¸ ¾È³»
  - Á¢¼Ó Áß: »õ·Î µé¾î¿Â ¸ŞÀÏ¸¸ ½Ç½Ã°£ È®ÀÎ, ±ä±Ş°Ç¸¸ ¾È³»

### ±¸Çö »ó¼¼
1. ¼¼¼Ç »óÅÂ ÀúÀå Ãß°¡ (`gmail_alert_state.json`)
- `last_disconnect_by_user`: »ç¿ëÀÚº° ¸¶Áö¸· Á¾·á½Ã°¢ ÀúÀå
- `delivered_ids`: ÀÌ¹Ì ¾È³»ÇÑ ¸ŞÀÏ ID ÀúÀå(Áßº¹ ¹æÁö)

2. ¸ğµâ API Ãß°¡
- `begin_session(user_id, connected_at_ts)`
  - ÀÌÀü Á¾·á½Ã°¢ºÎÅÍ ÇöÀç Á¢¼Ó½Ã°¢±îÁö ¹é·Î±× ½ºÄµ ÈÄ ±ä±Ş°Ç ¹İÈ¯
- `poll_live_alerts(user_id)`
  - Á¢¼Ó Áß ¸¶Áö¸· Æú¸µ ÀÌÈÄ~ÇöÀç ½Ã°¢ »çÀÌ ½Å±Ô ¸ŞÀÏ¸¸ ½ºÄµ
- `end_session(user_id, disconnected_at_ts)`
  - Á¾·á ½Ã°¢ ÀúÀå

3. ¼­¹ö ¿¬µ¿
- ¿¬°á ÈÄ `gmail_alert_loop` ½ÃÀÛ ½Ã `begin_session` 1È¸ ¼öÇà
- ·çÇÁ ³»¿¡¼­´Â `poll_live_alerts` ÁÖ±â È£Ãâ
- websocket Á¾·á finally¿¡¼­ `end_session` È£Ãâ

4. ºĞ·ù ¸ğµå
- `GMAIL_URGENT_CLASSIFY_MODE=llm_only`(±âº») ¶Ç´Â `hybrid`
- ÇöÀç ±âº»Àº llm-only·Î µ¿ÀÛ
- Ãß°¡ ¼öÁ¤: Gmail ¾Ë¸² µğ¹ö±× ·Î±×(`GMAIL_ALERT_DEBUG`)¸¦ Ãß°¡ÇØ, Æú¸µ/ºĞ·ù/½ºÅµ »çÀ¯¸¦ ·Î±×¿¡¼­ Áï½Ã È®ÀÎÇÒ ¼ö ÀÖ°Ô Çß½À´Ï´Ù.
- Ãß°¡ ¼öÁ¤: Gmail ·çÇÁ ½ÃÀÛ ·Î±×¿¡ »ç¿ëÀÚ ½Äº°(`user_id`)¸¦ Æ÷ÇÔÇß½À´Ï´Ù.
- Ãß°¡ º¯°æ: Á¢¼Ó Áß Gmail ¾Ë¸²À» ÁÖ±â Æú¸µ ±â¹İ¿¡¼­ IMAP IDLE ÀÌº¥Æ® ´ë±â ±â¹İÀ¸·Î ÀüÈ¯Çß½À´Ï´Ù.
- µ¿ÀÛ: `wait_next_live_alert(user_id, idle_timeout)`°¡ »õ ¸ŞÀÏ EXISTS ÀÌº¥Æ®¸¦ ±â´Ù¸° µÚ ÇØ´ç ½Ã°£Ã¢ ¸ŞÀÏ¸¸ ±ä±Ş ÆÇÁ¤.
- Á¢¼Ó ½Ã ¹é·Î±× 1È¸ È®ÀÎ(`begin_session`)Àº À¯Áö.
- ½Å±Ô env: `GMAIL_IDLE_TIMEOUT_SEC` (±âº» 120ÃÊ)
- Ãß°¡ ¼öÁ¤: IMAP IDLE µµÂø ½ÅÈ£ ´©¶ô ´ëºñ·Î Á¢¼Ó Áß `poll_live_alerts` fallback °æ·Î¸¦ Ãß°¡Çß½À´Ï´Ù.
- Ãß°¡ ¼öÁ¤: Á¢¼Ó ½Ã ¹é·Î±× È®ÀÎ¿¡¼­ °á°ú°¡ ¾øÀ» °æ¿ì `UNSEEN` ¸ŞÀÏ ÃÖ½Å ½ºÄµ º¸Á¶ °æ·Î¸¦ Ãß°¡Çß½À´Ï´Ù.
- ½Å±Ô env: `GMAIL_LIVE_POLL_FALLBACK_SEC` (±âº» 20ÃÊ)
- Ãß°¡ ¼öÁ¤: Gmail ÇÁ·Î¾×Æ¼ºê ¾Ë¸²À» ¶óÀÌºêÄÁÅØ½ºÆ® ÁÖÀÔ ¹æ½Ä¿¡¼­ `Á÷Á¢ user turn Àü¼Û` ¹æ½ÄÀ¸·Î º¯°æÇØ ½ÇÁ¦ À½¼º ÀÀ´ä Æ®¸®°Å¸¦ °­È­Çß½À´Ï´Ù.
- Ãß°¡ ¼öÁ¤: IDLE ´ë±â ±¸°£¿¡ ÇÏµå Å¸ÀÓ¾Æ¿ô(`asyncio.wait_for`)À» Ãß°¡ÇØ ºí·ÎÅ· ½Ã fallback poll·Î ³Ñ¾î°¡µµ·Ï º¸°­Çß½À´Ï´Ù.
- Ãß°¡ ·Î±×: ¹é·Î±× ±ä±Ş °¨Áö °Ç¼ö(`backlog urgent detected: N`) Ãâ·Â.
- Ãß°¡ °³¼±: Gmail ±ä±Ş ÆÇÁ¤ LLM ÀÀ´ä¿¡¼­ `tone`(urgent/celebratory/empathetic/neutral), `style`¸¦ ÇÔ²² ¹Ş¾Æ ¾Ë¸² ¹ßÈ­ ÅæÀ» µ¿ÀûÀ¸·Î ¹İ¿µÇÏµµ·Ï º¯°æ.
- ¼­¹ö ÇÁ·Î¾×Æ¼ºê ¹ßÈ­ ÇÔ¼ö `_send_proactive_announcement`¿¡ tone/style ÀÎÀÚ¸¦ Ãß°¡ÇÏ°í Åæº° °¡ÀÌµå ¹®±¸¸¦ Àû¿ë.
- ¹é·Î±× ¾Ë¸²Àº ¿©·¯ °ÇÀ» ÇÕÃÄ ÀĞÁö ¾Ê°í, ¸ŞÀÏº° toneÀ» º¸Á¸ÇØ ÃÖ´ë 2°Ç °³º° ¾È³»ÇÏµµ·Ï º¯°æ.
- Ãß°¡ ¼öÁ¤: ÇÁ·Î¾×Æ¼ºê ¸ŞÀÏ ¾Ë¸² Àü/ÈÄ `response_guard` ¹× `transit_turn_gate`¸¦ °­Á¦ ÃÊ±âÈ­ÇÏ´Â `_reset_response_gate()`¸¦ Ãß°¡Çß½À´Ï´Ù.
- ¸ñÀû: ¸ŞÀÏ ¾Ë¸² ÈÄ ÈÄ¼Ó »ç¿ëÀÚ ¹ßÈ­°¡ ¸·È÷´Â(¹«ÀÀ´ä) »óÅÂ¸¦ ¹æÁö.

## 2026-02-15 - Á¤¸® ºê·£Ä¡ 1Â÷ Å¬¸°¾÷ (¹Ì»ç¿ë ÆÄÀÏ Á¦°Å)
- ºê·£Ä¡: `mun-cleanup-server`
- ¸ñÀû: main º´ÇÕ ½Ã Ãæµ¹/È¥¼± ÃÖ¼ÒÈ­¸¦ À§ÇØ ÇöÀç ½ÇÇà °æ·Î¿¡¼­ ¹Ì»ç¿ë ÆÄÀÏ Á¦°Å.

### Á¦°Å ÆÄÀÏ
- `backend/aira_main_updated.py` (½ÇÇè¿ë ´ëÃ¼ ¿£Æ®¸®, ÇöÀç run °æ·Î ¹Ì»ç¿ë)
- `backend/module_manager.py` (´º½º ½ÇÇè °æ·Î¿ë, ÇöÀç ¼­¹ö ·±Å¸ÀÓ ¹Ì»ç¿ë)
- `test_news_agent.py` (·ÎÄÃ Å×½ºÆ® ½ºÅ©¸³Æ®, ¹èÆ÷ °æ·Î ¹Ì»ç¿ë)
- `works_aira.txt` (ÀÛ¾÷ ¸Ş¸ğ ÆÄÀÏ)

### ¿µÇâ
- `start_services.bat -> backend/run_server.py -> backend/server.py` ½ÇÇà °æ·Î¿¡´Â ¿µÇâ ¾øÀ½.

## 2026-02-15 - server.py Á¤¸® 2Â÷ (IntentRouter ¸ğµâ ºĞ¸®)
- ºê·£Ä¡: `mun-cleanup-server`
- ¸ñÀû: `server.py` Ãæµ¹ ÁöÁ¡À» ÁÙÀÌ±â À§ÇØ ÀÇµµ ¶ó¿ìÆÃ Å¬·¡½º¸¦ `modules`·Î ºĞ¸®.

### º¯°æ ³»¿ë
- Ãß°¡: `backend/modules/intent_router.py`
  - `IntentRouter` Å¬·¡½º ÀÌµ¿
  - Azure OpenAI ÃÊ±âÈ­/LLM ¶ó¿ìÆÃ/fallback ·ÎÁ÷ Æ÷ÇÔ
  - destination ÃßÃâ ÇÔ¼ö´Â Äİ¹é ÁÖÀÔ ¹æ½ÄÀ¸·Î ÀÇÁ¸¼º ºĞ¸®

- ¼öÁ¤: `backend/server.py`
  - ÀÎ¶óÀÎ `IntentRouter` Å¬·¡½º »èÁ¦
  - `from modules.intent_router import IntentRouter`·Î ±³Ã¼
  - `_extract_destination_from_text` Á¤ÀÇ ÀÌÈÄ `intent_router` ÀÎ½ºÅÏ½º »ı¼ºÇÏµµ·Ï º¯°æ
  - ºÒÇÊ¿äÇØÁø `AzureOpenAI` Á÷Á¢ import Á¦°Å

### ¿µÇâ
- ±â´É µ¿ÀÛÀº µ¿ÀÏ À¯Áö
- `server.py` »ó´Ü ´ëÇü Å¬·¡½º ºí·Ï Á¦°Å·Î Ãæµ¹¸éÀû Ãà¼Ò

## 2026-02-15 - server.py cleanup step 3 (SeoulLiveService module split)
- branch: `mun-cleanup-server`
- purpose: reduce `server.py` merge conflict surface by moving intent-specific live context composition into modules.

### changes
- added: `backend/modules/seoul_live_service.py`
  - added `SeoulLiveService` class.
  - handles intent-specific execution for `news`, `weather`, `air_quality`, and transit intents.
  - uses callback injection for dependencies from `server.py`.
- updated: `backend/server.py`
  - added `from modules.seoul_live_service import SeoulLiveService`
  - initialized `seoul_live_service = SeoulLiveService(...)` after live summary helpers are defined.
  - replaced `_execute_tools_for_intent` body with delegation to module method.
  - removed duplicated inline branching logic from `server.py`.

### impact
- runtime behavior remains equivalent (routing path refactored only).
- large intent branching block removed from `server.py`, reducing future merge conflicts.

## 2026-02-15 - server.py cleanup step 4 (Gmail alert loop module split)
- branch: `mun-cleanup-server`
- purpose: remove long async Gmail alert loop block from `server.py` and reduce merge conflict surface.

### changes
- added: `backend/modules/gmail_alert_runner.py`
  - added `run_gmail_alert_loop(...)` async runner.
  - includes backlog check, live IDLE wait, fallback polling, urgency delivery trigger, and user-turn interruption guards.
- updated: `backend/server.py`
  - added `from modules.gmail_alert_runner import run_gmail_alert_loop`
  - removed inline `gmail_alert_loop` definition.
  - task creation now calls `run_gmail_alert_loop(...)` with injected dependencies.

### impact
- behavior preserved; orchestration moved to module.
- `server.py` websocket section became shorter and easier to diff/merge.

## 2026-02-15 - server.py cleanup step 5 (Vision service module split)
- branch: `mun-cleanup-server`
- purpose: reduce websocket/vision branching size in `server.py` by moving camera state and frame handling into a module.

### changes
- added: `backend/modules/vision_service.py`
  - added `VisionService` class.
  - owns camera state (`enabled`, frame counters, latest snapshot, timestamps).
  - handles:
    - camera on/off transitions,
    - base64 frame decode + realtime Gemini frame send,
    - snapshot decode/storage + optional send,
    - recent snapshot retrieval for vision-related user turns.
- updated: `backend/server.py`
  - added `from modules.vision_service import VisionService`
  - replaced inline `camera_state` dict with `vision_service` instance.
  - removed inline `_send_camera_frame_to_gemini` function.
  - replaced camera payload branches with module calls:
    - `set_camera_enabled`
    - `handle_camera_frame_payload`
    - `handle_camera_snapshot_payload`
  - user STT vision hint path now uses `get_recent_snapshot_for_query(...)`.

### impact
- behavior preserved; logic moved to module.
- `server.py` websocket receive block is shorter and easier to merge.
