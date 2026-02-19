import base64
import time
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
        }

    async def send_frame_to_gemini(
        self,
        session_ref: dict,
        inject_live_context_now,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
    ):
        if not image_bytes:
            return
        now_ts = time.monotonic()
        # Keep latest frame snapshot synced so query-time snapshot turn uses the newest view.
        self.camera_state["latest_snapshot"] = bytes(image_bytes)
        self.camera_state["snapshot_ts"] = now_ts
        if now_ts - float(self.camera_state.get("last_frame_ts") or 0.0) < self.min_interval_sec:
            return
        session_obj = session_ref.get("obj")
        if not session_obj:
            return
        try:
            await session_obj.send_realtime_input(media={"data": image_bytes, "mime_type": mime_type})
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
        self.log(f"[Vision] Camera state changed: enabled={camera_on}")
        if camera_on:
            await inject_live_context_now(
                "[VISION] Camera has been turned on. Wait for incoming frame context and use it with voice.",
                complete_turn=False,
            )

    async def handle_camera_frame_payload(self, payload: dict, session_ref: dict, inject_live_context_now):
        if not self.camera_state.get("enabled"):
            return
        b64 = payload.get("data")
        mime_type = str(payload.get("mime_type") or "image/jpeg")
        if isinstance(b64, str) and b64:
            try:
                image_bytes = base64.b64decode(b64)
                await self.send_frame_to_gemini(
                    session_ref=session_ref,
                    inject_live_context_now=inject_live_context_now,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                )
            except Exception as e:
                self.log(f"[Vision] camera frame decode failed: {e}")

    async def handle_camera_snapshot_payload(self, payload: dict, session_ref: dict, inject_live_context_now):
        if not self.camera_state.get("enabled"):
            return
        b64 = payload.get("data")
        if isinstance(b64, str) and b64:
            try:
                image_bytes = base64.b64decode(b64)
                self.camera_state["latest_snapshot"] = image_bytes
                self.camera_state["snapshot_ts"] = time.monotonic()
                self.camera_state["snapshot_updates"] = int(self.camera_state.get("snapshot_updates") or 0) + 1
                updates = int(self.camera_state["snapshot_updates"])
                if updates == 1 or updates % 20 == 0:
                    self.log(f"[Vision] snapshot updated x{updates}")
                await self.send_frame_to_gemini(
                    session_ref=session_ref,
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
