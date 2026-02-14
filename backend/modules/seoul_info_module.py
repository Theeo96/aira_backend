from __future__ import annotations

import re
from typing import Any


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _to_str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _to_float_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _to_int_or_none(value: Any) -> int | None:
    number = _to_float_or_none(value)
    if number is None:
        return None
    return int(number)


def round_eta_minutes(total_seconds: int) -> int:
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return minutes + 1 if seconds >= 30 else minutes


def parse_eta_minutes_from_message(message: str) -> int | None:
    text = str(message or "")
    match = re.search(r"(\d+)\s*분(?:\s*(\d+)\s*초)?", text)
    if match:
        minutes = int(match.group(1) or 0)
        seconds = int(match.group(2) or 0)
        return round_eta_minutes(minutes * 60 + seconds)

    if re.search(r"전역\s*도착", text):
        return 1
    if re.search(r"진입|도착", text):
        return 0
    return None


def resolve_eta_minutes(seconds: Any, message: Any) -> dict[str, Any]:
    raw_seconds = _to_int_or_none(seconds)
    msg = str(message or "")

    if raw_seconds is not None and raw_seconds > 0:
        minutes = round_eta_minutes(raw_seconds)
        return {"minutes": minutes, "text": f"약 {minutes}분", "rawSeconds": raw_seconds}

    from_message = parse_eta_minutes_from_message(msg)
    if from_message is not None:
        return {"minutes": from_message, "text": f"약 {from_message}분", "rawSeconds": raw_seconds}

    return {"minutes": None, "text": "도착예정시간 정보 없음", "rawSeconds": raw_seconds}


def _parse_culture(input_value: Any) -> dict[str, Any] | None:
    row = _as_dict(input_value)
    area = _to_str_or_none(row.get("area"))
    if not area:
        return None

    news_preview: list[dict[str, str]] = []
    for item in _as_list(row.get("culture_news_preview")):
        data = _as_dict(item)
        news_preview.append(
            {
                "title": str(data.get("title", "-")),
                "date": str(data.get("date", "-")),
            }
        )

    return {
        "area": area,
        "eventCount": _to_int_or_none(row.get("event_count")) or 0,
        "eventPreview": [str(v) for v in _as_list(row.get("event_preview"))],
        "cultureNewsCount": _to_int_or_none(row.get("culture_news_count")) or 0,
        "cultureNewsPreview": news_preview,
    }


def _parse_train(input_value: Any) -> dict[str, Any] | None:
    row = _as_dict(input_value)
    if not row:
        return None

    line = str(row.get("trainLineNm", row.get("line", "-")))
    message = str(row.get("arvlMsg2", row.get("arrivalMessage", "-")))
    seconds = row.get("barvlDt", row.get("arrivalSeconds"))
    eta = resolve_eta_minutes(seconds=seconds, message=message)

    return {
        "line": line,
        "message": message,
        "etaMinutes": eta["minutes"],
        "etaMinutesText": eta["text"],
        "rawSeconds": eta["rawSeconds"],
    }


def _voice_context(voice_payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    voice = _as_dict(voice_payload)
    return {
        "voice": voice,
        "observations": _as_dict(voice.get("observations")),
        "culture": _as_dict(voice.get("culture")),
        "news": _as_dict(voice.get("news")),
        "resolvedArea": _as_dict(voice.get("resolved_area")),
    }


def build_place_info(voice_payload: dict[str, Any] | None) -> dict[str, Any]:
    ctx = _voice_context(voice_payload)
    observations = ctx["observations"]
    resolved_area = ctx["resolvedArea"]
    return {
        "originArea": _to_str_or_none(resolved_area.get("areaName")),
        "destinationArea": _to_str_or_none(observations.get("destination_area")),
        "destinationStation": _to_str_or_none(observations.get("destination_station")),
    }


def build_transit_info(
    voice_payload: dict[str, Any] | None,
    odsay_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ctx = _voice_context(voice_payload)
    observations = ctx["observations"]
    odsay = _as_dict(odsay_payload)
    fastest_path = _as_dict(odsay.get("fastestPath"))
    walk = _as_dict(odsay.get("walkToDepartureStation"))
    walk_exact = walk.get("exactFromCurrentOnly")

    return {
        "fastest": _parse_train(observations.get("subway_fastest")),
        "next": _parse_train(observations.get("subway_next")),
        "totalTimeMinutes": _to_int_or_none(fastest_path.get("totalTimeMinutes")),
        "transferCount": _to_int_or_none(fastest_path.get("transferCount")),
        "walkToDepartureMinutes": _to_int_or_none(walk.get("minutes")),
        "walkExact": walk_exact if isinstance(walk_exact, bool) else None,
    }


def build_environment_info(voice_payload: dict[str, Any] | None) -> dict[str, Any]:
    observations = _voice_context(voice_payload)["observations"]
    return {
        "congestion": _to_str_or_none(observations.get("area_congestion")),
        "weatherTemp": _to_float_or_none(observations.get("weather_temp")),
        "bikeParkingTotal": _to_int_or_none(observations.get("bike_parking_total")),
        "bikeRackTotal": _to_int_or_none(observations.get("bike_rack_total")),
        "bikeOccupancyPct": _to_float_or_none(observations.get("bike_occupancy_pct")),
    }


def build_culture_info(voice_payload: dict[str, Any] | None) -> dict[str, Any]:
    ctx = _voice_context(voice_payload)
    observations = ctx["observations"]
    culture = ctx["culture"]
    return {
        "aroundOrigin": _parse_culture(culture.get("around_origin", observations.get("origin_culture"))),
        "aroundDestination": _parse_culture(
            culture.get("around_destination", observations.get("destination_culture"))
        ),
    }


def build_news_info(voice_payload: dict[str, Any] | None) -> dict[str, Any]:
    news = _voice_context(voice_payload)["news"]
    latest: list[dict[str, str]] = []
    for row in _as_list(news.get("items"))[:2]:
        item = _as_dict(row)
        latest.append(
            {
                "title": str(item.get("title", "")),
                "date": str(item.get("pubDate", "")),
                "link": str(item.get("originallink", item.get("link", ""))),
            }
        )
    return {"latest": latest}


def build_speech_info(voice_payload: dict[str, Any] | None) -> dict[str, str]:
    voice = _voice_context(voice_payload)["voice"]
    return {
        "summary": _to_str_or_none(voice.get("speak_text")) or "요약 정보가 없습니다.",
        "followUp": _to_str_or_none(voice.get("follow_up_question"))
        or "원하시는 조건으로 다시 안내할까요?",
    }


def build_seoul_info_packet(
    voice_payload: dict[str, Any] | None,
    odsay_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    voice = _as_dict(voice_payload)
    odsay = _as_dict(odsay_payload)
    return {
        "meta": {
            "source": {
                "voiceAssistant": bool(voice),
                "odsayFastest": bool(odsay),
            }
        },
        "place": build_place_info(voice_payload),
        "transit": build_transit_info(voice_payload, odsay_payload),
        "environment": build_environment_info(voice_payload),
        "culture": build_culture_info(voice_payload),
        "news": build_news_info(voice_payload),
        "speech": build_speech_info(voice_payload),
    }


def build_speech_summary(packet: dict[str, Any]) -> str:
    parts: list[str] = []
    place = _as_dict(packet.get("place"))
    environment = _as_dict(packet.get("environment"))
    transit = _as_dict(packet.get("transit"))
    culture = _as_dict(packet.get("culture"))

    origin_area = _to_str_or_none(place.get("originArea"))
    if origin_area:
        parts.append(f"현재 기준 지역은 {origin_area}입니다.")

    congestion = _to_str_or_none(environment.get("congestion"))
    if congestion:
        parts.append(f"혼잡도는 {congestion}입니다.")

    fastest = _as_dict(transit.get("fastest"))
    if fastest:
        parts.append(
            f"가장 빠른 열차는 {fastest.get('line', '-')}"
            f" {fastest.get('message', '-')}, {fastest.get('etaMinutesText', '도착예정시간 정보 없음')}입니다."
        )

    nxt = _as_dict(transit.get("next"))
    if nxt:
        parts.append(f"다음 열차는 {nxt.get('etaMinutesText', '도착예정시간 정보 없음')}입니다.")

    total_minutes = _to_int_or_none(transit.get("totalTimeMinutes"))
    if total_minutes is not None:
        parts.append(f"최단 경로 총 소요시간은 {total_minutes}분입니다.")

    walk_minutes = _to_int_or_none(transit.get("walkToDepartureMinutes"))
    if walk_minutes is not None:
        parts.append(f"출발역까지 도보 {walk_minutes}분입니다.")

    around_destination = _as_dict(culture.get("aroundDestination"))
    event_count = _to_int_or_none(around_destination.get("eventCount"))
    if event_count is not None and event_count > 0:
        parts.append(f"도착지 주변 문화 이벤트는 {event_count}건입니다.")

    return " ".join(parts)
