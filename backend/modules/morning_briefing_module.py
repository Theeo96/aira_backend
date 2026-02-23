import json
import math
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from dotenv import dotenv_values

from .news_agent import NewsAgent
from .tmap_service import TmapService

KST = ZoneInfo("Asia/Seoul")


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _to_int(value: Any) -> int | None:
    try:
        return int(float(value))
    except Exception:
        return None


def _http_get_json(url: str, timeout: int = 6) -> dict[str, Any] | None:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
        return json.loads(body)
    except Exception:
        return None


def _haversine_meters(a: dict[str, float], b: dict[str, float]) -> float:
    lat1, lon1 = float(a["lat"]), float(a["lng"])
    lat2, lon2 = float(b["lat"]), float(b["lng"])
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    s = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * (2 * math.atan2(math.sqrt(s), math.sqrt(1 - s)))


@dataclass
class BriefingConfig:
    profile_path: str = "backend/data/user_profile.json"
    test_config_path: str = "backend/data/test_config.json"
    test_mode: bool = False


class MorningBriefingModule:
    def __init__(self, news_agent: NewsAgent | None = None, log=print):
        self.log = log
        self.news_agent = news_agent
        self.tmap = TmapService(os.getenv("TMAP_APP_KEY"), log=log)
        self.odsay_key = str(os.getenv("ODSAY_API_KEY") or "").strip()
        self.project_root = Path(__file__).resolve().parents[2]

        raw_profile_path = os.getenv("BRIEFING_PROFILE_PATH", "backend/data/user_profile.json")
        raw_test_config_path = os.getenv("BRIEFING_TEST_CONFIG", "backend/data/test_config.json")
        self.config = BriefingConfig(
            profile_path=str(self._resolve_path(raw_profile_path)),
            test_config_path=str(self._resolve_path(raw_test_config_path)),
            test_mode=False,
        )

    def _normalize_mode(self, raw_mode: Any, default: str = "live") -> str:
        mode = str(raw_mode or "").strip().lower()
        if mode in {"off", "live", "test"}:
            return mode
        return default

    def _read_dotenv_runtime(self) -> dict[str, str]:
        env_path = self.project_root / ".env"
        try:
            values = dotenv_values(str(env_path))
            return {str(k): str(v) for k, v in values.items() if k and v is not None}
        except Exception:
            return {}

    def _get_runtime_env(self, key: str, default: str) -> str:
        file_env = self._read_dotenv_runtime()
        if key in file_env:
            return str(file_env.get(key) or default)
        return str(os.getenv(key, default))

    def _get_phase_mode(self, phase: str) -> str:
        phase_key_map = {
            "wake_up": "BRIEFING_MODE_WAKE_UP",
            "leave_home": "BRIEFING_MODE_LEAVE_HOME",
            "leave_office": "BRIEFING_MODE_LEAVE_OFFICE",
        }
        env_key = phase_key_map.get(str(phase or "").strip())
        if not env_key:
            return "live"
        return self._normalize_mode(self._get_runtime_env(env_key, "live"), default="live")

    def _refresh_runtime_config(self):
        raw_profile_path = self._get_runtime_env("BRIEFING_PROFILE_PATH", "backend/data/user_profile.json")
        raw_test_config_path = self._get_runtime_env("BRIEFING_TEST_CONFIG", "backend/data/test_config.json")
        modes = {
            self._get_phase_mode("wake_up"),
            self._get_phase_mode("leave_home"),
            self._get_phase_mode("leave_office"),
        }
        self.config.profile_path = str(self._resolve_path(raw_profile_path))
        self.config.test_config_path = str(self._resolve_path(raw_test_config_path))
        self.config.test_mode = "test" in modes

    def _resolve_path(self, raw_path: str) -> Path:
        p = Path(str(raw_path or "").strip())
        if p.is_absolute():
            return p
        candidate = (self.project_root / p).resolve()
        if candidate.exists():
            return candidate
        return p.resolve()

    def _load_json(self, path: str) -> dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            self.log(f"[MorningBriefing] load failed: {path} ({e})")
            return {}

    def _resolve_context(self) -> tuple[dict[str, Any], dict[str, Any] | None]:
        self._refresh_runtime_config()
        profile = self._load_json(self.config.profile_path)
        test_cfg = self._load_json(self.config.test_config_path)
        return profile, test_cfg

    def _section(self, test_cfg: dict[str, Any] | None, key: str) -> dict[str, Any]:
        if not isinstance(test_cfg, dict):
            return {}
        v = test_cfg.get(key)
        return v if isinstance(v, dict) else {}

    def _parse_iso(self, value: Any, fallback: datetime) -> datetime:
        text = str(value or "").strip()
        if not text:
            return fallback
        try:
            dt = datetime.fromisoformat(text.replace(" ", "T"))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=KST)
            return dt.astimezone(KST)
        except Exception:
            return fallback

    def _coord(self, raw: dict[str, Any] | None) -> dict[str, float] | None:
        if not isinstance(raw, dict):
            return None
        lat = _to_float(raw.get("lat"))
        lng = _to_float(raw.get("lng"))
        if lat is None or lng is None:
            return None
        return {"lat": float(lat), "lng": float(lng)}

    def _weather_from_raw(self, raw: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(raw, dict):
            return {}
        return {
            "temperature": _to_float(raw.get("temperature")),
            "condition_code": _to_int(raw.get("condition_code")),
            "precipitation_probability": _to_int(raw.get("precipitation_probability")),
            "rain_mm": _to_float(raw.get("rain_mm")),
            "today_max": _to_float(raw.get("today_max")),
            "today_min": _to_float(raw.get("today_min")),
        }

    def _fetch_weather(self, lat: float, lng: float) -> dict[str, Any]:
        url = (
            "https://api.open-meteo.com/v1/forecast?"
            + urllib.parse.urlencode(
                {
                    "latitude": lat,
                    "longitude": lng,
                    "current": "temperature_2m,precipitation,rain,weather_code",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                    "timezone": "Asia/Seoul",
                    "forecast_days": 1,
                }
            )
        )
        raw = _http_get_json(url)
        if not isinstance(raw, dict):
            return {}
        cur = raw.get("current", {}) if isinstance(raw.get("current"), dict) else {}
        daily = raw.get("daily", {}) if isinstance(raw.get("daily"), dict) else {}
        pop_arr = daily.get("precipitation_probability_max") if isinstance(daily.get("precipitation_probability_max"), list) else []
        tmax_arr = daily.get("temperature_2m_max") if isinstance(daily.get("temperature_2m_max"), list) else []
        tmin_arr = daily.get("temperature_2m_min") if isinstance(daily.get("temperature_2m_min"), list) else []
        return {
            "temperature": _to_float(cur.get("temperature_2m")),
            "condition_code": _to_int(cur.get("weather_code")),
            "precipitation_probability": _to_int(pop_arr[0]) if pop_arr else None,
            "rain_mm": _to_float(cur.get("rain")),
            "today_max": _to_float(tmax_arr[0]) if tmax_arr else None,
            "today_min": _to_float(tmin_arr[0]) if tmin_arr else None,
        }
    def _fetch_odsay_transit(self, origin: dict[str, float], destination: dict[str, float]) -> dict[str, Any]:
        if not self.odsay_key:
            return {}
        query = urllib.parse.urlencode(
            {
                "apiKey": self.odsay_key,
                "SX": origin["lng"],
                "SY": origin["lat"],
                "EX": destination["lng"],
                "EY": destination["lat"],
                "SearchPathType": 0,
            }
        )
        data = _http_get_json(f"https://api.odsay.com/v1/api/searchPubTransPathT?{query}")
        if not isinstance(data, dict):
            return {}
        result = data.get("result", {}) if isinstance(data.get("result"), dict) else {}
        paths = result.get("path") if isinstance(result.get("path"), list) else []
        if not paths:
            return {}
        p0 = paths[0] if isinstance(paths[0], dict) else {}
        info = p0.get("info", {}) if isinstance(p0.get("info"), dict) else {}
        sub_path = p0.get("subPath", []) if isinstance(p0.get("subPath"), list) else []
        first_mode = None
        subway_line = None
        boarding_station = None
        for seg in sub_path:
            if not isinstance(seg, dict):
                continue
            t = _to_int(seg.get("trafficType"))
            if t in (1, 2):
                first_mode = "subway" if t == 1 else "bus"
                boarding_station = str(seg.get("startName") or "").strip() or None
                lane = seg.get("lane", [])
                if isinstance(lane, list) and lane and isinstance(lane[0], dict):
                    subway_line = str(lane[0].get("name") or "").strip() or None
                break
        return {
            "estimated_minutes": _to_int(info.get("totalTime")),
            "provider": "odsay",
            "first_mode": first_mode,
            "subway_line": subway_line,
            "boarding_station": boarding_station,
        }

    def _fetch_transit_time(self, origin: dict[str, float], destination: dict[str, float]) -> dict[str, Any]:
        def _norm(raw: Any) -> int | None:
            m = _to_int(raw)
            if m is None or m <= 0:
                return None
            return int(round(m / 60)) if m > 240 else m

        tmap_raw = self.tmap.get_transit_route(origin=origin, destination=destination)
        if isinstance(tmap_raw, dict):
            meta = tmap_raw.get("metaData", {}) if isinstance(tmap_raw.get("metaData"), dict) else {}
            plan = meta.get("plan", {}) if isinstance(meta.get("plan"), dict) else {}
            routes = plan.get("itineraries") if isinstance(plan.get("itineraries"), list) else []
            if routes and isinstance(routes[0], dict):
                m = _norm(routes[0].get("totalTime"))
                if m is not None:
                    return {"estimated_minutes": m, "provider": "tmap"}

        odsay = self._fetch_odsay_transit(origin=origin, destination=destination)
        m = _norm(odsay.get("estimated_minutes"))
        if m is not None:
            odsay["estimated_minutes"] = m
            return odsay
        return odsay

    def _fetch_car_minutes(self, origin: dict[str, float], destination: dict[str, float]) -> int | None:
        route = self.tmap.get_car_route(origin=origin, destination=destination)
        if not isinstance(route, dict):
            return None
        features = route.get("features") if isinstance(route.get("features"), list) else []
        if not features:
            return None
        props = features[0].get("properties") if isinstance(features[0], dict) and isinstance(features[0].get("properties"), dict) else {}
        sec = _to_int(props.get("totalTime"))
        if sec is not None and sec > 0:
            return max(1, int(round(sec / 60)))
        return _to_int(props.get("totalTimeMin"))

    def _extract_district(self, lat: float, lng: float) -> str:
        district = self.tmap.reverse_geocode_district(lat=lat, lng=lng)
        return district if district else "서울"

    def _fetch_news(self, keywords: list[str], max_count: int = 3) -> list[dict[str, Any]]:
        agent = self.news_agent or NewsAgent()
        items: list[dict[str, Any]] = []
        seen = set()
        for kw in keywords:
            try:
                fetched = agent._search_naver_news(str(kw), display=3)
            except Exception as e:
                self.log(f"[MorningBriefing] news fetch failed for '{kw}': {e}")
                fetched = []
            for n in fetched:
                if not isinstance(n, dict):
                    continue
                link = str(n.get("link") or "").strip()
                if link and link in seen:
                    continue
                if link:
                    seen.add(link)
                items.append({"title": str(n.get("title") or "").strip(), "link": link, "pubDate": str(n.get("pubDate") or "").strip()})
        items.sort(key=lambda x: x.get("pubDate", ""), reverse=True)
        return items[:max_count]

    def _fetch_events(self, district: str, max_count: int = 2) -> list[dict[str, Any]]:
        key = str(os.getenv("SEOUL_API_KEY") or os.getenv("Seoul_API") or "").strip()
        if not key:
            return []
        data = _http_get_json(f"http://openapi.seoul.go.kr:8088/{key}/json/culturalEventInfo/1/120/", timeout=6)
        if not isinstance(data, dict):
            return []
        body = data.get("culturalEventInfo", {}) if isinstance(data.get("culturalEventInfo"), dict) else {}
        rows = body.get("row") if isinstance(body.get("row"), list) else []
        picked: list[dict[str, Any]] = []
        k = str(district or "").replace(" ", "")
        for row in rows:
            if not isinstance(row, dict):
                continue
            gu = str(row.get("GUNAME") or "").replace(" ", "")
            if k and gu and (k not in gu and gu not in k):
                continue
            title = str(row.get("TITLE") or "").strip()
            if not title:
                continue
            picked.append({"title": title, "date": str(row.get("DATE") or "").strip(), "place": str(row.get("PLACE") or "").strip()})
            if len(picked) >= max_count:
                break
        return picked

    def normalize_transport_mode(self, mode: Any) -> str:
        raw = str(mode or "").strip().lower()
        if raw in {"car", "drive", "driving", "자가용", "자동차", "택시"}:
            return "car"
        if raw in {"public", "transit", "public_transit", "subway", "bus", "대중교통", "지하철", "버스"}:
            return "public"
        return "public"

    def detect_transport_choice(self, text: str) -> str | None:
        t = str(text or "")
        low = t.lower()
        if "car" in low or "drive" in low or any(k in t for k in ["자가용", "자동차", "택시", "운전"]):
            return "car"
        if "public" in low or "transit" in low or any(k in t for k in ["대중교통", "지하철", "버스"]):
            return "public"
        return None

    def get_transport_prompt_choices(self) -> list[str]:
        return ["대중교통", "자가용"]

    def get_default_transport_mode(self) -> str:
        profile, test_cfg = self._resolve_context()
        mode = self.normalize_transport_mode(profile.get("default_transport_mode"))
        if self._get_phase_mode("wake_up") == "test":
            wake = self._section(test_cfg, "wake_up")
            mode = self.normalize_transport_mode(wake.get("recommended_transport") or mode)
        return mode

    def should_auto_wake_up_in_test(self) -> bool:
        if self._get_phase_mode("wake_up") != "test":
            return False
        _, test_cfg = self._resolve_context()
        ctrl = self._section(test_cfg, "test_control")
        return bool(ctrl.get("auto_wake_up"))

    def is_test_mode(self) -> bool:
        self._refresh_runtime_config()
        return bool(
            self._get_phase_mode("wake_up") == "test"
            or self._get_phase_mode("leave_home") == "test"
            or self._get_phase_mode("leave_office") == "test"
        )

    def is_wake_up_test_mode(self) -> bool:
        return self._get_phase_mode("wake_up") == "test"

    def is_leaving_home_test_mode(self) -> bool:
        return self._get_phase_mode("leave_home") == "test"

    def is_leaving_office_test_mode(self) -> bool:
        return self._get_phase_mode("leave_office") == "test"

    def is_briefing_enabled(self) -> bool:
        return (
            self._get_phase_mode("wake_up") != "off"
            or self._get_phase_mode("leave_home") != "off"
            or self._get_phase_mode("leave_office") != "off"
        )

    def is_wake_up_enabled(self) -> bool:
        return self._get_phase_mode("wake_up") != "off"

    def is_leaving_home_enabled(self) -> bool:
        return self._get_phase_mode("leave_home") != "off"

    def is_leaving_office_enabled(self) -> bool:
        return self._get_phase_mode("leave_office") != "off"

    def is_briefing_api_enabled(self) -> bool:
        return self.is_briefing_enabled()

    def get_briefing_mode(self) -> str:
        modes = {
            self._get_phase_mode("wake_up"),
            self._get_phase_mode("leave_home"),
            self._get_phase_mode("leave_office"),
        }
        return list(modes)[0] if len(modes) == 1 else "mixed"

    def get_wake_up_time(self) -> str:
        profile, test_cfg = self._resolve_context()
        wake = self._section(test_cfg, "wake_up") if self._get_phase_mode("wake_up") == "test" else {}
        val = str(wake.get("alarm_time") or profile.get("wake_up_time") or "07:00").strip()
        return val if val else "07:00"

    def get_evening_trigger_window(self) -> tuple[int, int]:
        profile, test_cfg = self._resolve_context()
        sec = self._section(test_cfg, "leave_office") if self._get_phase_mode("leave_office") == "test" else {}
        start = _to_int(sec.get("window_start_hour")) or _to_int(profile.get("leave_office_window_start_hour")) or 18
        end = _to_int(sec.get("window_end_hour")) or _to_int(profile.get("leave_office_window_end_hour")) or 19
        return (start, end) if start <= end else (end, start)

    def _clothing_tip(self, temp: float | None, pop: int | None) -> str:
        tips = []
        if temp is None:
            tips.append("가벼운 겉옷을 챙기세요.")
        elif temp <= 3:
            tips.append("두꺼운 코트와 목도리를 추천해요.")
        elif temp <= 10:
            tips.append("코트나 자켓이 적당해요.")
        elif temp <= 18:
            tips.append("얇은 겉옷을 챙기면 좋아요.")
        else:
            tips.append("가벼운 차림이 좋아요.")
        if pop is not None and pop >= 50:
            tips.append("우산을 챙기세요.")
        return " ".join(tips)
    def build_wake_up_briefing(self) -> dict[str, Any]:
        phase_mode = self._get_phase_mode("wake_up")
        if phase_mode == "off":
            return {"ok": True, "phase": "wake_up", "triggered": False, "reason": "mode_off"}
        profile, test_cfg = self._resolve_context()
        sec = self._section(test_cfg, "wake_up") if phase_mode == "test" else {}
        now = self._parse_iso(sec.get("mock_now"), datetime.now(KST)) if sec else datetime.now(KST)

        home = self._coord(sec.get("home")) if sec else None
        office = self._coord(sec.get("office")) if sec else None
        home = home or self._coord(profile.get("home"))
        office = office or self._coord(profile.get("office"))
        if not home or not office:
            return {"ok": False, "error": "home/office coordinates are required"}

        weather = self._weather_from_raw(sec.get("weather")) if sec else {}
        if not weather:
            weather = self._fetch_weather(home["lat"], home["lng"])

        transit = sec.get("transit_info") if isinstance(sec.get("transit_info"), dict) else {}
        if not transit:
            transit = self._fetch_transit_time(home, office)
        car_minutes = _to_int((sec.get("car_info") or {}).get("estimated_minutes")) if sec else None
        if car_minutes is None:
            car_minutes = self._fetch_car_minutes(home, office)

        transit_minutes = _to_int(transit.get("estimated_minutes"))
        recommended = self.normalize_transport_mode(sec.get("recommended_transport") if sec else None)
        reason = ""
        if sec and str(sec.get("recommendation_reason") or "").strip():
            reason = str(sec.get("recommendation_reason")).strip()
        else:
            if transit_minutes is None and car_minutes is None:
                recommended, reason = "public", "현재 교통 데이터가 제한적이라 우선 대중교통 기준으로 안내할게요."
            elif transit_minutes is None:
                recommended, reason = "car", f"자가용이 약 {car_minutes}분으로 예상돼요."
            elif car_minutes is None:
                recommended, reason = "public", f"대중교통이 약 {transit_minutes}분으로 예상돼요."
            elif transit_minutes <= car_minutes - 5:
                recommended, reason = "public", f"대중교통 {transit_minutes}분, 자가용 {car_minutes}분으로 대중교통이 더 빨라요."
            elif car_minutes <= transit_minutes - 5:
                recommended, reason = "car", f"자가용 {car_minutes}분, 대중교통 {transit_minutes}분으로 자가용이 더 빨라요."
            else:
                recommended, reason = "public", "두 수단이 비슷하지만 혼잡 리스크를 고려해 대중교통을 추천해요."

        temp = _to_float(weather.get("temperature"))
        pop = _to_int(weather.get("precipitation_probability"))
        parts = ["좋은 아침이에요."]
        if temp is not None:
            parts.append(f"현재 기온은 {int(round(temp))}도입니다.")
        if pop is not None:
            parts.append(f"강수확률은 {pop}%입니다.")
        parts.append(self._clothing_tip(temp, pop))
        if transit_minutes is not None:
            parts.append(f"출근 예상 시간은 대중교통 약 {transit_minutes}분입니다.")
        if car_minutes is not None:
            parts.append(f"자가용은 약 {car_minutes}분입니다.")
        if reason:
            parts.append(reason)
        parts.append("오늘 이동수단은 대중교통과 자가용 중 무엇으로 안내할까요?")

        interest_news = [x for x in (sec.get("interest_news") if isinstance(sec.get("interest_news"), list) else []) if isinstance(x, dict)] if sec else []
        if not interest_news:
            kws = profile.get("interest_keywords") if isinstance(profile.get("interest_keywords"), list) else []
            keywords = [str(x).strip() for x in kws if str(x).strip()] or ["AI", "경제", "서울"]
            interest_news = self._fetch_news(keywords, max_count=3)

        district = str(sec.get("home_district") or "").strip() if sec else ""
        if not district:
            district = self._extract_district(home["lat"], home["lng"])
        events = [x for x in (sec.get("local_events") if isinstance(sec.get("local_events"), list) else []) if isinstance(x, dict)] if sec else []
        local_news = [x for x in (sec.get("local_news") if isinstance(sec.get("local_news"), list) else []) if isinstance(x, dict)] if sec else []
        if not events:
            events = self._fetch_events(district, max_count=2)
        if not local_news:
            local_news = self._fetch_news([district], max_count=2)

        return {
            "ok": True,
            "phase": "wake_up",
            "triggered": True,
            "trigger_time": now.isoformat(),
            "briefing": " ".join([p for p in parts if p]).strip(),
            "weather": weather,
            "commute_public": transit,
            "commute_car": {"estimated_minutes": car_minutes, "provider": "tmap" if car_minutes else None},
            "recommended_transport": recommended,
            "ask_transport_choice": True,
            "transport_choices": self.get_transport_prompt_choices(),
            "interest_news": interest_news,
            "local_issue": {"events": events, "local_news": local_news},
            "home_district": district,
            "test_mode": phase_mode == "test",
        }
    def build_commute_briefing(
        self,
        trigger_type: str,
        current_gps: dict[str, float] | None,
        selected_transport: str | None = None,
        moved_m: float | None = None,
    ) -> dict[str, Any]:
        if trigger_type not in {"leave_home", "leave_office"}:
            return {"ok": False, "error": "invalid trigger_type"}

        phase_key = "leave_home" if trigger_type == "leave_home" else "leave_office"
        mode = self._get_phase_mode(phase_key)
        if mode == "off":
            return {"ok": True, "triggered": False, "phase": trigger_type, "reason": "mode_off"}

        profile, test_cfg = self._resolve_context()
        sec = self._section(test_cfg, phase_key) if mode == "test" else {}
        now = self._parse_iso(sec.get("mock_now"), datetime.now(KST)) if sec else datetime.now(KST)

        home = self._coord(sec.get("home")) if sec else None
        office = self._coord(sec.get("office")) if sec else None
        home = home or self._coord(profile.get("home"))
        office = office or self._coord(profile.get("office"))
        if not home or not office:
            return {"ok": False, "error": "home/office coordinates are required", "phase": trigger_type}

        if not isinstance(current_gps, dict):
            if sec and isinstance(sec.get("current_gps"), dict):
                current_gps = sec.get("current_gps")
            else:
                return {"ok": False, "error": "current_gps is required", "phase": trigger_type}

        current = self._coord(current_gps)
        if not current:
            return {"ok": False, "error": "invalid current_gps", "phase": trigger_type}

        anchor = home if trigger_type == "leave_home" else office
        destination = office if trigger_type == "leave_home" else home
        distance_m = _to_float(sec.get("distance_from_anchor_m")) if sec else None
        if distance_m is None:
            distance_m = _haversine_meters(current, anchor)
        if distance_m < 50:
            return {"ok": True, "triggered": False, "phase": trigger_type, "distance_m": int(distance_m), "reason": "within_anchor_radius"}

        if trigger_type == "leave_office":
            start_h, end_h = self.get_evening_trigger_window()
            if mode == "live" and not (start_h <= now.hour <= end_h):
                return {"ok": True, "triggered": False, "phase": trigger_type, "reason": "outside_evening_window"}
            if mode == "live" and moved_m is not None and float(moved_m) < 50.0:
                return {"ok": True, "triggered": False, "phase": trigger_type, "reason": "movement_too_small", "moved_m": float(moved_m)}

        transport = self.normalize_transport_mode(selected_transport or sec.get("selected_transport") or profile.get("default_transport_mode"))

        transit_info = sec.get("transit_info") if isinstance(sec.get("transit_info"), dict) else {}
        car_info = sec.get("car_info") if isinstance(sec.get("car_info"), dict) else {}
        if transport == "car":
            commute = {"estimated_minutes": _to_int(car_info.get("estimated_minutes")), "provider": str(car_info.get("provider") or "mock"), "traffic_note": str(car_info.get("traffic_note") or "").strip()}
            if commute.get("estimated_minutes") is None:
                commute = {"estimated_minutes": self._fetch_car_minutes(current, destination), "provider": "tmap", "traffic_note": ""}
        else:
            commute = {
                "estimated_minutes": _to_int(transit_info.get("estimated_minutes")),
                "provider": str(transit_info.get("provider") or "mock"),
                "first_mode": str(transit_info.get("first_mode") or "").strip() or None,
                "subway_line": str(transit_info.get("subway_line") or "").strip() or None,
                "boarding_station": str(transit_info.get("boarding_station") or "").strip() or None,
                "arrival_info": str(transit_info.get("arrival_info") or "").strip(),
            }
            if commute.get("estimated_minutes") is None:
                commute = self._fetch_transit_time(current, destination)

        destination_weather = self._weather_from_raw(sec.get("destination_weather")) if sec else {}
        if not destination_weather:
            destination_weather = self._fetch_weather(destination["lat"], destination["lng"])

        incidents = [x for x in (sec.get("traffic_incidents") if isinstance(sec.get("traffic_incidents"), list) else []) if isinstance(x, dict)] if sec else []
        poi_data = sec.get("poi_congestion") if isinstance(sec.get("poi_congestion"), dict) else None
        if not poi_data:
            poi_data = self.tmap.get_poi_congestion(lat=destination["lat"], lng=destination["lng"])
        poi_label = None
        if isinstance(poi_data, dict):
            for k in ("congestionLabel", "label", "congestion", "level"):
                v = str(poi_data.get(k) or "").strip()
                if v:
                    poi_label = v
                    break

        district = str(sec.get("local_district") or "").strip() if sec else ""
        if not district:
            p = current if trigger_type == "leave_home" else anchor
            district = self._extract_district(p["lat"], p["lng"])

        interest_news = [x for x in (sec.get("interest_news") if isinstance(sec.get("interest_news"), list) else []) if isinstance(x, dict)] if sec else []
        if not interest_news:
            kws = profile.get("interest_keywords") if isinstance(profile.get("interest_keywords"), list) else []
            keywords = [str(x).strip() for x in kws if str(x).strip()] or ["AI", "경제", "서울"]
            interest_news = self._fetch_news(keywords, max_count=3)

        events = [x for x in (sec.get("local_events") if isinstance(sec.get("local_events"), list) else []) if isinstance(x, dict)] if sec else []
        local_news = [x for x in (sec.get("local_news") if isinstance(sec.get("local_news"), list) else []) if isinstance(x, dict)] if sec else []
        if not events:
            events = self._fetch_events(district, max_count=2)
        if not local_news:
            local_news = self._fetch_news([district], max_count=2)

        eta = _to_int(commute.get("estimated_minutes"))
        parts = ["출근 확인: 이동 시작을 확인했어요." if trigger_type == "leave_home" else "퇴근 확인: 이동 시작을 확인했어요."]
        if eta is not None:
            parts.append(f"{'대중교통' if transport == 'public' else '자가용'} 기준 예상 소요시간은 약 {eta}분입니다.")
        if transport == "public":
            line = str(commute.get("subway_line") or "").strip()
            station = str(commute.get("boarding_station") or "").strip()
            if line and station:
                parts.append(f"{station}역에서 {line} 탑승 기준으로 안내합니다.")
            if str(commute.get("arrival_info") or "").strip():
                parts.append(str(commute.get("arrival_info")).strip())
        elif str(commute.get("traffic_note") or "").strip():
            parts.append(str(commute.get("traffic_note")).strip())

        temp = _to_float(destination_weather.get("temperature"))
        pop = _to_int(destination_weather.get("precipitation_probability"))
        if temp is not None:
            parts.append(f"도착지 기온은 약 {int(round(temp))}도입니다.")
        if pop is not None:
            parts.append(f"도착지 강수확률은 {pop}%입니다.")

        if incidents:
            s = str(incidents[0].get("summary") or incidents[0].get("title") or "").strip()
            if s:
                parts.append(f"교통 이슈: {s}")
        if poi_label:
            parts.append(f"도착지 주변 혼잡도는 {poi_label}입니다.")

        if trigger_type == "leave_home" and interest_news:
            n = str(interest_news[0].get("title") or "").strip()
            if n:
                parts.append(f"관심 뉴스: {n}")

        if events:
            e = events[0]
            t = str(e.get("title") or "").strip()
            p = str(e.get("place") or "").strip()
            if t:
                parts.append(f"지역 문화행사: {t}{f' ({p})' if p else ''}")
        elif local_news:
            n = str(local_news[0].get("title") or "").strip()
            if n:
                parts.append(f"지역 소식: {n}")

        return {
            "ok": True,
            "triggered": True,
            "phase": trigger_type,
            "trigger_time": now.isoformat(),
            "distance_m": int(distance_m),
            "selected_transport": transport,
            "alert": " ".join([p for p in parts if p]).strip(),
            "commute": commute,
            "destination_weather": destination_weather,
            "traffic_incidents": incidents,
            "poi_congestion": poi_data,
            "district": district,
            "interest_news": interest_news,
            "local_issue": {"events": events, "local_news": local_news},
            "test_mode": mode == "test",
        }

    def build_leaving_home_alert(self, current_gps: dict[str, float] | None = None, selected_transport: str | None = None) -> dict[str, Any]:
        return self.build_commute_briefing("leave_home", current_gps, selected_transport, None)

    def build_evening_local_alert(
        self,
        current_gps: dict[str, float] | None,
        moved_m: float | None = None,
        selected_transport: str | None = None,
    ) -> dict[str, Any]:
        return self.build_commute_briefing("leave_office", current_gps, selected_transport, moved_m)
