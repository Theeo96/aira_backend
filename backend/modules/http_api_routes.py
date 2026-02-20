from __future__ import annotations

import asyncio
from typing import Any, Callable

from fastapi import APIRouter, Body, Query


def create_api_router(
    build_live_seoul_summary: Callable[..., dict],
    to_float: Callable[[Any], float | None],
    morning_briefing: Any,
    build_seoul_info_packet: Callable[[Any, Any], dict],
    build_speech_summary: Callable[[dict], str],
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/seoul-info/normalize")
    async def normalize_seoul_info(payload: dict = Body(...)):
        voice_payload = payload.get("voicePayload")
        odsay_payload = payload.get("odsayPayload")
        packet = build_seoul_info_packet(voice_payload, odsay_payload)
        speech_summary = build_speech_summary(packet)
        return {"packet": packet, "speechSummary": speech_summary}

    @router.get("/api/seoul-info/live")
    async def get_live_seoul_info(
        lat: float | None = Query(default=None),
        lng: float | None = Query(default=None),
        station: str | None = Query(default=None),
        destination: str | None = Query(default=None),
    ):
        return build_live_seoul_summary(
            lat=lat,
            lng=lng,
            station_name=station,
            destination_name=destination,
        )

    @router.get("/api/briefing/wake-up")
    async def get_wake_up_briefing():
        if morning_briefing is None:
            return {"ok": False, "error": "morning briefing module unavailable"}
        if not morning_briefing.is_briefing_api_enabled():
            return {"ok": False, "error": "briefing api disabled"}
        if not morning_briefing.is_wake_up_enabled():
            return {"ok": False, "error": "wake-up briefing disabled"}
        return await asyncio.to_thread(morning_briefing.build_wake_up_briefing)

    @router.post("/api/briefing/leaving-home")
    async def get_leaving_home_alert(payload: dict = Body(...)):
        if morning_briefing is None:
            return {"ok": False, "error": "morning briefing module unavailable"}
        if not morning_briefing.is_briefing_api_enabled():
            return {"ok": False, "error": "briefing api disabled"}
        if not morning_briefing.is_leaving_home_enabled():
            return {"ok": False, "error": "leaving-home briefing disabled"}
        current_gps = payload.get("current_gps") if isinstance(payload, dict) else None
        if not isinstance(current_gps, dict):
            lat = to_float(payload.get("lat")) if isinstance(payload, dict) else None
            lng = to_float(payload.get("lng")) if isinstance(payload, dict) else None
            if lat is not None and lng is not None:
                current_gps = {"lat": lat, "lng": lng}
        selected_transport = payload.get("selected_transport") if isinstance(payload, dict) else None
        return await asyncio.to_thread(morning_briefing.build_leaving_home_alert, current_gps, selected_transport)

    @router.post("/api/briefing/leaving-office")
    async def get_leaving_office_alert(payload: dict = Body(...)):
        if morning_briefing is None:
            return {"ok": False, "error": "morning briefing module unavailable"}
        if not morning_briefing.is_briefing_api_enabled():
            return {"ok": False, "error": "briefing api disabled"}
        if not morning_briefing.is_leaving_office_enabled():
            return {"ok": False, "error": "leaving-office briefing disabled"}
        current_gps = payload.get("current_gps") if isinstance(payload, dict) else None
        if not isinstance(current_gps, dict):
            lat = to_float(payload.get("lat")) if isinstance(payload, dict) else None
            lng = to_float(payload.get("lng")) if isinstance(payload, dict) else None
            if lat is not None and lng is not None:
                current_gps = {"lat": lat, "lng": lng}
        moved_m = to_float(payload.get("moved_m")) if isinstance(payload, dict) else None
        selected_transport = payload.get("selected_transport") if isinstance(payload, dict) else None
        return await asyncio.to_thread(
            morning_briefing.build_evening_local_alert,
            current_gps,
            moved_m,
            selected_transport,
        )

    return router
