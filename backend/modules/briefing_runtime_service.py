from __future__ import annotations

import asyncio
import re
import time
from datetime import datetime
from typing import Any, Awaitable, Callable
from zoneinfo import ZoneInfo


KST = ZoneInfo("Asia/Seoul")


class BriefingRuntimeService:
    def __init__(
        self,
        morning_briefing: Any,
        send_proactive_announcement: Callable[..., Awaitable[None]],
        runtime_env_bool: Callable[..., bool],
        runtime_env_path: str,
        briefing_pre_ad_copy: str,
        log=print,
    ):
        self.morning_briefing = morning_briefing
        self.send_proactive_announcement = send_proactive_announcement
        self.runtime_env_bool = runtime_env_bool
        self.runtime_env_path = runtime_env_path
        self.briefing_pre_ad_copy = str(briefing_pre_ad_copy or "")
        self.log = log

    def build_initial_state(self, default_transport_mode: str = "public") -> dict[str, Any]:
        return {
            "wake_sent_date": "",
            "test_wake_sent": False,
            "leave_home_sent_date": "",
            "leave_office_sent_date": "",
            "last_leave_home_check_ts": 0.0,
            "last_leave_office_check_ts": 0.0,
            "awaiting_transport_choice": False,
            "selected_transport": str(default_transport_mode or "public"),
            "transport_choice_date": "",
        }

    def get_default_transport_mode(self) -> str:
        if self.morning_briefing is None:
            return "public"
        try:
            return str(self.morning_briefing.get_default_transport_mode() or "public")
        except Exception:
            return "public"

    def _today(self) -> str:
        return datetime.now(KST).strftime("%Y-%m-%d")

    def apply_transport_choice(self, briefing_state: dict[str, Any], user_text: str) -> dict[str, Any]:
        if self.morning_briefing is None:
            return {"handled": False}
        if not isinstance(briefing_state, dict) or not briefing_state.get("awaiting_transport_choice"):
            return {"handled": False}
        picked = self.morning_briefing.detect_transport_choice(user_text)
        if picked not in {"public", "car"}:
            return {"handled": False}
        briefing_state["selected_transport"] = picked
        briefing_state["awaiting_transport_choice"] = False
        briefing_state["transport_choice_date"] = self._today()
        compact_choice = re.sub(r"[\s\W_]+", "", str(user_text or ""))
        return {
            "handled": True,
            "picked": picked,
            "should_short_circuit": len(compact_choice) <= 12,
            "ack_text": (
                "오늘은 대중교통 기준으로 안내할게요."
                if picked == "public"
                else "오늘은 자가용 기준으로 안내할게요."
            ),
        }

    async def maybe_send_wake_up_briefing(self, briefing_state: dict[str, Any], force: bool = False):
        if self.morning_briefing is None:
            return
        if not self.morning_briefing.is_wake_up_enabled():
            return
        today = self._today()
        if (not force) and briefing_state.get("wake_sent_date") == today:
            return
        try:
            payload = await asyncio.to_thread(self.morning_briefing.build_wake_up_briefing)
        except Exception as e:
            self.log(f"[MorningBriefing] wake-up build failed: {e}")
            return
        if not isinstance(payload, dict) or not payload.get("ok"):
            return
        text = str(payload.get("briefing") or "").strip()
        if not text:
            return
        if self.runtime_env_bool(
            key="BRIEFING_AD_MODE",
            default=False,
            env_path=self.runtime_env_path,
        ):
            await self.send_proactive_announcement(
                summary_text=self.briefing_pre_ad_copy,
                tone="celebratory",
                style="전문 라디오 광고 성우 톤으로 또렷하고 리듬감 있게 말해 주세요.",
                add_followup_hint=False,
                max_chars=260,
                max_sentences=6,
                split_by_sentence=True,
                chunk_max_sentences=1,
                chunk_max_chars=95,
            )
        await self.send_proactive_announcement(
            summary_text=text,
            tone="neutral",
            add_followup_hint=False,
            max_chars=180,
            max_sentences=4,
            split_by_sentence=True,
            chunk_max_sentences=1,
            chunk_max_chars=110,
        )
        recommended = self.morning_briefing.normalize_transport_mode(payload.get("recommended_transport"))
        briefing_state["selected_transport"] = recommended
        awaiting_choice = bool(payload.get("ask_transport_choice", True))
        briefing_state["awaiting_transport_choice"] = awaiting_choice
        briefing_state["transport_choice_date"] = "" if awaiting_choice else today
        briefing_state["wake_sent_date"] = today

    async def maybe_send_leaving_home_alert(self, briefing_state: dict[str, Any], current_gps: dict):
        if self.morning_briefing is None or not isinstance(current_gps, dict):
            return
        if not self.morning_briefing.is_leaving_home_enabled():
            return
        now_mono = time.monotonic()
        last_ts = float(briefing_state.get("last_leave_home_check_ts") or 0.0)
        if (now_mono - last_ts) < 15.0:
            return
        briefing_state["last_leave_home_check_ts"] = now_mono
        today = self._today()
        if briefing_state.get("leave_home_sent_date") == today:
            return
        try:
            payload = await asyncio.to_thread(
                self.morning_briefing.build_leaving_home_alert,
                current_gps,
                briefing_state.get("selected_transport"),
            )
        except Exception as e:
            self.log(f"[MorningBriefing] leaving-home build failed: {e}")
            return
        if not isinstance(payload, dict) or (not payload.get("ok")):
            return
        if not bool(payload.get("triggered")):
            return
        text = str(payload.get("alert") or "").strip()
        if not text:
            return
        await self.send_proactive_announcement(
            summary_text=text,
            tone="neutral",
            add_followup_hint=False,
            max_chars=170,
            max_sentences=4,
            split_by_sentence=True,
            chunk_max_sentences=1,
            chunk_max_chars=110,
        )
        briefing_state["leave_home_sent_date"] = today
        briefing_state["awaiting_transport_choice"] = False

    async def maybe_send_evening_local_alert(
        self,
        briefing_state: dict[str, Any],
        current_gps: dict,
        moved_m: float | None = None,
    ):
        if self.morning_briefing is None or not isinstance(current_gps, dict):
            return
        if not self.morning_briefing.is_leaving_office_enabled():
            return
        now_mono = time.monotonic()
        last_ts = float(briefing_state.get("last_leave_office_check_ts") or 0.0)
        if (now_mono - last_ts) < 15.0:
            return
        briefing_state["last_leave_office_check_ts"] = now_mono
        today = self._today()
        if briefing_state.get("leave_office_sent_date") == today:
            return
        try:
            payload = await asyncio.to_thread(
                self.morning_briefing.build_evening_local_alert,
                current_gps,
                moved_m,
                briefing_state.get("selected_transport"),
            )
        except Exception as e:
            self.log(f"[MorningBriefing] evening-local build failed: {e}")
            return
        if not isinstance(payload, dict) or (not payload.get("ok")) or (not payload.get("triggered")):
            return
        text = str(payload.get("alert") or "").strip()
        if not text:
            return
        await self.send_proactive_announcement(
            summary_text=text,
            tone="neutral",
            add_followup_hint=False,
            max_chars=170,
            max_sentences=4,
            split_by_sentence=True,
            chunk_max_sentences=1,
            chunk_max_chars=110,
        )
        briefing_state["leave_office_sent_date"] = today

    async def scheduler_loop(self, briefing_state: dict[str, Any]):
        if self.morning_briefing is None:
            return
        while True:
            try:
                if not self.morning_briefing.is_wake_up_enabled():
                    briefing_state["test_wake_sent"] = False
                elif bool(self.morning_briefing.is_wake_up_test_mode()):
                    auto_wake_test = self.morning_briefing.should_auto_wake_up_in_test()
                    if auto_wake_test and (not bool(briefing_state.get("test_wake_sent"))):
                        await self.maybe_send_wake_up_briefing(briefing_state=briefing_state, force=True)
                        briefing_state["test_wake_sent"] = True
                    elif not auto_wake_test:
                        briefing_state["test_wake_sent"] = False
                else:
                    briefing_state["test_wake_sent"] = False
                    wake_time = str(self.morning_briefing.get_wake_up_time() or "07:00").strip()
                    try:
                        hh, mm = wake_time.split(":")
                        wake_hh = int(hh)
                        wake_mm = int(mm)
                    except Exception:
                        wake_hh, wake_mm = 7, 0
                    now = datetime.now(KST)
                    now_total_min = now.hour * 60 + now.minute
                    wake_total_min = wake_hh * 60 + wake_mm
                    delta_min = now_total_min - wake_total_min
                    if 0 <= delta_min <= 10:
                        await self.maybe_send_wake_up_briefing(briefing_state=briefing_state, force=False)
                await asyncio.sleep(20)
            except asyncio.CancelledError:
                return
            except Exception as e:
                self.log(f"[MorningBriefing] scheduler error: {e}")
