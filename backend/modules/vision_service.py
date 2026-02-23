import base64
import time
from collections import deque
from typing import Callable


class VisionService:
    def __init__(self, min_interval_sec: float, snapshot_ttl_sec: float, log: Callable[[str], None] = print):
        self.min_interval_sec = float(min_interval_sec)
        self.snapshot_ttl_sec = float(snapshot_ttl_sec)
        self.log = log
        self.camera_state = {
            "enabled": False,
            "last_frame_ts": 0.0,
            "frames_sent": 0,
            "latest_snapshot": None,
            "snapshot_ts": 0.0,
            "snapshot_updates": 0,
            "snapshot_buffer": deque(maxlen=40),
        }

    def _record_snapshot(self, image_bytes: bytes, ts: float | None = None):
        if not image_bytes:
            return
        now_ts = float(ts if ts is not None else time.monotonic())
        self.camera_state["latest_snapshot"] = bytes(image_bytes)
        self.camera_state["snapshot_ts"] = now_ts
        buf = self.camera_state.get("snapshot_buffer")
        if isinstance(buf, deque):
            buf.append({"ts": now_ts, "data": bytes(image_bytes)})

    async def send_frame_to_gemini(
        self,
        push_image_now: Callable[[bytes], Callable],
        inject_live_context_now,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
    ):
        if not image_bytes:
            return
        now_ts = time.monotonic()
        # Keep latest frame snapshot synced so query-time snapshot turn uses the newest view.
        self._record_snapshot(image_bytes=image_bytes, ts=now_ts)
        if now_ts - float(self.camera_state.get("last_frame_ts") or 0.0) < self.min_interval_sec:
            return
        if not push_image_now:
            return
        try:
            await push_image_now(image_bytes)
            self.camera_state["last_frame_ts"] = now_ts
            self.camera_state["frames_sent"] = int(self.camera_state.get("frames_sent") or 0) + 1
            frames = int(self.camera_state["frames_sent"])
            if frames == 1:
                await inject_live_context_now(
                    "[VISION] Camera is on and at least one live frame has been received. "
                    "You can answer questions about what is visible in the current scene.",
                    complete_turn=False,
                )
            if frames % 5 == 0:
                self.log(f"[Vision] camera frames sent to Gemini: {frames}")
        except Exception as e:
            self.log(f"[Vision] camera frame send failed: {e}")

    async def set_camera_enabled(self, enabled: bool, inject_live_context_now):
        camera_on = bool(enabled)
        self.camera_state["enabled"] = camera_on
        # Reset cached visual state on every camera mode transition to avoid stale-scene reuse.
        self.camera_state["frames_sent"] = 0
        self.camera_state["snapshot_updates"] = 0
        self.camera_state["latest_snapshot"] = None
        self.camera_state["snapshot_ts"] = 0.0
        self.camera_state["last_frame_ts"] = 0.0
        buf = self.camera_state.get("snapshot_buffer")
        if isinstance(buf, deque):
            buf.clear()
        self.log(f"[Vision] Camera state changed: enabled={camera_on}")
        if camera_on:
            await inject_live_context_now(
                "[VISION] Camera has been turned on. Wait for incoming frame context and use it with voice.",
                complete_turn=False,
            )

    async def handle_camera_frame_payload(self, payload: dict, push_image_now: Callable, inject_live_context_now):
        if not self.camera_state.get("enabled"):
            return
        b64 = payload.get("data")
        mime_type = str(payload.get("mime_type") or "image/jpeg")
        if isinstance(b64, str) and b64:
            try:
                image_bytes = base64.b64decode(b64)
                await self.send_frame_to_gemini(
                    push_image_now=push_image_now,
                    inject_live_context_now=inject_live_context_now,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                )
            except Exception as e:
                self.log(f"[Vision] camera frame decode failed: {e}")

    async def handle_camera_snapshot_payload(self, payload: dict, push_image_now: Callable, inject_live_context_now):
        if not self.camera_state.get("enabled"):
            return
        b64 = payload.get("data")
        if isinstance(b64, str) and b64:
            try:
                image_bytes = base64.b64decode(b64)
                self._record_snapshot(image_bytes=image_bytes, ts=time.monotonic())
                self.camera_state["snapshot_updates"] = int(self.camera_state.get("snapshot_updates") or 0) + 1
                updates = int(self.camera_state["snapshot_updates"])
                if updates == 1 or updates % 20 == 0:
                    self.log(f"[Vision] snapshot updated x{updates}")
                await self.send_frame_to_gemini(
                    push_image_now=push_image_now,
                    inject_live_context_now=inject_live_context_now,
                    image_bytes=image_bytes,
                    mime_type="image/jpeg",
                )
            except Exception as e:
                self.log(f"[Vision] snapshot decode failed: {e}")

    def get_recent_snapshot_for_query(self, text: str, is_vision_related_query: Callable[[str], bool]) -> bytes | None:
        if not is_vision_related_query(text):
            return None
        snapshot_bytes = self.camera_state.get("latest_snapshot")
        snapshot_ts = float(self.camera_state.get("snapshot_ts") or 0.0)
        if (
            isinstance(snapshot_bytes, (bytes, bytearray))
            and (time.monotonic() - snapshot_ts) <= self.snapshot_ttl_sec
        ):
            return bytes(snapshot_bytes)
        return None

    def get_recent_snapshot(self, max_age_sec: float | None = None) -> bytes | None:
        snapshot_bytes = self.camera_state.get("latest_snapshot")
        snapshot_ts = float(self.camera_state.get("snapshot_ts") or 0.0)
        ttl = float(max_age_sec) if max_age_sec is not None else float(self.snapshot_ttl_sec)
        if (
            isinstance(snapshot_bytes, (bytes, bytearray))
            and (time.monotonic() - snapshot_ts) <= ttl
        ):
            return bytes(snapshot_bytes)
        return None

    def get_snapshot_for_speech_window(
        self,
        utterance_start_ts: float,
        utterance_end_ts: float,
        pre_roll_sec: float = 2.0,
        max_age_sec: float = 12.0,
    ) -> bytes | None:
        start = max(0.0, float(utterance_start_ts or 0.0) - float(pre_roll_sec))
        end = float(utterance_end_ts or 0.0)
        now = time.monotonic()
        buf = self.camera_state.get("snapshot_buffer")
        if isinstance(buf, deque) and len(buf) > 0:
            picked = None
            for item in reversed(buf):
                ts = float(item.get("ts") or 0.0)
                data = item.get("data")
                if not isinstance(data, (bytes, bytearray)):
                    continue
                if ts < (now - float(max_age_sec)):
                    continue
                if start <= ts <= end:
                    picked = bytes(data)
                    break
            if picked is not None:
                return picked
        return self.get_recent_snapshot(max_age_sec=max_age_sec)
