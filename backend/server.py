import os
# Load env variables first
from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import math
import numpy as np
import re
import time
from fastapi import Body, FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from google import genai
import azure.cognitiveservices.speech as speechsdk
import sys
import urllib.parse
import urllib.request
import urllib.error
from openai import AzureOpenAI
from modules.cosmos_db import cosmos_service
from modules.memory import memory_service
from modules.seoul_info_module import build_seoul_info_packet, build_speech_summary

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("[Server] Starting up... (Lifespan Event)")
    yield
    # Shutdown logic
    print("[Server] Shutting down... (Lifespan Event)")

app = FastAPI(lifespan=lifespan)


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-native-audio-preview-12-2025"
GEMINI_DIRECT_AUDIO_INPUT = os.getenv("GEMINI_DIRECT_AUDIO_INPUT", "true").strip().lower() in {"1", "true", "yes", "on"}

# Azure Speech Config
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
SEOUL_API_KEY = os.getenv("SEOUL_API_KEY") or os.getenv("Seoul_API")
ODSAY_API_KEY = os.getenv("ODSAY_API_KEY")
HOME_LAT = os.getenv("HOME_LAT")
HOME_LNG = os.getenv("HOME_LNG")
COMMUTE_DEFAULT_DESTINATION = os.getenv("COMMUTE_DEFAULT_DESTINATION", "광화문")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
INTENT_ROUTER_MODEL = os.getenv("INTENT_ROUTER_MODEL") or AZURE_OPENAI_DEPLOYMENT_NAME or "gpt-4o-mini"
ENABLE_TRANSIT_FILLER = os.getenv("ENABLE_TRANSIT_FILLER", "false").strip().lower() in {"1", "true", "yes", "on"}
print(f"[Config] ENABLE_TRANSIT_FILLER={ENABLE_TRANSIT_FILLER}")
print(f"[Config] GEMINI_DIRECT_AUDIO_INPUT={GEMINI_DIRECT_AUDIO_INPUT}")


class IntentRouter:
    def __init__(self):
        self.client = None
        if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
            print("[IntentRouter] Azure OpenAI credentials missing. Fallback routing only.")
            return
        base_endpoint = AZURE_OPENAI_ENDPOINT
        if "/openai/v1" in base_endpoint:
            base_endpoint = base_endpoint.split("/openai/v1")[0]
        try:
            self.client = AzureOpenAI(
                api_key=AZURE_OPENAI_API_KEY,
                api_version=AZURE_OPENAI_API_VERSION,
                azure_endpoint=base_endpoint,
                timeout=4.0,
            )
            print("[IntentRouter] Azure OpenAI router initialized.")
        except Exception as e:
            print(f"[IntentRouter] init failed: {e}")
            self.client = None

    def _fallback(self, text: str):
        t = str(text or "")
        if any(k in t for k in ["지하철", "역", "방면", "열차", "몇 분"]):
            return {"intent": "subway_route", "destination": _extract_destination_from_text(t), "source": "fallback", "home_update": False}
        if any(k in t for k in ["버스", "정류장"]):
            return {"intent": "bus_route", "destination": _extract_destination_from_text(t), "source": "fallback", "home_update": False}
        if any(k in t for k in ["날씨", "비", "기온"]):
            return {"intent": "weather", "destination": _extract_destination_from_text(t), "source": "fallback", "home_update": False}
        if any(k in t for k in ["대기질", "미세먼지", "aqi"]):
            return {"intent": "air_quality", "destination": _extract_destination_from_text(t), "source": "fallback", "home_update": False}
        return {"intent": "commute_overview", "destination": _extract_destination_from_text(t), "source": "fallback", "home_update": False}

    def route(self, text: str):
        if not self.client:
            return self._fallback(text)
        system = (
            "Classify Korean commuter query intent. Return JSON only with keys: "
            "intent, destination, home_update. intent one of "
            "[subway_route,bus_route,weather,air_quality,commute_overview,general]. "
            "destination should be a concise place/station name or null. "
            "home_update must be true only when the user explicitly indicates home relocation/change "
            "(e.g., moved house, changed home location, says 'my home is now ...'). "
            "If user is just asking route to another place (friend's home, visit, outing), home_update must be false."
        )
        try:
            resp = self.client.chat.completions.create(
                model=INTENT_ROUTER_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": str(text or "")},
                ],
            )
            content = resp.choices[0].message.content
            data = json.loads(content) if content else {}
            intent = data.get("intent") if isinstance(data, dict) else None
            destination = data.get("destination") if isinstance(data, dict) else None
            home_update = bool(data.get("home_update")) if isinstance(data, dict) else False
            if intent not in {"subway_route", "bus_route", "weather", "air_quality", "commute_overview", "general"}:
                return self._fallback(text)
            return {"intent": intent, "destination": destination, "source": "llm", "home_update": home_update}
        except Exception as e:
            print(f"[IntentRouter] route failed: {e}")
            if "DeploymentNotFound" in str(e):
                print("[IntentRouter] Disabling Azure router due to missing deployment. Using fallback routing.")
                self.client = None
            return self._fallback(text)


intent_router = IntentRouter()


def _http_get_json(url: str, timeout: int = 6):
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            return json.loads(body)
    except Exception as e:
        print(f"[SeoulInfo] HTTP error: {e}")
        return None


def _to_float(value):
    try:
        return float(value)
    except Exception:
        return None


def _resolve_home_coords():
    lat = _to_float(HOME_LAT)
    lng = _to_float(HOME_LNG)
    if lat is None or lng is None:
        return None, None
    return lat, lng


def _extract_destination_from_text(text: str):
    s = str(text or "").strip()
    if not s:
        return None
    # Korean patterns: "...까지", "...으로/로", "...가려면", "...가는"
    patterns = [
        r"([가-힣A-Za-z0-9\s]{1,30})\s*까지",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*(?:으로|로)\s*가",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*가려면",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*가는",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*가는\s*길",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*가는길",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*(?:가는|갈|가능)\s*방법",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*에서\s*약속",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*쪽(?:으로)?",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*(?:에|에서)\s*가",
    ]
    for p in patterns:
        m = re.search(p, s)
        if m:
            cand = re.sub(r"\s+", " ", m.group(1)).strip()
            cand = re.sub(r"(쪽|근처|부근|방향)$", "", cand).strip()
            if cand and cand not in ("집", "회사", "학교", "거기", "여기"):
                return cand
    # "성수역으로", "강남으로" 같은 단문 보강
    m2 = re.search(r"([가-힣A-Za-z0-9]{2,20})(?:역)?\s*(?:으로|로)$", s)
    if m2:
        cand = m2.group(1).strip()
        if cand:
            return cand
    # "성수 방법", "성수 경로"처럼 짧은 목적지+키워드 패턴
    m3 = re.search(r"([가-힣A-Za-z0-9]{2,20})\s*(?:방법|경로)$", s)
    if m3:
        cand = m3.group(1).strip()
        if cand:
            return cand
    return None


def _normalize_place_name(name: str | None) -> str:
    if not name:
        return ""
    return re.sub(r"\s+", "", str(name)).lower()


def _is_home_update_utterance(text: str) -> bool:
    t = str(text or "")
    if not t:
        return False
    keywords = [
        "이사",
        "집은",
        "우리 집",
        "우리집",
        "집 주소",
        "집 위치",
        "집 도착역",
        "집 근처 역",
        "집이 ",
    ]
    return any(k in t for k in keywords)


def _build_destination_candidates(name: str | None):
    raw = str(name or "").strip()
    if not raw:
        return []
    cands = []

    def _add(v: str):
        t = str(v or "").strip()
        if t and t not in cands:
            cands.append(t)

    base = raw
    _add(base)
    # Remove common trailing particles/noise from STT.
    cleaned = re.sub(r"(으로|로|에|에서|쪽|근처|부근|방향|가는길|가는 길|가는|갈|방법|경로)$", "", base).strip()
    _add(cleaned)
    compact = re.sub(r"\s+", "", cleaned)
    _add(compact)

    for seed in [base, cleaned, compact]:
        if seed and not seed.endswith("역"):
            _add(seed + "역")
    return [x for x in cands if x]


def _resolve_destination_coords_from_name(name: str):
    if not ODSAY_API_KEY or not name:
        return None, None

    def _search_station(station_name: str):
        query = urllib.parse.urlencode({"apiKey": ODSAY_API_KEY, "stationName": station_name})
        url = f"https://api.odsay.com/v1/api/searchStation?{query}"
        data = _http_get_json(url, timeout=6)
        if not isinstance(data, dict):
            return None, None
        result = data.get("result", {})
        station_list = result.get("station") if isinstance(result, dict) else None
        if isinstance(station_list, list) and station_list:
            first = station_list[0] if isinstance(station_list[0], dict) else {}
            x = _to_float(first.get("x"))
            y = _to_float(first.get("y"))
            return y, x
        return None, None

    candidates = _build_destination_candidates(name)

    for cand in candidates:
        y, x = _search_station(cand)
        if y is not None and x is not None:
            return y, x

    return None, None


def _to_int(value):
    try:
        return int(float(value))
    except Exception:
        return None


def _round_eta_minutes(total_seconds: int) -> int:
    if total_seconds <= 0:
        return 0
    # Conservative rounding for boarding decisions:
    # 3m30s -> about 3 minutes (not 4), while keeping sub-1m as 1.
    return max(1, total_seconds // 60)


def _parse_eta_minutes_from_message(message: str):
    text = str(message or "")
    m = re.search(r"(\d+)\s*\uBD84(?:\s*(\d+)\s*\uCD08)?", text)
    if m:
        mm = int(m.group(1) or 0)
        ss = int(m.group(2) or 0)
        return _round_eta_minutes(mm * 60 + ss)
    if re.search(r"\uC804\uC5ED\s*\uB3C4\uCC29", text):
        return 1
    if re.search(r"\uACF3\s*\uB3C4\uCC29|\uC7A0\uC2DC\s*\uD6C4|\uC9C4\uC785|\uB3C4\uCC29", text):
        return 0
    return None

def _extract_arrival_minutes(row: dict, allow_zero: bool = True):
    raw_seconds = _to_int(row.get("barvlDt"))
    if raw_seconds is not None and raw_seconds > 0:
        return _round_eta_minutes(raw_seconds)
    if raw_seconds == 0 and allow_zero:
        return 0
    parsed = _parse_eta_minutes_from_message(str(row.get("arvlMsg2", "")))
    if parsed == 0 and not allow_zero:
        return None
    return parsed


def _format_eta_phrase(minutes: int | None) -> str | None:
    if minutes is None:
        return None
    if minutes <= 2:
        return "곧 도착"
    return f"약 {minutes}분"


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _estimate_walk_minutes(lat: float, lng: float, station_lat: float | None, station_lng: float | None):
    if station_lat is None or station_lng is None:
        return None
    distance_m = _haversine_meters(lat, lng, station_lat, station_lng)
    # Inflate straight-line distance to approximate real walking path.
    path_m = distance_m * 1.25
    speed_m_per_min = 4200 / 60  # ~4.2km/h
    return max(1, int(round(path_m / speed_m_per_min)))


def _pick_station_from_odsay_response(data):
    if not isinstance(data, dict):
        return None

    if data.get("error"):
        print(f"[SeoulInfo] ODSAY error: {data.get('error')}")
    if data.get("result", {}).get("error"):
        print(f"[SeoulInfo] ODSAY result error: {data.get('result', {}).get('error')}")

    result = data.get("result", {})
    candidates = []
    if isinstance(result, dict):
        for key in ("station", "stationInfo", "stations"):
            value = result.get(key)
            if isinstance(value, list):
                candidates.extend([x for x in value if isinstance(x, dict)])

    if not candidates and isinstance(result, list):
        candidates = [x for x in result if isinstance(x, dict)]

    if not candidates:
        return None

    first = candidates[0]
    name = str(first.get("stationName") or first.get("stationNm") or first.get("name") or "").strip()
    if not name:
        return None

    raw_lng = first.get("x") or first.get("gpsX") or first.get("lon") or first.get("longitude")
    raw_lat = first.get("y") or first.get("gpsY") or first.get("lat") or first.get("latitude")
    station_lng = float(raw_lng) if raw_lng is not None else None
    station_lat = float(raw_lat) if raw_lat is not None else None

    return {
        "name": name,
        "lat": station_lat,
        "lng": station_lng,
    }


def _get_nearby_station(lat: float, lng: float, station_class: int | None = 2, log_label: str = "station"):
    if not ODSAY_API_KEY:
        return None

    # Try wider search radii and flexible parameter sets because pointSearch
    # responses vary by account tier/region and nearby station density.
    for radius in (800, 1500, 3000):
        for include_station_class in (True, False):
            params = {
                "apiKey": ODSAY_API_KEY,
                "x": lng,  # longitude
                "y": lat,  # latitude
                "radius": radius,
            }
            if include_station_class:
                if station_class is None:
                    continue
                params["stationClass"] = station_class

            query = urllib.parse.urlencode(params)
            url = f"https://api.odsay.com/v1/api/pointSearch?{query}"
            data = _http_get_json(url)
            picked = _pick_station_from_odsay_response(data)
            if picked:
                return picked

    print(f"[SeoulInfo] ODSAY nearby {log_label} not found (lat={lat}, lng={lng})")
    return None


def _get_nearby_bus_stop(lat: float, lng: float):
    return _get_nearby_station(lat, lng, station_class=1, log_label="bus stop")


def _get_subway_arrival(station_name: str):
    if not SEOUL_API_KEY:
        return []

    safe_station = urllib.parse.quote(station_name)
    url = (
        f"http://swopenapi.seoul.go.kr/api/subway/{SEOUL_API_KEY}/json/"
        f"realtimeStationArrival/0/5/{safe_station}"
    )
    data = _http_get_json(url)
    if not isinstance(data, dict):
        return []

    rows = data.get("realtimeArrivalList", [])
    return rows if isinstance(rows, list) else []


def _get_odsay_path(sx: float, sy: float, ex: float, ey: float, search_path_type: int = 0):
    if not ODSAY_API_KEY:
        return None
    query = urllib.parse.urlencode(
        {
            "apiKey": ODSAY_API_KEY,
            "SX": sx,
            "SY": sy,
            "EX": ex,
            "EY": ey,
            "SearchPathType": search_path_type,  # 0=all, 1=subway
        }
    )
    url = f"https://api.odsay.com/v1/api/searchPubTransPathT?{query}"
    data = _http_get_json(url, timeout=8)
    if not isinstance(data, dict):
        return None
    if data.get("error"):
        print(f"[SeoulInfo] ODSAY path error: {data.get('error')}")
    result = data.get("result", {})
    paths = result.get("path") if isinstance(result, dict) else None
    if isinstance(paths, list) and paths:
        return paths[0] if isinstance(paths[0], dict) else None
    return None


def _parse_odsay_strategy(path_obj: dict):
    if not isinstance(path_obj, dict):
        return {}
    info = path_obj.get("info", {}) if isinstance(path_obj.get("info"), dict) else {}
    sub_paths = path_obj.get("subPath", []) if isinstance(path_obj.get("subPath"), list) else []

    first_ride = None
    for seg in sub_paths:
        if not isinstance(seg, dict):
            continue
        traffic_type = _to_int(seg.get("trafficType"))
        if traffic_type in (1, 2):
            first_ride = seg
            break

    strategy = {
        "totalTimeMinutes": _to_int(info.get("totalTime")),
        "payment": _to_int(info.get("payment")),
        "transferCount": _to_int(info.get("busTransitCount")) if _to_int(info.get("busTransitCount")) is not None else _to_int(info.get("subwayTransitCount")),
        "firstMode": None,
        "firstBoardName": None,
        "firstDirection": None,
        "firstStartLat": _to_float(first_ride.get("startY")) if isinstance(first_ride, dict) else None,
        "firstStartLng": _to_float(first_ride.get("startX")) if isinstance(first_ride, dict) else None,
        "busNumbers": [],
        "subwayLine": None,
        "subwayLegs": [],
    }

    if isinstance(first_ride, dict):
        tt = _to_int(first_ride.get("trafficType"))
        lane = first_ride.get("lane", [])
        lane0 = lane[0] if isinstance(lane, list) and lane and isinstance(lane[0], dict) else {}
        strategy["firstBoardName"] = first_ride.get("startName")
        strategy["firstDirection"] = first_ride.get("way")

        if tt == 2:
            strategy["firstMode"] = "bus"
            bus_nos = []
            if isinstance(lane, list):
                for l in lane:
                    if isinstance(l, dict):
                        no = l.get("busNo")
                        if no:
                            bus_nos.append(str(no))
            strategy["busNumbers"] = bus_nos
        elif tt == 1:
            strategy["firstMode"] = "subway"
            strategy["subwayLine"] = lane0.get("name")

    # Capture full subway-leg sequence for detailed transfer guidance.
    subway_legs = []
    for seg in sub_paths:
        if not isinstance(seg, dict):
            continue
        if _to_int(seg.get("trafficType")) != 1:
            continue
        lane = seg.get("lane", [])
        lane0 = lane[0] if isinstance(lane, list) and lane and isinstance(lane[0], dict) else {}
        subway_legs.append(
            {
                "line": str(lane0.get("name") or "").strip(),
                "start": str(seg.get("startName") or "").strip(),
                "end": str(seg.get("endName") or "").strip(),
                "direction": str(seg.get("way") or "").strip(),
            }
        )
    strategy["subwayLegs"] = [x for x in subway_legs if x.get("line") and x.get("start") and x.get("end")]

    return strategy


def _get_weather_and_air(lat: float, lng: float):
    weather = {}
    w_url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urllib.parse.urlencode(
            {
                "latitude": lat,
                "longitude": lng,
                "current": "temperature_2m,precipitation,rain",
                "timezone": "Asia/Seoul",
            }
        )
    )
    w = _http_get_json(w_url, timeout=6)
    if isinstance(w, dict) and isinstance(w.get("current"), dict):
        cur = w.get("current")
        weather = {
            "tempC": _to_float(cur.get("temperature_2m")),
            "precipitationMm": _to_float(cur.get("precipitation")),
            "rainMm": _to_float(cur.get("rain")),
        }

    aq_url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality?"
        + urllib.parse.urlencode(
            {
                "latitude": lat,
                "longitude": lng,
                "current": "us_aqi,pm10,pm2_5",
                "timezone": "Asia/Seoul",
            }
        )
    )
    aq = _http_get_json(aq_url, timeout=6)
    air = {}
    if isinstance(aq, dict) and isinstance(aq.get("current"), dict):
        cur = aq.get("current")
        air = {
            "usAqi": _to_int(cur.get("us_aqi")),
            "pm10": _to_float(cur.get("pm10")),
            "pm25": _to_float(cur.get("pm2_5")),
        }

    return weather, air


def _build_live_seoul_summary(
    lat: float | None,
    lng: float | None,
    station_name: str | None,
    destination_name: str | None = None,
    prefer_subway: bool = False,
    detailed_subway: bool = False,
):
    station = station_name.strip() if isinstance(station_name, str) and station_name.strip() else None
    station_lat = None
    station_lng = None

    bus_stop_name = None
    walk_to_bus_stop_min = None

    if lat is not None and lng is not None:
        nearby_subway = _get_nearby_station(lat, lng)
        if isinstance(nearby_subway, dict):
            if not station:
                station = nearby_subway.get("name")
            station_lat = nearby_subway.get("lat")
            station_lng = nearby_subway.get("lng")

        nearby_bus = _get_nearby_bus_stop(lat, lng)
        if isinstance(nearby_bus, dict):
            bus_stop_name = nearby_bus.get("name")
            walk_to_bus_stop_min = _estimate_walk_minutes(lat, lng, nearby_bus.get("lat"), nearby_bus.get("lng"))

    destination_requested = bool(destination_name and str(destination_name).strip())
    target_lat, target_lng = _resolve_destination_coords_from_name(destination_name) if destination_requested else (None, None)
    destination_resolved = target_lat is not None and target_lng is not None
    # Only use default home coords when user did not explicitly request another destination.
    if not destination_requested and (target_lat is None or target_lng is None):
        target_lat, target_lng = _resolve_home_coords()
        destination_resolved = target_lat is not None and target_lng is not None
    strategy = {}
    if lat is not None and lng is not None and target_lat is not None and target_lng is not None:
        path_type = 1 if prefer_subway else 0
        path_obj = _get_odsay_path(sx=lng, sy=lat, ex=target_lng, ey=target_lat, search_path_type=path_type)
        strategy = _parse_odsay_strategy(path_obj) if isinstance(path_obj, dict) else {}
        # If subway-only path fails, fallback to general path to preserve minimum guidance.
        if prefer_subway and strategy.get("firstMode") != "subway":
            fallback_obj = _get_odsay_path(sx=lng, sy=lat, ex=target_lng, ey=target_lat, search_path_type=0)
            fallback_strategy = _parse_odsay_strategy(fallback_obj) if isinstance(fallback_obj, dict) else {}
            if isinstance(fallback_strategy, dict) and fallback_strategy:
                strategy = fallback_strategy

    weather = {}
    air = {}
    if lat is not None and lng is not None:
        weather, air = _get_weather_and_air(lat, lng)

    first_mode = strategy.get("firstMode")
    first_board = strategy.get("firstBoardName")
    first_direction = strategy.get("firstDirection")
    subway_line = strategy.get("subwayLine")
    bus_numbers = strategy.get("busNumbers") or []
    subway_legs = strategy.get("subwayLegs") or []

    departure_station = first_board if first_mode == "subway" and first_board else station
    arrivals = _get_subway_arrival(departure_station) if departure_station else []
    rows = [r for r in arrivals if isinstance(r, dict)]
    rows.sort(key=lambda r: str(r.get("ordkey", "")))

    # If line hint exists, prioritize rows matching that line text.
    if subway_line:
        line_token = str(subway_line).split("(")[0].strip()
        matched = [r for r in rows if line_token and line_token in str(r.get("trainLineNm", ""))]
        if matched:
            rows = matched

    first = rows[0] if rows else {}
    second = rows[1] if len(rows) > 1 else {}

    first_eta = _extract_arrival_minutes(first, allow_zero=True) if first else None
    next_eta = _extract_arrival_minutes(second, allow_zero=False) if second else None
    if first_eta is not None and next_eta is not None and next_eta <= first_eta:
        next_eta = None

    # Walking time to first boarding point (prefer ODSAY first segment coords)
    walk_to_departure_min = None
    if lat is not None and lng is not None:
        walk_to_departure_min = _estimate_walk_minutes(
            lat,
            lng,
            strategy.get("firstStartLat") if strategy else station_lat,
            strategy.get("firstStartLng") if strategy else station_lng,
        )

    decision = None
    if first_mode == "subway":
        if walk_to_departure_min is not None and first_eta is not None:
            if walk_to_departure_min < first_eta:
                decision = "first"
            else:
                if next_eta is not None:
                    if walk_to_departure_min < next_eta:
                        decision = "next"
                    else:
                        decision = "after_next"
                else:
                    decision = "after_next"
        else:
            decision = "first"

    parts = []

    if destination_requested and not destination_resolved:
        parts.append(f"'{destination_name}' 목적지를 역 기준으로 찾지 못했어요. 예: 성수역, 강남역처럼 말씀해 주세요.")
        if station:
            parts.append(f"현재 기준 가장 가까운 역은 {station}역이에요.")
    elif prefer_subway:
        # Commute-home default: always speak in subway terms.
        if not departure_station:
            parts.append("지하철 출발역을 찾지 못했어요. 역 이름을 말씀해 주시면 바로 확인해 드릴게요.")
        else:
            line_text = str(subway_line or first.get("trainLineNm") or "해당 노선")
            direction_text = str(first_direction or first.get("trainLineNm") or "방면 정보 확인 중")
            parts.append(f"지하철로 가시려면 {departure_station}역에서 {line_text}을 타시면 돼요.")
            parts.append(f"탑승 방면은 {direction_text}입니다.")
            if walk_to_departure_min is not None:
                parts.append(f"현재 위치에서 출발역까지 도보 약 {walk_to_departure_min}분 걸려요.")
            eta_phrase = _format_eta_phrase(first_eta)
            if eta_phrase:
                parts.append(f"이번 열차는 {eta_phrase}이에요.")

            if decision == "next" and next_eta is not None:
                next_phrase = _format_eta_phrase(next_eta) or f"약 {next_eta}분"
                parts.append(f"현재 이동 시간 기준으로 이번 열차는 어렵고, 다음 열차({next_phrase} 후)를 권장해요.")
            elif decision == "after_next":
                parts.append("현재 이동 시간 기준으로 이번/다음 열차 모두 어렵습니다. 역 도착 후 다음 열차 시간을 다시 확인해 주세요.")
            elif decision == "first":
                parts.append("지금 출발하면 이번 열차 탑승 가능성이 있어요.")

            if detailed_subway and subway_legs:
                first_leg = subway_legs[0]
                parts.append(
                    f"상세 경로는 {first_leg.get('start')}역에서 {first_leg.get('line')} "
                    f"{first_leg.get('direction') or '방면'} 열차를 타고 {first_leg.get('end')}역에서 내리시면 돼요."
                )
                if len(subway_legs) > 1:
                    for idx, leg in enumerate(subway_legs[1:], start=2):
                        parts.append(
                            f"{idx-1}차 환승은 {leg.get('start')}역에서 {leg.get('line')} "
                            f"{leg.get('direction') or '방면'}으로 갈아타고 {leg.get('end')}역에서 내리시면 돼요."
                        )

    elif first_mode == "bus":
        parts.append("가장 빠른 대중교통 시작 구간은 버스예요.")
        if bus_numbers:
            parts.append(f"탑승 버스 번호는 {', '.join(bus_numbers)}입니다.")
        if first_board:
            parts.append(f"탑승 정류장은 {first_board}입니다.")
        if walk_to_departure_min is not None:
            parts.append(f"현재 위치에서 그 정류장까지 도보 약 {walk_to_departure_min}분 걸려요.")
        elif bus_stop_name and walk_to_bus_stop_min is not None:
            parts.append(f"가장 가까운 정류장 {bus_stop_name}까지 도보 약 {walk_to_bus_stop_min}분 걸려요.")

    elif first_mode == "subway":
        line_text = str(subway_line or first.get("trainLineNm") or "해당 노선")
        direction_text = str(first_direction or first.get("trainLineNm") or "방면 정보 없음")
        parts.append(f"지하철 기준 가장 빠른 경로는 {departure_station}역에서 {line_text} 열차 탑승이에요.")
        parts.append(f"탑승 방면은 {direction_text}입니다.")

        if walk_to_departure_min is not None:
            parts.append(f"현재 위치에서 출발역까지 도보 약 {walk_to_departure_min}분 걸려요.")
        eta_phrase = _format_eta_phrase(first_eta)
        if eta_phrase:
            parts.append(f"출발역 기준 이번 열차는 {eta_phrase}이에요.")

        if decision == "next" and next_eta is not None:
            next_phrase = _format_eta_phrase(next_eta) or f"약 {next_eta}분"
            parts.append(f"지금 이동하면 이번 열차는 어렵고, 다음 열차는 {next_phrase} 후예요.")
        elif decision == "after_next":
            parts.append("지금 이동하면 이번/다음 열차 모두 어렵습니다. 역 도착 후 다음 열차 시간을 다시 확인해 주세요.")
        elif decision == "first":
            parts.append("지금 출발하면 이번 열차 탑승 가능성이 있어요.")

        if detailed_subway and subway_legs:
            first_leg = subway_legs[0]
            parts.append(
                f"상세 경로는 {first_leg.get('start')}역에서 {first_leg.get('line')} "
                f"{first_leg.get('direction') or '방면'} 열차를 타고 {first_leg.get('end')}역에서 내리시면 돼요."
            )
            if len(subway_legs) > 1:
                for idx, leg in enumerate(subway_legs[1:], start=2):
                    parts.append(
                        f"{idx-1}차 환승은 {leg.get('start')}역에서 {leg.get('line')} "
                        f"{leg.get('direction') or '방면'}으로 갈아타고 {leg.get('end')}역에서 내리시면 돼요."
                    )

    else:
        if station:
            parts.append(f"현재 기준 가장 가까운 지하철역은 {station}역이에요.")
        if bus_stop_name and walk_to_bus_stop_min is not None:
            parts.append(f"가장 가까운 버스 정류장은 {bus_stop_name}, 도보 약 {walk_to_bus_stop_min}분입니다.")

    if not parts:
        parts.append("실시간 경로 정보를 충분히 받지 못했어요. 출발지와 목적지를 다시 확인해 주세요.")

    summary = " ".join(parts)

    return {
        "station": station,
        "speechSummary": summary,
        "arrivals": arrivals,
        "decision": decision,
        "firstEtaMinutes": first_eta,
        "nextEtaMinutes": next_eta,
        "walkToStationMinutes": walk_to_departure_min,
        "busStopName": bus_stop_name,
        "walkToBusStopMinutes": walk_to_bus_stop_min,
        "busNumbers": bus_numbers,
        "firstMode": first_mode,
        "firstDirection": first_direction,
        "weather": weather,
        "air": air,
        "homeConfigured": target_lat is not None and target_lng is not None,
        "destinationName": destination_name,
        "destinationRequested": destination_requested,
        "destinationResolved": destination_resolved,
    }


def _execute_tools_for_intent(
    intent: str,
    lat: float | None,
    lng: float | None,
    destination_name: str | None,
):
    is_default_destination = (
        _normalize_place_name(destination_name) == _normalize_place_name(COMMUTE_DEFAULT_DESTINATION)
        if destination_name
        else True
    )
    prefer_subway = intent == "subway_route" or (intent == "commute_overview" and is_default_destination)
    detailed_subway = (intent in {"subway_route", "commute_overview"}) and (not is_default_destination)
    live = _build_live_seoul_summary(
        lat=lat,
        lng=lng,
        station_name=None,
        destination_name=destination_name,
        prefer_subway=prefer_subway,
        detailed_subway=detailed_subway,
    )
    if not isinstance(live, dict):
        return None

    parts = []
    if intent == "subway_route":
        parts.append(str(live.get("speechSummary", "")))
    elif intent == "bus_route":
        nums = live.get("busNumbers") or []
        stop = live.get("busStopName")
        walk = live.get("walkToBusStopMinutes")
        if nums:
            parts.append(f"버스 번호는 {', '.join([str(x) for x in nums])}입니다.")
        if stop:
            if walk is not None:
                parts.append(f"탑승 정류장은 {stop}, 도보 약 {walk}분입니다.")
            else:
                parts.append(f"탑승 정류장은 {stop}입니다.")
        if not parts:
            parts.append("버스 정보를 확인하지 못했어요. 목적지나 출발지를 더 구체적으로 말씀해 주세요.")
    elif intent == "weather":
        w = live.get("weather") or {}
        t = w.get("tempC")
        rain = w.get("rainMm")
        precip = w.get("precipitationMm")
        if t is not None:
            parts.append(f"현재 기온은 약 {int(round(float(t)))}도입니다.")
        if rain is not None or precip is not None:
            parts.append(f"강수는 현재 약 {rain or precip}mm 수준입니다.")
        if not parts:
            parts.append("날씨 데이터를 현재 받지 못했어요.")
    elif intent == "air_quality":
        a = live.get("air") or {}
        if a.get("usAqi") is not None:
            parts.append(f"현재 대기질은 US AQI {a.get('usAqi')}입니다.")
        if a.get("pm25") is not None:
            parts.append(f"초미세먼지는 {a.get('pm25')}입니다.")
        if a.get("pm10") is not None:
            parts.append(f"미세먼지는 {a.get('pm10')}입니다.")
        if not parts:
            parts.append("대기질 데이터를 현재 받지 못했어요.")
    else:
        parts.append(str(live.get("speechSummary", "")))

    merged = " ".join([p for p in parts if p]).strip()
    live["speechSummary"] = merged or str(live.get("speechSummary", ""))
    return live

# --- Helper: Azure STT Setup ---
def create_push_stream(sample_rate=16000):
    stream_format = speechsdk.audio.AudioStreamFormat(samples_per_second=sample_rate, bits_per_sample=16, channels=1)
    push_stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
    audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
    return push_stream, audio_config

def create_recognizer(audio_config, language="en-US"): # Default to English for now, or use "ko-KR"
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_recognition_language = language
    
    # [Optimization] Reduce segmentation silence timeout to force faster phrase finalization
    # Default is usually higher (e.g. 500ms-1000ms). Setting to 100ms.
    speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "100")
    
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    return recognizer

# --- WebSocket Endpoint ---
@app.websocket("/ws/audio")
async def audio_websocket(ws: WebSocket):
    await ws.accept()
    
    # 1. Auth & Identification
    user_id = ws.query_params.get("user_id")
    current_lat = _to_float(ws.query_params.get("lat"))
    current_lng = _to_float(ws.query_params.get("lng"))
    client_state = {"lat": current_lat, "lng": current_lng, "last_log_lat": current_lat, "last_log_lng": current_lng}
    if not user_id or "@" not in user_id:
        print("[Server] Missing or invalid user_id.")
        await ws.close(code=1008, reason="Invalid Login Token")
        return
        
    print(f"[Server] Client connected: {user_id}")
    if current_lat is None or current_lng is None:
        print("[SeoulInfo] Missing lat/lng in websocket query. Live ODSAY routing will be unavailable.")
    else:
        print(f"[SeoulInfo] Client location lat={current_lat}, lng={current_lng}")
    if not API_KEY or not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        print("[Error] Missing API Keys.")
        await ws.close(code=1008, reason="API Keys missing")
        return

    # 2. Load Memory (Context)
    # Fetch ALL past summaries for this user
    # Fetch ALL past summaries for this user (Blocking I/O -> Async Thread)
    # past_memories = cosmos_service.get_all_memories(user_id) 
    past_memories = await asyncio.to_thread(cosmos_service.get_all_memories, user_id)
    memory_context = ""
    if past_memories:
        memory_context = "Here is the summary of past conversations with this user:\n"
        for item in past_memories:
            summary = item.get("summary", {})
            context_text = summary.get("context_summary", "No summary")
            date = item.get("date", "Unknown Date")
            memory_context += f"- [{date}] {context_text}\n"
        
        print(f"[Memory] Loaded {len(past_memories)} past conversation summaries.")

    # Initialize Gemini
    client = genai.Client(api_key=API_KEY)
    
    user_profile = await asyncio.to_thread(cosmos_service.get_user_profile, user_id)
    saved_home_destination = None
    if isinstance(user_profile, dict):
        saved_home_destination = str(user_profile.get("home_destination") or "").strip() or None
    if saved_home_destination:
        print(f"[Profile] Loaded home destination for {user_id}: {saved_home_destination}")

    destination_state = {
        "name": saved_home_destination or COMMUTE_DEFAULT_DESTINATION,
        "asked_once": False,
    }

    # Inject Memory into System Instruction
    system_instruction = (
        "You are Aira, a warm and practical Korean voice assistant. "
        "For transit/city/weather/air-quality topics, never fabricate facts. "
        "Only state information that is explicitly present in provided live context. "
        "If required data is missing, say what is missing and ask one concise follow-up question. "
        "For subway guidance, include departure station, line/direction, ETA, walking minutes, and whether to take current or next train only when present in live context. "
        "For bus guidance, provide bus number, boarding stop name, and walking minutes when present in live context. "
        "Do not invent route, direction, ETA, weather, or air-quality values. "
        "Do not mention crowding/congestion unless explicit congestion data is provided in live context. "
        "For Korean transit questions, never ask user's current location; device coordinates are already provided by server."
    )
    if current_lat is not None and current_lng is not None:
        system_instruction += (
            " Current location is already known from device coordinates. "
            "Do not ask the user where they are. "
            f"Known coordinates: lat={current_lat}, lng={current_lng}."
        )
    if memory_context:
        system_instruction += f"\n\n[MEMORY LOADED]\n{memory_context}\nUse this context to personalize your responses."
    # Do not pin a preloaded route in system instruction.
    # Route context should be injected per-turn to avoid stale destination bias.

    config = {
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "voice_config": {"prebuilt_voice_config": {"voice_name": "Aoede"}}
        },
        "system_instruction": system_instruction
    }

    # Initialize Azure STT (User: 16kHz, AI: 24kHz)
    user_push_stream, user_audio_config = create_push_stream(16000)
    user_recognizer = create_recognizer(user_audio_config, "ko-KR") # Assuming Korean context based on user prompts

    ai_push_stream, ai_audio_config = create_push_stream(24000)
    ai_recognizer = create_recognizer(ai_audio_config, "ko-KR")

    # Capture the main event loop
    loop = asyncio.get_running_loop()

    # Track state for Smart Flushing
    state = {"last_ai_write_time": 0, "flushed": False}
    dynamic_contexts = []
    dynamic_context_lock = asyncio.Lock()
    session_ref = {"obj": None}
    
    # Track Full Transcript for Summarization
    session_transcript = []
    route_dedupe = {"text": "", "ts": 0.0}
    transit_turn_gate = {"until": 0.0}

    async def _inject_live_context_now(context_text: str, complete_turn: bool = False):
        session_obj = session_ref.get("obj")
        if not session_obj:
            async with dynamic_context_lock:
                dynamic_contexts.append(context_text)
            return
        await session_obj.send_client_content(
            turns=[
                {
                    "role": "user",
                    "parts": [
                        {"text": "[LIVE_CONTEXT_UPDATE]\n" + context_text + "\nUse this for current answer."}
                    ],
                }
            ],
            turn_complete=complete_turn,
        )

    async def _send_user_text_turn(user_text: str):
        session_obj = session_ref.get("obj")
        if not session_obj:
            return
        await session_obj.send_client_content(
            turns=[
                {
                    "role": "user",
                    "parts": [{"text": str(user_text or "")}],
                }
            ],
            turn_complete=True,
        )

    async def _inject_initial_location_context():
        if client_state.get("lat") is None or client_state.get("lng") is None:
            return
        try:
            await _inject_live_context_now(
                "[INTENT:location_context] Current location coordinates are already known from device. "
                "Do not ask user's current location.",
                complete_turn=False,
            )
        except Exception as e:
            print(f"[SeoulInfo] initial location context injection failed: {e}")

    async def _save_home_destination(new_home_destination: str):
        dest = str(new_home_destination or "").strip()
        if not dest:
            return
        try:
            await asyncio.to_thread(
                cosmos_service.upsert_user_profile,
                user_id,
                {"home_destination": dest},
            )
        except Exception as e:
            print(f"[Profile] Failed to save home destination: {e}")

    # STT Event Handlers
    def on_recognized(args, role):
        if args.result.text:
            text = args.result.text
            print(f"[STT] {role}: {text}")
            
            # Store for memory
            session_transcript.append(f"{role.upper()}: {text}")

            if role == "user":
                try:
                    normalized_user_text = re.sub(r"\s+", "", str(text or ""))
                    now_ts = time.monotonic()
                    # Azure STT can emit near-duplicate finalized chunks; skip fast duplicates.
                    if (
                        normalized_user_text
                        and normalized_user_text == route_dedupe.get("text")
                        and (now_ts - float(route_dedupe.get("ts") or 0.0)) < 1.5
                    ):
                        print(f"[IntentRouter] skip duplicate user turn: {text}")
                        return
                    route_dedupe["text"] = normalized_user_text
                    route_dedupe["ts"] = now_ts

                    route = intent_router.route(text)
                    intent = route.get("intent") if isinstance(route, dict) else "commute_overview"
                    routed_dest = route.get("destination") if isinstance(route, dict) else None
                    routed_home_update = bool(route.get("home_update")) if isinstance(route, dict) else False
                    route_source = route.get("source") if isinstance(route, dict) else "fallback"
                    print(
                        f"[IntentRouter] source={route_source}, intent={intent}, "
                        f"destination={routed_dest}, home_update={routed_home_update}"
                    )
                    # LLM-first: only use regex destination extraction when fallback routing is active.
                    if route_source == "llm":
                        dest = routed_dest
                    else:
                        dest = routed_dest or _extract_destination_from_text(text)
                    # If destination is explicitly mentioned with route-like wording, prefer route intent.
                    if dest and intent == "general" and any(k in text for k in ["길", "경로", "가는"]):
                        intent = "commute_overview"
                    if dest:
                        next_dest = str(dest).strip()
                        if next_dest and next_dest != destination_state.get("name"):
                            destination_state["name"] = next_dest
                        destination_state["asked_once"] = False

                    # Persist home destination only when classifier says this is a home update utterance.
                    if routed_home_update or (route_source != "llm" and _is_home_update_utterance(text)):
                        home_candidate = str(dest or "").strip()
                        if not home_candidate and route_source != "llm":
                            home_candidate = str(_extract_destination_from_text(text) or "").strip()
                        if home_candidate:
                            destination_state["name"] = home_candidate
                            destination_state["asked_once"] = False
                            if loop.is_running():
                                asyncio.run_coroutine_threadsafe(
                                    _save_home_destination(home_candidate),
                                    loop,
                                )
                            print(f"[Profile] Home destination updated in-session: {home_candidate}")

                    live_summary = None
                    routing_intents = {"subway_route", "bus_route", "commute_overview", "weather", "air_quality"}
                    should_inject_live = intent in routing_intents

                    if should_inject_live:
                        if client_state.get("lat") is not None and client_state.get("lng") is not None and loop.is_running():
                            asyncio.run_coroutine_threadsafe(
                                _inject_live_context_now(
                                    "[INTENT:location_guard] Device location is already known and valid for this turn. "
                                    "Do not ask user location.",
                                    complete_turn=False,
                                ),
                                loop,
                            )

                        # For transit queries that require live API fetch, speak a short filler first.
                        # This reduces awkward silence while ODSAY/Seoul APIs are being fetched.
                        if (
                            (not GEMINI_DIRECT_AUDIO_INPUT)
                            and ENABLE_TRANSIT_FILLER
                            and intent in {"subway_route", "bus_route", "commute_overview"}
                            and loop.is_running()
                        ):
                            filler_text = (
                                "[INTENT:loading] The user requested live transit guidance. "
                                "First, say one short Korean filler sentence naturally "
                                "(e.g., '음, 잠시만요. 지금 확인해볼게요.'). "
                                "Do not provide route details yet. "
                                "Do not ask for user location."
                            )
                            asyncio.run_coroutine_threadsafe(
                                _inject_live_context_now(filler_text, complete_turn=True),
                                loop,
                            )

                        live_data = _execute_tools_for_intent(
                            intent=intent or "commute_overview",
                            lat=client_state.get("lat"),
                            lng=client_state.get("lng"),
                            destination_name=destination_state["name"],
                        )
                        live_summary = live_data.get("speechSummary") if isinstance(live_data, dict) else None
                        print(
                            f"[SeoulInfo] live context built: intent={intent}, destination={destination_state.get('name')}, "
                            f"summary_ok={bool(live_summary)}"
                        )

                        guidance = []
                        if client_state.get("lat") is not None and client_state.get("lng") is not None:
                            guidance.append("Location is known; do not ask user's current location.")
                        if destination_state.get("name"):
                            guidance.append(
                                f"Use destination '{destination_state['name']}' for this turn and ignore older destination context."
                            )
                        if (
                            not destination_state.get("name")
                            and intent in {"subway_route", "bus_route", "commute_overview"}
                        ):
                            if not destination_state.get("asked_once", False):
                                guidance.append("Ask destination exactly once in one short question.")
                                destination_state["asked_once"] = True
                            else:
                                guidance.append("Destination still missing; do not repeat destination question.")

                        if not live_summary:
                            if client_state.get("lat") is not None and client_state.get("lng") is not None:
                                live_summary = (
                                    "현재 위치 좌표는 이미 수신되어 있어요. "
                                    "목적지만 확인되면 경로를 바로 계산할 수 있어요."
                                )
                            else:
                                live_summary = "경로 계산에 필요한 위치 좌표가 없습니다."

                        ctx_text = f"[INTENT:{intent or 'commute_overview'}] {str(live_summary)}"
                        if guidance:
                            ctx_text += " [GUIDE] " + " ".join(guidance)
                        if intent in {"subway_route", "bus_route", "commute_overview"}:
                            ctx_text += (
                                " [ACTION] Respond to the user's latest request now using this context. "
                                "Give one concise final answer only. "
                                "Do not add extra uncertainty/caveat sentences or follow-up questions after answering. "
                                "Do not say you cannot provide realtime data unless the provided summary explicitly says data is missing. "
                                "If summary exists, prioritize it and answer directly from it."
                            )
                            # Temporarily gate direct audio input so context turn is processed first.
                            transit_turn_gate["until"] = time.monotonic() + 2.5

                        if loop.is_running():
                            asyncio.run_coroutine_threadsafe(
                                _inject_live_context_now(
                                    ctx_text,
                                    complete_turn=intent in {"subway_route", "bus_route", "commute_overview"},
                                ),
                                loop,
                            )
                    else:
                        # Text-only path for non-routing/general turns when direct audio is disabled.
                        if (not GEMINI_DIRECT_AUDIO_INPUT) and loop.is_running():
                            asyncio.run_coroutine_threadsafe(_send_user_text_turn(text), loop)
                except Exception as e:
                    print(f"[SeoulInfo] dynamic context build failed: {e}")
            
            payload = json.dumps({"type": "transcript", "role": role, "text": text})
            
            # [Fix 1] Robust Loop Handling
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(ws.send_text(payload), loop)
            else:
                print(f"[Error] Main loop is closed. Cannot send STT: {text}")

    user_recognizer.recognized.connect(lambda evt: on_recognized(evt, "user"))
    ai_recognizer.recognized.connect(lambda evt: on_recognized(evt, "ai"))

    user_recognizer.start_continuous_recognition()
    ai_recognizer.start_continuous_recognition()

    try:
        async with client.aio.live.connect(model=MODEL_NAME, config=config) as session:
            print("[Gemini] Connected to Live API")
            session_ref["obj"] = session
            await _inject_initial_location_context()
            state["last_ai_write_time"] = asyncio.get_running_loop().time()
            
            async def receive_from_client():
                try:
                    while True:
                        msg = await ws.receive()
                        msg_type = msg.get("type")
                        if msg_type == "websocket.disconnect":
                            print("[Server] WebSocket Disconnected (Receive Loop)")
                            return
                        if msg_type != "websocket.receive":
                            continue

                        text_data = msg.get("text")
                        if text_data:
                            try:
                                payload = json.loads(text_data)
                                if isinstance(payload, dict) and payload.get("type") == "location_update":
                                    new_lat = _to_float(payload.get("lat"))
                                    new_lng = _to_float(payload.get("lng"))
                                    if new_lat is not None and new_lng is not None:
                                        client_state["lat"] = new_lat
                                        client_state["lng"] = new_lng
                                        prev_lat = _to_float(client_state.get("last_log_lat"))
                                        prev_lng = _to_float(client_state.get("last_log_lng"))
                                        moved_m = None
                                        if prev_lat is not None and prev_lng is not None:
                                            moved_m = _haversine_meters(prev_lat, prev_lng, new_lat, new_lng)
                                        # Reduce noisy logs: print only when movement is meaningful.
                                        if moved_m is None or moved_m >= 25:
                                            print(f"[SeoulInfo] Location updated lat={new_lat}, lng={new_lng}")
                                            client_state["last_log_lat"] = new_lat
                                            client_state["last_log_lng"] = new_lng
                            except Exception:
                                pass
                            continue

                        data = msg.get("bytes")
                        # Ignore non-binary frames (e.g., text/control keepalive)
                        if not data:
                            continue

                        # Inject freshest per-turn live context before audio chunk when available.
                        injected_context = None
                        async with dynamic_context_lock:
                            if dynamic_contexts:
                                injected_context = dynamic_contexts.pop()
                                dynamic_contexts.clear()
                        if injected_context:
                            try:
                                await session.send_client_content(
                                    turns=[
                                        {
                                            "role": "user",
                                            "parts": [
                                                {
                                                    "text": (
                                                        "[LIVE_CONTEXT_UPDATE]\n"
                                                        + injected_context
                                                        + "\nUse this for current answer."
                                                    )
                                                }
                                            ],
                                        }
                                    ],
                                    turn_complete=False,
                                )
                            except Exception as e:
                                print(f"[SeoulInfo] context injection failed: {e}")
                        if GEMINI_DIRECT_AUDIO_INPUT and time.monotonic() >= float(transit_turn_gate.get("until") or 0.0):
                            await session.send_realtime_input(audio={"data": data, "mime_type": "audio/pcm;rate=16000"})
                        # [Fix] Pushing to Azure Stream might block if internal buffer is full. Offload to thread.
                        await asyncio.to_thread(user_push_stream.write, data)
                except WebSocketDisconnect:
                    print("[Server] WebSocket Disconnected (Receive Loop)")
                    return # Clean exit logic will be handled by finally block
                except Exception as e:
                    print(f"[Server] Error processing input: {e}")

            async def send_to_client():
                try:
                    while True:
                        async for response in session.receive():
                            if response.server_content and response.server_content.model_turn:
                                for part in response.server_content.model_turn.parts:
                                    if part.inline_data:
                                        audio_bytes = part.inline_data.data
                                        await ws.send_bytes(audio_bytes)
                                        # [Fix] Offload AI audio write to thread
                                        await asyncio.to_thread(ai_push_stream.write, audio_bytes)
                                        # Update state: Audio received, not flushed yet
                                        state["last_ai_write_time"] = asyncio.get_running_loop().time()
                                        state["flushed"] = False
                            
                            # [Fix 3] Monitor Gemini Turn Complete
                            if response.server_content and response.server_content.turn_complete:
                                pass

                except Exception as e:
                    print(f"[Server] Error processing output: {e}")
                    # Don't raise here, allow silence injector to keep running or clean exit

            # [Smart Flush]
            async def smart_flush_injector():
                silence_chunk = b'\x00' * 24000 
                try:
                    while True:
                        await asyncio.sleep(0.1) # Check every 100ms
                        now = asyncio.get_running_loop().time()
                        
                        # If > 500ms passed since last audio AND we haven't flushed yet
                        if (now - state["last_ai_write_time"] > 0.5) and (not state["flushed"]):
                            print("[STT] Pause detected. Injecting silence to flush buffer.")
                            await asyncio.to_thread(ai_push_stream.write, silence_chunk)
                            state["flushed"] = True # Mark as flushed to STOP sending silence
                            
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print(f"[Server] Smart Flush Error: {e}")

            # Run tasks
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(receive_from_client()), 
                    asyncio.create_task(send_to_client()),
                    asyncio.create_task(smart_flush_injector())
                ],
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending: task.cancel()

    except Exception as e:
        print(f"[Server] Session Error or Disconnect: {e}")
    finally:
        # Cleanup
        session_ref["obj"] = None
        print("[Server] Cleaning up resources...")
        try:
            # Execute cleanup asynchronously with TIMEOUT to avoid blocking the Event Loop
            # If Azure takes too long to stop, we just abandon it to prevent "Waiting for child process" hang.
            await asyncio.wait_for(asyncio.to_thread(user_recognizer.stop_continuous_recognition), timeout=2.0)
            await asyncio.wait_for(asyncio.to_thread(ai_recognizer.stop_continuous_recognition), timeout=2.0)
        except Exception as e:
            print(f"[Server] Cleanup Warning: {e}")
        try: await ws.close() 
        except: pass
        print("[Server] Connection closed")

        # 3. Save Memory (Summarization)
        if session_transcript and len(session_transcript) > 2: # Don't save empty sessions
            print("[Memory] Summarizing session...")
            full_text = "\n".join(session_transcript)
            
            # Blocking I/O -> Async Thread
            summary_json = await asyncio.to_thread(memory_service.summarize, full_text)
            
            if summary_json and summary_json.get("context_summary"):
                await asyncio.to_thread(cosmos_service.save_memory, user_id, full_text, summary_json)
                print(f"[Memory] Session saved for {user_id}")
            else:
                print("[Memory] Skipped saving: Summary is empty or invalid.")

# --- Seoul Info Module Endpoint ---
@app.post("/api/seoul-info/normalize")
async def normalize_seoul_info(payload: dict = Body(...)):
    voice_payload = payload.get("voicePayload")
    odsay_payload = payload.get("odsayPayload")

    packet = build_seoul_info_packet(voice_payload, odsay_payload)
    speech_summary = build_speech_summary(packet)

    return {
        "packet": packet,
        "speechSummary": speech_summary
    }


@app.get("/api/seoul-info/live")
async def get_live_seoul_info(
    lat: float | None = Query(default=None),
    lng: float | None = Query(default=None),
    station: str | None = Query(default=None),
    destination: str | None = Query(default=None),
):
    data = _build_live_seoul_summary(
        lat=lat,
        lng=lng,
        station_name=station,
        destination_name=destination,
    )
    return data

# --- Static Files (Frontend) ---
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_front", "out")

if os.path.exists(FRONTEND_BUILD_DIR):
    # [Fix] Explicitly set MIME types for Windows Server compatibility
    import mimetypes
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("text/css", ".css")
    mimetypes.add_type("image/svg+xml", ".svg")
    
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD_DIR, html=True), name="static")
else:
    @app.get("/")
    def read_root():
        return {"status": "Frontend build not found. Please run 'npm run build' in temp_front."}

if __name__ == "__main__":
    import uvicorn
    # Use use_colors=False to fix ANSI escape sequences on Windows CMD
    uvicorn.run(app, host="0.0.0.0", port=8000, use_colors=False)


