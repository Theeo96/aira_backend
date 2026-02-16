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
from datetime import datetime
from zoneinfo import ZoneInfo
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
from modules.cosmos_db import cosmos_service
from modules.memory import memory_service
from modules.seoul_info_module import build_seoul_info_packet, build_speech_summary
from modules.news_agent import NewsAgent
from modules.gmail_alert_module import GmailAlertModule
from modules.gmail_alert_runner import run_gmail_alert_loop
from modules.intent_router import IntentRouter
from modules.seoul_live_service import SeoulLiveService
from modules.vision_service import VisionService
from modules.news_context_service import NewsContextService
from modules.timer_service import TimerService
from modules.proactive_service import ProactiveService
from modules.ws_orchestrator_service import WsOrchestratorService

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
CAMERA_FRAME_MIN_INTERVAL_SEC = float(os.getenv("CAMERA_FRAME_MIN_INTERVAL_SEC", "1.0"))
VISION_SNAPSHOT_TTL_SEC = float(os.getenv("VISION_SNAPSHOT_TTL_SEC", "120"))
ENV_CACHE_TTL_SEC = float(os.getenv("ENV_CACHE_TTL_SEC", "300"))

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
STT_SEGMENTATION_SILENCE_TIMEOUT_MS = os.getenv("STT_SEGMENTATION_SILENCE_TIMEOUT_MS", "280")
GMAIL_POLL_INTERVAL_SEC = float(os.getenv("GMAIL_POLL_INTERVAL_SEC", "60"))
GMAIL_ALERT_BIND_USER = os.getenv("GMAIL_ALERT_BIND_USER", "true").strip().lower() in {"1", "true", "yes", "on"}
GMAIL_IDLE_TIMEOUT_SEC = float(os.getenv("GMAIL_IDLE_TIMEOUT_SEC", "120"))
GMAIL_LIVE_POLL_FALLBACK_SEC = float(os.getenv("GMAIL_LIVE_POLL_FALLBACK_SEC", "20"))
print(f"[Config] ENABLE_TRANSIT_FILLER={ENABLE_TRANSIT_FILLER}")
print(f"[Config] GEMINI_DIRECT_AUDIO_INPUT={GEMINI_DIRECT_AUDIO_INPUT}")

try:
    NEWS_AGENT = NewsAgent()
except Exception as e:
    NEWS_AGENT = None
    print(f"[News] NewsAgent init failed: {e}")

news_context_service = NewsContextService(news_agent=NEWS_AGENT, log=print)
ws_orchestrator = WsOrchestratorService()

try:
    GMAIL_ALERT = GmailAlertModule()
except Exception as e:
    GMAIL_ALERT = None
    print(f"[GmailAlert] init failed: {e}")


intent_router = None


def _now_kst_text():
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    return now.strftime("%Y-%m-%d %H:%M:%S")


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


intent_router = IntentRouter(
    api_key=AZURE_OPENAI_API_KEY,
    endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION,
    model=INTENT_ROUTER_MODEL,
    destination_extractor=_extract_destination_from_text,
)


def _extract_news_topic_from_text(text: str):
    return news_context_service.extract_topic(text)


def _get_news_headlines(topic: str | None, limit: int = 3):
    return news_context_service.get_headlines(topic=topic, limit=limit)


def _get_news_items(topic: str | None, limit: int = 3):
    return news_context_service.get_items(topic=topic, limit=limit)


def _is_news_detail_query(text: str) -> bool:
    return news_context_service.is_detail_query(text)


def _is_news_followup_query(text: str) -> bool:
    return news_context_service.is_followup_query(text)


def _select_news_item_by_text(text: str, items: list[dict]):
    return news_context_service.select_item_by_text(text=text, items=items)


def _build_news_detail_summary(item: dict) -> str:
    return news_context_service.build_detail_summary(item)


def _is_vision_related_query(text: str) -> bool:
    t = str(text or "")
    if not t:
        return False
    keywords = [
        "화면", "보여", "보이", "보여줘", "사진", "이미지", "이거", "저거",
        "무엇", "뭐야", "무슨", "읽어", "글자", "문서", "차트", "표", "슬라이드",
        "색", "옷", "어울려", "보이는", "scene", "screen", "image", "what do you see",
    ]
    return any(k in t.lower() for k in keywords)


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


def _get_weather_only(lat: float, lng: float):
    weather = {}
    w_url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urllib.parse.urlencode(
            {
                "latitude": lat,
                "longitude": lng,
                "current": "temperature_2m,precipitation,rain,cloud_cover,weather_code",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": 1,
                "timezone": "Asia/Seoul",
            }
        )
    )
    w = _http_get_json(w_url, timeout=6)
    if isinstance(w, dict):
        cur = w.get("current", {}) if isinstance(w.get("current"), dict) else {}
        daily = w.get("daily", {}) if isinstance(w.get("daily"), dict) else {}
        daily_max = daily.get("temperature_2m_max") if isinstance(daily.get("temperature_2m_max"), list) else []
        daily_min = daily.get("temperature_2m_min") if isinstance(daily.get("temperature_2m_min"), list) else []
        daily_pop = daily.get("precipitation_probability_max") if isinstance(daily.get("precipitation_probability_max"), list) else []
        cloud_cover = _to_float(cur.get("cloud_cover"))
        weather_code = _to_int(cur.get("weather_code"))
        is_cloudy = (cloud_cover is not None and cloud_cover >= 60) or (weather_code in {2, 3, 45, 48} if weather_code is not None else False)
        weather = {
            "tempC": _to_float(cur.get("temperature_2m")),
            "precipitationMm": _to_float(cur.get("precipitation")),
            "rainMm": _to_float(cur.get("rain")),
            "cloudCoverPct": cloud_cover,
            "weatherCode": weather_code,
            "isCloudy": bool(is_cloudy),
            "skyText": "흐림" if is_cloudy else "대체로 맑음",
            "todayMaxC": _to_float(daily_max[0]) if daily_max else None,
            "todayMinC": _to_float(daily_min[0]) if daily_min else None,
            "precipProbPct": _to_int(daily_pop[0]) if daily_pop else None,
            "fetchedAtTs": int(time.time()),
        }
    return weather

def _get_air_only(lat: float, lng: float):
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
        us_aqi = _to_int(cur.get("us_aqi"))
        grade = None
        if us_aqi is not None:
            if us_aqi <= 50:
                grade = "좋음"
            elif us_aqi <= 100:
                grade = "보통"
            elif us_aqi <= 150:
                grade = "민감군 주의"
            elif us_aqi <= 200:
                grade = "나쁨"
            else:
                grade = "매우 나쁨"
        air = {
            "usAqi": us_aqi,
            "pm10": _to_float(cur.get("pm10")),
            "pm25": _to_float(cur.get("pm2_5")),
            "grade": grade,
            "fetchedAtTs": int(time.time()),
        }
    return air

def _get_weather_and_air(lat: float, lng: float):
    weather = _get_weather_only(lat, lng)
    air = _get_air_only(lat, lng)
    return weather, air


def _is_env_cache_fresh(env_cache: dict | None, lat: float | None, lng: float | None) -> bool:
    if not isinstance(env_cache, dict):
        return False
    ts = float(env_cache.get("ts") or 0.0)
    if ts <= 0:
        return False
    if (time.monotonic() - ts) > ENV_CACHE_TTL_SEC:
        return False
    cache_lat = _to_float(env_cache.get("lat"))
    cache_lng = _to_float(env_cache.get("lng"))
    if lat is None or lng is None or cache_lat is None or cache_lng is None:
        return True
    # If user moved materially, refresh cache.
    return _haversine_meters(cache_lat, cache_lng, lat, lng) < 200


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


seoul_live_service = SeoulLiveService(
    default_destination=COMMUTE_DEFAULT_DESTINATION,
    normalize_place_name=_normalize_place_name,
    build_live_summary=_build_live_seoul_summary,
    get_weather_only=_get_weather_only,
    get_air_only=_get_air_only,
    get_weather_and_air=_get_weather_and_air,
    is_env_cache_fresh=_is_env_cache_fresh,
    extract_news_topic=_extract_news_topic_from_text,
    get_news_headlines=_get_news_headlines,
    get_news_items=_get_news_items,
)


def _execute_tools_for_intent(
    intent: str,
    lat: float | None,
    lng: float | None,
    destination_name: str | None,
    env_cache: dict | None = None,
    user_text: str | None = None,
):
    return seoul_live_service.execute_tools_for_intent(
        intent=intent,
        lat=lat,
        lng=lng,
        destination_name=destination_name,
        env_cache=env_cache,
        user_text=user_text,
    )

# --- Helper: Azure STT Setup ---
def create_push_stream(sample_rate=16000):
    stream_format = speechsdk.audio.AudioStreamFormat(samples_per_second=sample_rate, bits_per_sample=16, channels=1)
    push_stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
    audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
    return push_stream, audio_config

def create_recognizer(audio_config, language="en-US"): # Default to English for now, or use "ko-KR"
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_recognition_language = language
    # Too-low timeout harms Korean phrase stability. Use tunable default.
    speech_config.set_property(
        speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs,
        str(STT_SEGMENTATION_SILENCE_TIMEOUT_MS),
    )
    
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
    env_cache = {"weather": {}, "air": {}, "lat": current_lat, "lng": current_lng, "ts": 0.0}
    news_state = {"topic": "", "items": [], "selected": None, "ts": 0.0}

    # Inject Memory into System Instruction
    system_instruction = (
        "You are Aira, a warm and practical Korean voice assistant. "
        "For transit/city/weather/air-quality/news topics, never fabricate facts. "
        "Only state information that is explicitly present in provided live context. "
        "If required data is missing, say what is missing and ask one concise follow-up question. "
        "For subway guidance, include departure station, line/direction, ETA, walking minutes, and whether to take current or next train only when present in live context. "
        "For bus guidance, provide bus number, boarding stop name, and walking minutes when present in live context. "
        "Do not invent route, direction, ETA, weather, or air-quality values. "
        "Do not mention crowding/congestion unless explicit congestion data is provided in live context. "
        "For Korean transit questions, never ask user's current location; device coordinates are already provided by server. "
        "If visual context is provided from camera/screen, use it naturally together with voice context. "
        "When visual context is available, do not say phrases like '보내주신 이미지', '사진에서', "
        "'실시간 화면을 볼 수 없다'. Refer naturally to the current screen "
        "(e.g., '지금 화면에서 ...')."
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
    vision_service = VisionService(
        min_interval_sec=CAMERA_FRAME_MIN_INTERVAL_SEC,
        snapshot_ttl_sec=VISION_SNAPSHOT_TTL_SEC,
        log=print,
    )
    dynamic_contexts = []
    dynamic_context_lock = asyncio.Lock()
    session_ref = {"obj": None}
    
    # Track Full Transcript for Summarization
    session_transcript = []
    route_dedupe = {"text": "", "ts": 0.0}
    timer_set_dedupe = {"key": "", "ts": 0.0}
    user_activity = {"last_user_ts": time.monotonic()}
    transit_turn_gate = {"until": 0.0}
    speech_capture_gate = {"until": 0.0}
    response_guard = {
        "active": False,
        "context_sent": False,
        "suppressed_audio_seen": False,
        "block_direct_audio": False,
        "block_direct_audio_until": 0.0,
        "forced_intent_turn": None,
    }

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

    proactive_service = ProactiveService(
        response_guard=response_guard,
        transit_turn_gate=transit_turn_gate,
        inject_live_context_now=_inject_live_context_now,
        log=print,
    )

    def _reset_response_gate(reason: str = ""):
        proactive_service.reset_response_gate(reason)

    async def _request_spoken_response_with_context(
        intent_tag: str,
        context_summary: str,
        action_instruction: str,
        tone: str = "neutral",
        style: str = "",
        complete_turn: bool = True,
    ):
        await proactive_service.request_spoken_response_with_context(
            intent_tag=intent_tag,
            context_summary=context_summary,
            action_instruction=action_instruction,
            tone=tone,
            style=style,
            complete_turn=complete_turn,
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

    async def _send_proactive_announcement(
        summary_text: str,
        tone: str = "neutral",
        style: str = "",
        add_followup_hint: bool = True,
    ):
        await proactive_service.send_proactive_announcement(
            summary_text=summary_text,
            tone=tone,
            style=style,
            add_followup_hint=add_followup_hint,
        )

    async def _on_timer_fired(delay_sec: int):
        if delay_sec >= 60:
            amount = max(1, delay_sec // 60)
            unit = "분"
        else:
            amount = delay_sec
            unit = "초"
        await _send_proactive_announcement(
            f"요청하신 {amount}{unit}이 지났어요. 다시 이야기할까요?",
            tone="neutral",
            add_followup_hint=False,
        )

    timer_service = TimerService(
        on_fire=_on_timer_fired,
        log=print,
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

    async def _preload_env_cache(force: bool = False):
        lat = client_state.get("lat")
        lng = client_state.get("lng")
        if lat is None or lng is None:
            return
        fresh = _is_env_cache_fresh(env_cache, lat, lng)
        if fresh and not force:
            return
        try:
            weather, air = await asyncio.to_thread(_get_weather_and_air, lat, lng)
            env_cache["weather"] = weather or {}
            env_cache["air"] = air or {}
            env_cache["lat"] = lat
            env_cache["lng"] = lng
            env_cache["ts"] = time.monotonic()
            print(
                f"[SeoulInfo] Env cache refreshed: "
                f"weather={bool(env_cache['weather'])}, air={bool(env_cache['air'])}"
            )
        except Exception as e:
            print(f"[SeoulInfo] Env cache refresh failed: {e}")

    # STT Event Handlers
    def on_recognized(args, role):
        if args.result.text:
            text = args.result.text
            print(f"[STT] {role}: {text}")
            
            # Store for memory
            session_transcript.append(f"{role.upper()}: {text}")

            if role == "user":
                try:
                    user_activity["last_user_ts"] = time.monotonic()
                    speech_capture_gate["until"] = max(
                        float(speech_capture_gate.get("until") or 0.0),
                        time.monotonic() + 1.0,
                    )
                    now_text = _now_kst_text()
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            _inject_live_context_now(
                                f"[INTENT:time_context] Current Seoul time is {now_text} (KST, Asia/Seoul). Use this as 'now'.",
                                complete_turn=False,
                            ),
                            loop,
                        )

                    snapshot_bytes = vision_service.get_recent_snapshot_for_query(
                        text,
                        _is_vision_related_query,
                    )
                    if snapshot_bytes and loop.is_running():
                            asyncio.run_coroutine_threadsafe(
                                vision_service.send_frame_to_gemini(
                                    session_ref=session_ref,
                                    inject_live_context_now=_inject_live_context_now,
                                    image_bytes=snapshot_bytes,
                                    mime_type="image/jpeg",
                                ),
                                loop,
                            )
                            asyncio.run_coroutine_threadsafe(
                                _inject_live_context_now(
                                    "[VISION] Recent visual context is available for this turn. "
                                    "Use visual context if relevant.",
                                    complete_turn=False,
                                ),
                                loop,
                            )

                    normalized_user_text = re.sub(r"[\s\W_]+", "", str(text or ""))
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

                    route = intent_router.route(text, active_timer=timer_service.has_active())
                    intent = route.get("intent") if isinstance(route, dict) else "commute_overview"
                    routed_dest = route.get("destination") if isinstance(route, dict) else None
                    routed_home_update = bool(route.get("home_update")) if isinstance(route, dict) else False
                    routed_timer_seconds = route.get("timer_seconds") if isinstance(route, dict) else None
                    route_source = route.get("source") if isinstance(route, dict) else "fallback"
                    print(
                        f"[IntentRouter] source={route_source}, intent={intent}, "
                        f"destination={routed_dest}, home_update={routed_home_update}, "
                        f"timer_seconds={routed_timer_seconds}"
                    )
                    if intent == "timer_cancel" and (not timer_service.has_active()):
                        # Timer cancel intent is only meaningful while a timer is active.
                        intent = "general"
                    if intent == "timer_cancel" and timer_service.has_active():
                        canceled = timer_service.cancel_all()
                        asyncio.run_coroutine_threadsafe(
                            _inject_live_context_now(
                                f"[INTENT:timer_canceled] Canceled {canceled} active timer(s). "
                                "Acknowledge cancellation briefly in Korean, then answer the user's current request directly.",
                                complete_turn=True,
                            ),
                            loop,
                        )
                        # Let the same user utterance proceed naturally after cancel notice.
                        # Do not run live-tool routing for this branch.
                        return
                    if intent == "timer" and loop.is_running():
                        timer_sec = None
                        try:
                            timer_sec = int(routed_timer_seconds) if routed_timer_seconds is not None else None
                        except Exception:
                            timer_sec = None
                        if timer_sec is not None and 5 <= timer_sec <= 21600:
                            # Prevent duplicate "timer set" responses from near-duplicate STT finalization.
                            timer_key = f"{timer_sec}:{normalized_user_text}"
                            now_timer_ts = time.monotonic()
                            if (
                                timer_key
                                and timer_key == str(timer_set_dedupe.get("key") or "")
                                and (now_timer_ts - float(timer_set_dedupe.get("ts") or 0.0)) < 2.5
                            ):
                                print(f"[Timer] duplicate timer_set skipped: {timer_sec}s")
                                return
                            timer_set_dedupe["key"] = timer_key
                            timer_set_dedupe["ts"] = now_timer_ts

                            # Block stale parallel model response from the raw audio turn.
                            response_guard["active"] = True
                            response_guard["context_sent"] = True
                            response_guard["suppressed_audio_seen"] = False
                            response_guard["block_direct_audio"] = True
                            response_guard["block_direct_audio_until"] = max(
                                float(response_guard.get("block_direct_audio_until") or 0.0),
                                time.monotonic() + 1.4,
                            )
                            transit_turn_gate["until"] = max(
                                float(transit_turn_gate.get("until") or 0.0),
                                time.monotonic() + 1.1,
                            )
                            asyncio.run_coroutine_threadsafe(
                                timer_service.register(timer_sec),
                                loop,
                            )
                            print(f"[Timer] timer_set accepted: {timer_sec}s")
                        else:
                            print("[Timer] timer_set rejected: invalid timer_seconds")
                        return

                    # News detail/follow-up inference from recently fetched news items.
                    has_recent_news = (
                        bool(news_state.get("items"))
                        and (now_ts - float(news_state.get("ts") or 0.0)) < 900
                    )
                    if has_recent_news and intent in {"general", "news"}:
                        wants_detail = _is_news_detail_query(text)
                        wants_followup = _is_news_followup_query(text)
                        if wants_detail or wants_followup:
                            matched_item = _select_news_item_by_text(
                                text=text,
                                items=(news_state.get("items") or []),
                            )
                            if matched_item is None and wants_followup:
                                matched_item = news_state.get("selected")
                            if matched_item is not None:
                                news_state["selected"] = matched_item
                                intent = "news_detail" if wants_detail else "news_followup"

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
                    routing_intents = ws_orchestrator.ROUTING_INTENTS
                    should_inject_live = intent in routing_intents

                    if should_inject_live:
                        # Always gate response until live context is injected to prevent pre-context utterances.
                        ws_orchestrator.arm_live_response_gate(
                            response_guard=response_guard,
                            transit_turn_gate=transit_turn_gate,
                            intent=intent,
                        )
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
                        transit_intents = ws_orchestrator.TRANSIT_INTENTS
                        context_destination = destination_state["name"] if intent in transit_intents else None
                        if intent in {"news_detail", "news_followup"}:
                            picked = news_state.get("selected")
                            if picked is None and news_state.get("items"):
                                picked = _select_news_item_by_text(text=text, items=(news_state.get("items") or []))
                            if picked is None and news_state.get("items"):
                                picked = (news_state.get("items") or [None])[0]
                            if picked is not None:
                                news_state["selected"] = picked
                            detail_summary = _build_news_detail_summary(picked) if picked else "먼저 최신 뉴스를 불러온 뒤에, 관심 있는 키워드를 말해주시면 자세히 설명해드릴게요."
                            live_data = {
                                "speechSummary": detail_summary,
                                "news": {
                                    "topic": news_state.get("topic") or "",
                                    "headlines": [str(i.get("title") or "").strip() for i in (news_state.get("items") or []) if isinstance(i, dict)],
                                    "items": news_state.get("items") or [],
                                    "selected": picked,
                                },
                            }
                        else:
                            live_data = _execute_tools_for_intent(
                                intent=intent or "commute_overview",
                                lat=client_state.get("lat"),
                                lng=client_state.get("lng"),
                                destination_name=context_destination,
                                env_cache=env_cache,
                                user_text=text,
                            )
                        live_summary = live_data.get("speechSummary") if isinstance(live_data, dict) else None
                        if intent == "news":
                            news_meta = live_data.get("news") if isinstance(live_data, dict) else None
                            if isinstance(news_meta, dict):
                                news_state["topic"] = str(news_meta.get("topic") or "").strip()
                                items = news_meta.get("items") or []
                                if isinstance(items, list):
                                    news_state["items"] = [i for i in items if isinstance(i, dict)]
                                else:
                                    news_state["items"] = []
                                news_state["selected"] = None
                                news_state["ts"] = time.monotonic()
                        print(
                            f"[SeoulInfo] live context built: intent={intent}, destination={context_destination}, "
                            f"summary_ok={bool(live_summary)}"
                        )

                        guidance = []
                        if client_state.get("lat") is not None and client_state.get("lng") is not None:
                            guidance.append("Location is known; do not ask user's current location.")
                        if intent in transit_intents and destination_state.get("name"):
                            guidance.append(
                                f"Use destination '{destination_state['name']}' for this turn and ignore older destination context."
                            )
                        if (
                            not destination_state.get("name")
                            and intent in transit_intents
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

                        context_priority_intents = ws_orchestrator.CONTEXT_PRIORITY_INTENTS
                        context_summary = ws_orchestrator.merge_context_summary(
                            live_summary=live_summary,
                            guidance=guidance,
                        )
                        action_instruction = ws_orchestrator.build_action_instruction(intent)

                        if intent in context_priority_intents:
                            # Keep gate a little longer while response turn is being finalized.
                            ws_orchestrator.extend_post_context_gate(transit_turn_gate)

                        if loop.is_running():
                            asyncio.run_coroutine_threadsafe(
                                _request_spoken_response_with_context(
                                    intent_tag=(intent or "commute_overview"),
                                    context_summary=context_summary,
                                    action_instruction=action_instruction,
                                    tone="neutral",
                                    complete_turn=(intent in context_priority_intents),
                                ),
                                loop,
                            )
                            response_guard["context_sent"] = True
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

    def on_recognizing(args, role):
        if role != "user":
            return
        text = str(getattr(args.result, "text", "") or "").strip()
        if not text:
            return
        now_ts = time.monotonic()
        user_activity["last_user_ts"] = now_ts
        # Gate early model audio while user speech is being finalized by STT.
        speech_capture_gate["until"] = max(float(speech_capture_gate.get("until") or 0.0), now_ts + 1.2)
        # Also hard-block direct audio briefly to avoid stale pre-context model turns.
        response_guard["block_direct_audio"] = True
        response_guard["block_direct_audio_until"] = max(
            float(response_guard.get("block_direct_audio_until") or 0.0),
            now_ts + 1.5,
        )

    user_recognizer.recognized.connect(lambda evt: on_recognized(evt, "user"))
    ai_recognizer.recognized.connect(lambda evt: on_recognized(evt, "ai"))
    user_recognizer.recognizing.connect(lambda evt: on_recognizing(evt, "user"))

    user_recognizer.start_continuous_recognition()
    ai_recognizer.start_continuous_recognition()

    try:
        async with client.aio.live.connect(model=MODEL_NAME, config=config) as session:
            print("[Gemini] Connected to Live API")
            session_ref["obj"] = session
            await _preload_env_cache(force=True)
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
                                        # Refresh cached weather/air in background when movement is meaningful.
                                        if moved_m is None or moved_m >= 80:
                                            asyncio.create_task(_preload_env_cache(force=False))
                                elif isinstance(payload, dict) and payload.get("type") == "camera_state":
                                    await vision_service.set_camera_enabled(
                                        enabled=bool(payload.get("enabled")),
                                        inject_live_context_now=_inject_live_context_now,
                                    )
                                elif isinstance(payload, dict) and payload.get("type") == "camera_frame_base64":
                                    await vision_service.handle_camera_frame_payload(
                                        payload=payload,
                                        session_ref=session_ref,
                                        inject_live_context_now=_inject_live_context_now,
                                    )
                                elif isinstance(payload, dict) and payload.get("type") == "camera_snapshot_base64":
                                    await vision_service.handle_camera_snapshot_payload(
                                        payload=payload,
                                        session_ref=session_ref,
                                        inject_live_context_now=_inject_live_context_now,
                                    )
                            except Exception:
                                pass
                            continue

                        data = msg.get("bytes")
                        # Ignore non-binary frames (e.g., text/control keepalive)
                        if not data:
                            continue

                        # Safety release: if timed block elapsed, release hard block flag.
                        if (
                            response_guard.get("block_direct_audio")
                            and time.monotonic() >= float(response_guard.get("block_direct_audio_until") or 0.0)
                        ):
                            response_guard["block_direct_audio"] = False

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
                                # Live context was pushed; release output/input gate quickly
                                # so user does not feel unnecessary latency.
                                transit_turn_gate["until"] = min(
                                    float(transit_turn_gate.get("until") or 0.0),
                                    time.monotonic() + 0.15,
                                )
                            except Exception as e:
                                print(f"[SeoulInfo] context injection failed: {e}")
                        if (
                            GEMINI_DIRECT_AUDIO_INPUT
                            and (not response_guard.get("block_direct_audio"))
                            and time.monotonic() >= float(response_guard.get("block_direct_audio_until") or 0.0)
                            and time.monotonic() >= float(transit_turn_gate.get("until") or 0.0)
                        ):
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
                                        # Drop model audio during user speech capture/finalization window.
                                        if time.monotonic() < float(speech_capture_gate.get("until") or 0.0):
                                            continue
                                        # Suppress premature model audio while live-context turn is being prepared.
                                        if time.monotonic() < float(transit_turn_gate.get("until") or 0.0):
                                            if response_guard.get("active"):
                                                response_guard["suppressed_audio_seen"] = True
                                            continue
                                        # Drop any model audio before live context is sent for this guarded turn.
                                        if response_guard.get("active") and (not response_guard.get("context_sent")):
                                            response_guard["suppressed_audio_seen"] = True
                                            continue
                                        # If we already saw suppressed audio before context turn was ready,
                                        # keep dropping until the stale turn completes.
                                        if (
                                            response_guard.get("active")
                                            and response_guard.get("context_sent")
                                            and response_guard.get("suppressed_audio_seen")
                                        ):
                                            continue
                                        await ws.send_bytes(audio_bytes)
                                        # [Fix] Offload AI audio write to thread
                                        await asyncio.to_thread(ai_push_stream.write, audio_bytes)
                                        # Update state: Audio received, not flushed yet
                                        state["last_ai_write_time"] = asyncio.get_running_loop().time()
                                        state["flushed"] = False
                            
                            # [Fix 3] Monitor Gemini Turn Complete
                            if response.server_content and response.server_content.turn_complete:
                                if (
                                    response_guard.get("active")
                                    and response_guard.get("context_sent")
                                    and response_guard.get("suppressed_audio_seen")
                                ):
                                    # Stale pre-context turn ended; allow the next turn through.
                                    response_guard["suppressed_audio_seen"] = False
                                    response_guard["active"] = False
                                    response_guard["block_direct_audio"] = False
                                    response_guard["block_direct_audio_until"] = 0.0
                                    response_guard["forced_intent_turn"] = None
                                elif response_guard.get("active") and response_guard.get("context_sent"):
                                    # No stale audio detected; normal guarded turn complete.
                                    response_guard["active"] = False
                                    response_guard["block_direct_audio"] = False
                                    response_guard["block_direct_audio_until"] = 0.0
                                    response_guard["forced_intent_turn"] = None

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
            tasks = [
                asyncio.create_task(receive_from_client()),
                asyncio.create_task(send_to_client()),
                asyncio.create_task(smart_flush_injector()),
            ]
            if GMAIL_ALERT and GMAIL_ALERT.enabled:
                tasks.append(
                    asyncio.create_task(
                        run_gmail_alert_loop(
                            gmail_alert=GMAIL_ALERT,
                            user_id=user_id,
                            bind_user=GMAIL_ALERT_BIND_USER,
                            idle_timeout_sec=GMAIL_IDLE_TIMEOUT_SEC,
                            live_poll_fallback_sec=GMAIL_LIVE_POLL_FALLBACK_SEC,
                            user_activity=user_activity,
                            response_guard=response_guard,
                            send_proactive_announcement=_send_proactive_announcement,
                            log=print,
                        )
                    )
                )
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending: task.cancel()

    except Exception as e:
        print(f"[Server] Session Error or Disconnect: {e}")
    finally:
        # Cleanup
        session_ref["obj"] = None
        if GMAIL_ALERT and GMAIL_ALERT.enabled:
            try:
                await asyncio.to_thread(GMAIL_ALERT.end_session, user_id, time.time())
            except Exception as e:
                print(f"[GmailAlert] end_session failed: {e}")
        print("[Server] Cleaning up resources...")
        await timer_service.shutdown()
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


