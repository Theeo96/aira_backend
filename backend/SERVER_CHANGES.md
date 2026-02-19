# Server Change Log

## 2026-02-19

### File: `backend/server.py`
- Added `_is_vision_followup_utterance(...)`.
  - Purpose: when camera/screen share is ON, short follow-up utterances are treated as vision turns.
- Added `_send_user_text_with_snapshot_turn(...)`.
  - Sends user text + current snapshot in the same Gemini turn (`inline_data`).
  - Purpose: prevent vision questions from falling back to memory-only responses.
- Updated `on_recognized(...)` vision routing:
  - If camera ON + (explicit vision or inferred follow-up) + recent snapshot, route directly to vision turn and return.
  - Purpose: bypass generic intent path for visual Q&A and keep answers grounded to current frame.

### File: `backend/modules/vision_service.py`
- Added `get_recent_snapshot(max_age_sec=None)`.
  - Purpose: retrieve freshest snapshot independently of keyword matching for follow-up visual questions.
- Updated `send_frame_to_gemini(...)`:
  - Every incoming frame now refreshes `latest_snapshot`/`snapshot_ts` before rate-limit check.
  - Purpose: ensure query-time snapshot turn uses newest scene instead of stale cached image.
- Updated `set_camera_enabled(...)`:
  - On camera ON/OFF transition, reset `latest_snapshot`, `snapshot_ts`, `last_frame_ts`, counters.
  - Purpose: prevent old-scene reuse across camera sessions.

### File: `backend/server.py`
- Updated vision snapshot age threshold in `on_recognized(...)`: `4.0s -> 12.0s`.
  - Purpose: reduce false misses where valid recent snapshot exists but strict TTL blocks vision turn.

### Validation
- `python -m py_compile backend/server.py backend/modules/vision_service.py` passed.
