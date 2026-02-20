import json
import math
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from dotenv import dotenv_values

from .news_agent import NewsAgent
from .tmap_service import TmapService


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
        # backend/modules/morning_briefing_module.py -> project root
        self.project_root = Path(__file__).resolve().parents[2]
        raw_profile_path = os.getenv("BRIEFING_PROFILE_PATH", "backend/data/user_profile.json")
        raw_test_config_path = os.getenv("BRIEFING_TEST_CONFIG", "backend/data/test_config.json")
        init_mode = str(os.getenv("BRIEFING_MODE", "live")).strip().lower()
        self.config = BriefingConfig(
            profile_path=str(self._resolve_path(raw_profile_path)),
            test_config_path=str(self._resolve_path(raw_test_config_path)),
            test_mode=init_mode == "test",
        )

    def _read_dotenv_runtime(self) -> dict[str, str]:
        env_path = self.project_root / ".env"
        try:
            values = dotenv_values(str(env_path))
            return {str(k): str(v) for k, v in values.items() if k and v is not None}
        except Exception:
            return {}

    def _get_runtime_env(self, key: str, default: str) -> str:
        # Prefer current .env file value so runtime edits are reflected without restart.
        file_env = self._read_dotenv_runtime()
        if key in file_env:
            return str(file_env.get(key) or default)
        return str(os.getenv(key, default))

    def _is_enabled(self, key: str, default: bool = False) -> bool:
        raw = self._get_runtime_env(key, "true" if default else "false")
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}

    def _get_briefing_mode(self) -> str:
        # Unified mode:
        # - off: disable all briefing behavior
        # - live: real data/profile based briefing
        # - test: mock(test_config) based briefing
        mode = str(self._get_runtime_env("BRIEFING_MODE", "")).strip().lower()
        if mode in {"off", "live", "test"}:
            return mode
        # Backward compatibility when BRIEFING_MODE is not provided.
        return "test" if self._is_enabled("BRIEFING_TEST_MODE", default=False) else "live"

    def _refresh_runtime_config(self):
        raw_profile_path = self._get_runtime_env("BRIEFING_PROFILE_PATH", "backend/data/user_profile.json")
        raw_test_config_path = self._get_runtime_env("BRIEFING_TEST_CONFIG", "backend/data/test_config.json")
        mode = self._get_briefing_mode()
        self.config.profile_path = str(self._resolve_path(raw_profile_path))
        self.config.test_config_path = str(self._resolve_path(raw_test_config_path))
        self.config.test_mode = mode == "test"

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
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            self.log(f"[MorningBriefing] load failed: {path} ({e})")
            return {}

    def _resolve_context(self) -> tuple[dict[str, Any], dict[str, Any] | None]:
        self._refresh_runtime_config()
        profile = self._load_json(self.config.profile_path)
        test_cfg = self._load_json(self.config.test_config_path) if self.config.test_mode else None
        return profile, test_cfg

    def is_test_mode(self) -> bool:
        self._refresh_runtime_config()
        return bool(self.config.test_mode)

    def is_briefing_enabled(self) -> bool:
        return self._get_briefing_mode() != "off"

    def is_wake_up_enabled(self) -> bool:
        return self.is_briefing_enabled()

    def is_leaving_home_enabled(self) -> bool:
        return self.is_briefing_enabled()

    def is_briefing_api_enabled(self) -> bool:
        return self.is_briefing_enabled()

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

    def _fetch_odsay_commute(self, origin: dict[str, float], destination: dict[str, float]) -> dict[str, Any]:
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
            traffic_type = _to_int(seg.get("trafficType"))
            if traffic_type in (1, 2):
                first_mode = "subway" if traffic_type == 1 else "bus"
                boarding_station = seg.get("startName")
                lane = seg.get("lane", [])
                if isinstance(lane, list) and lane and isinstance(lane[0], dict):
                    subway_line = lane[0].get("name")
                break
        return {
            "estimated_minutes": _to_int(info.get("totalTime")),
            "first_mode": first_mode,
            "subway_line": subway_line,
            "boarding_station": boarding_station,
            "provider": "odsay",
        }

    def _fetch_commute_time(self, origin: dict[str, float], destination: dict[str, float]) -> dict[str, Any]:
        def _normalize_minutes(raw: Any) -> int | None:
            m = _to_int(raw)
            if m is None:
                return None
            if m <= 0:
                return None
            # In Tmap responses, totalTime can be returned in seconds.
            # Treat very large values as seconds and convert to minutes.
            if m > 240:
                m = int(round(m / 60))
            return m

        tmap_raw = self.tmap.get_transit_route(origin=origin, destination=destination)
        tmap_minutes = None
        if isinstance(tmap_raw, dict):
            mm = tmap_raw.get("metaData", {}) if isinstance(tmap_raw.get("metaData"), dict) else {}
            plan = mm.get("plan", {}) if isinstance(mm.get("plan"), dict) else {}
            routes = plan.get("itineraries") if isinstance(plan.get("itineraries"), list) else []
            if routes and isinstance(routes[0], dict):
                tmap_minutes = _normalize_minutes(routes[0].get("totalTime"))
        if tmap_minutes is not None and 1 <= int(tmap_minutes) <= 240:
            return {"estimated_minutes": tmap_minutes, "provider": "tmap", "first_mode": None, "subway_line": None, "boarding_station": None}
        odsay = self._fetch_odsay_commute(origin=origin, destination=destination)
        odsay_minutes = _normalize_minutes(odsay.get("estimated_minutes"))
        if odsay_minutes is not None:
            odsay["estimated_minutes"] = odsay_minutes
        if odsay_minutes is not None and 1 <= int(odsay_minutes) <= 240:
            return odsay
        if tmap_minutes is not None:
            fallback_minutes = min(max(int(tmap_minutes), 1), 240)
            return {"estimated_minutes": fallback_minutes, "provider": "tmap", "first_mode": None, "subway_line": None, "boarding_station": None}
        return odsay

    def _extract_district(self, lat: float, lng: float) -> str:
        district = self.tmap.reverse_geocode_district(lat=lat, lng=lng)
        if district:
            return district
        data = _http_get_json("http://ip-api.com/json/?fields=city")
        if isinstance(data, dict):
            city = str(data.get("city") or "").strip()
            if city:
                return city
        return "서울"

    def _fetch_news(self, keywords: list[str], max_count: int = 5) -> list[dict[str, Any]]:
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
                items.append(
                    {
                        "title": str(n.get("title") or "").strip(),
                        "link": link,
                        "pubDate": str(n.get("pubDate") or "").strip(),
                    }
                )
        items.sort(key=lambda x: x.get("pubDate", ""), reverse=True)
        return items[:max_count]

    def _news_summary(self, news: list[dict[str, Any]], max_lines: int = 3) -> str:
        if not news:
            return "뉴스를 불러오지 못했습니다."
        lines = []
        for i, n in enumerate(news[:max_lines], start=1):
            title = str(n.get("title") or "").strip()
            if title:
                lines.append(f"{i}. {title}")
        return " / ".join(lines) if lines else "뉴스를 불러오지 못했습니다."

    def _clothing_advice(self, temperature: float | None) -> str:
        if temperature is None:
            return "가벼운 외투를 챙기세요."
        if temperature <= 3:
            return "두꺼운 코트와 목도리를 권장합니다."
        if temperature <= 10:
            return "가벼운 코트가 적당합니다."
        if temperature <= 18:
            return "얇은 겉옷을 챙기세요."
        return "가벼운 차림이 좋습니다."

    def _compose_wake_up(
        self,
        weather: dict[str, Any],
        commute: dict[str, Any],
        news_summary: str,
        district: str,
        local_news: list[dict[str, Any]],
        car_hint: str | None,
        leave_early: str | None,
    ) -> str:
        t = weather.get("temperature")
        pop = weather.get("precipitation_probability")
        umbrella = bool(pop is not None and pop >= 50)
        parts: list[str] = []
        if t is not None:
            parts.append(f"현재 기온은 {int(round(float(t)))}도입니다.")
        if pop is not None:
            parts.append(f"강수확률은 {int(pop)}%입니다.")
        if umbrella:
            parts.append("우산을 챙기세요.")
        parts.append(self._clothing_advice(t))
        eta = commute.get("estimated_minutes")
        if eta is not None:
            parts.append(f"예상 출근 소요 시간은 약 {int(eta)}분입니다.")
        if leave_early:
            parts.append(leave_early)
        if car_hint:
            parts.append(car_hint)
        parts.append(f"주요 뉴스: {news_summary}")
        if local_news:
            title = str(local_news[0].get("title") or "").strip()
            if title:
                parts.append(f"{district} 지역 소식: {title}")
        # Keep proactive wake-up speech short to avoid audio cut-off.
        compact = [p for p in parts if p][:6]
        text = " ".join(compact).strip()
        if len(text) > 320:
            text = text[:317].rstrip() + "..."
        return text

    def _compose_leaving(
        self,
        destination_weather: dict[str, Any],
        incidents: list[dict[str, Any]],
        poi_congestion_label: str | None,
        alt_route_minutes: int | None,
        district: str,
        local_news: list[dict[str, Any]],
    ) -> str:
        parts = []
        t = destination_weather.get("temperature")
        pop = destination_weather.get("precipitation_probability")
        if t is not None:
            parts.append(f"도착지 예상 기온은 {int(round(float(t)))}도입니다.")
        if pop is not None:
            parts.append(f"도착지 강수확률은 {int(pop)}%입니다.")
        if incidents:
            parts.append(f"경로상 특이사항 {len(incidents)}건이 있습니다.")
        if poi_congestion_label:
            parts.append(f"목적지 주변 혼잡도는 {poi_congestion_label}입니다.")
        if alt_route_minutes is not None:
            parts.append(f"대체 차량 경로는 약 {alt_route_minutes}분입니다.")
        if local_news:
            title = str(local_news[0].get("title") or "").strip()
            if title:
                parts.append(f"{district} 지역 이슈: {title}")
        return " ".join([p for p in parts if p]).strip()

    def _parse_poi_congestion_label(self, poi_data: dict[str, Any] | None) -> str | None:
        if not isinstance(poi_data, dict):
            return None
        for key in ("congestionLabel", "label", "congestion", "level"):
            v = str(poi_data.get(key) or "").strip()
            if v:
                return v
        return None

    def _parse_car_route_minutes(self, route_data: dict[str, Any] | None) -> int | None:
        if not isinstance(route_data, dict):
            return None
        features = route_data.get("features") if isinstance(route_data.get("features"), list) else []
        if not features:
            return None
        prop = features[0].get("properties") if isinstance(features[0], dict) and isinstance(features[0].get("properties"), dict) else {}
        sec = _to_int(prop.get("totalTime"))
        if sec is not None:
            return max(1, int(round(sec / 60)))
        minutes = _to_int(prop.get("totalTimeMin"))
        return minutes

    def build_wake_up_briefing(self) -> dict[str, Any]:
        profile, test_cfg = self._resolve_context()
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        home = profile.get("home", {}) if isinstance(profile.get("home"), dict) else {}
        office = profile.get("office", {}) if isinstance(profile.get("office"), dict) else {}
        if isinstance(test_cfg, dict):
            if isinstance(test_cfg.get("mock_home"), dict):
                home = test_cfg.get("mock_home")
            if isinstance(test_cfg.get("mock_office"), dict):
                office = test_cfg.get("mock_office")
            mock_time = str(test_cfg.get("mock_time") or "").strip()
            if mock_time:
                try:
                    now = datetime.fromisoformat(mock_time.replace(" ", "T"))
                except Exception:
                    pass
        home_lat = _to_float(home.get("lat"))
        home_lng = _to_float(home.get("lng"))
        office_lat = _to_float(office.get("lat"))
        office_lng = _to_float(office.get("lng"))
        if home_lat is None or home_lng is None or office_lat is None or office_lng is None:
            return {"ok": False, "error": "home/office 좌표가 필요합니다."}

        weather = {}
        if isinstance(test_cfg, dict) and isinstance(test_cfg.get("mock_weather"), dict):
            weather = test_cfg.get("mock_weather")
        if not weather:
            weather = self._fetch_weather(home_lat, home_lng)

        commute = self._fetch_commute_time(
            origin={"lat": home_lat, "lng": home_lng},
            destination={"lat": office_lat, "lng": office_lng},
        )
        usual = _to_int(profile.get("usual_commute_minutes")) or 40
        estimated = _to_int(commute.get("estimated_minutes"))
        if estimated is not None and estimated > (usual * 3):
            # Safety-net for unexpected second/minute unit drift.
            sec_to_min = int(round(estimated / 60))
            if 1 <= sec_to_min <= 240:
                estimated = sec_to_min
                commute["estimated_minutes"] = estimated
        leave_early = None
        if estimated is not None and estimated - usual > 5:
            leave_early = f"평소보다 {estimated - usual}분 일찍 출발하는 것을 권장합니다."

        car_hint = None
        if str(commute.get("first_mode") or "") == "subway":
            line = str(commute.get("subway_line") or "").strip()
            station = str(commute.get("boarding_station") or "").strip()
            if line and station:
                cong = self.tmap.get_subway_car_congestion(
                    route_name=line,
                    station_name=station,
                    dow=now.weekday() + 1,
                    hh=now.hour,
                )
                if isinstance(cong, dict):
                    car_hint = "지하철 칸별 혼잡도 정보가 확인되어 덜 붐비는 칸 탑승을 권장합니다."

        interests = profile.get("interest_keywords") if isinstance(profile.get("interest_keywords"), list) else []
        interests = [str(x) for x in interests if str(x).strip()] or ["AI", "경제", "서울"]
        news = self._fetch_news(interests, max_count=5)
        news_summary = self._news_summary(news)

        district = self._extract_district(home_lat, home_lng)
        local_news = self._fetch_news([district], max_count=2)
        briefing_text = self._compose_wake_up(
            weather=weather,
            commute=commute,
            news_summary=news_summary,
            district=district,
            local_news=local_news,
            car_hint=car_hint,
            leave_early=leave_early,
        )
        return {
            "ok": True,
            "phase": "wake_up",
            "briefing": briefing_text,
            "weather": weather,
            "commute": commute,
            "district": district,
            "news": news,
            "local_news": local_news,
            "test_mode": self.config.test_mode,
        }

    def get_wake_up_time(self) -> str:
        profile, _ = self._resolve_context()
        wake_up_time = str(profile.get("wake_up_time") or "").strip()
        if not wake_up_time:
            return "07:00"
        return wake_up_time

    def build_leaving_home_alert(self, current_gps: dict[str, float] | None = None) -> dict[str, Any]:
        profile, test_cfg = self._resolve_context()
        home = profile.get("home", {}) if isinstance(profile.get("home"), dict) else {}
        office = profile.get("office", {}) if isinstance(profile.get("office"), dict) else {}
        if isinstance(test_cfg, dict):
            if isinstance(test_cfg.get("mock_office"), dict):
                office = test_cfg.get("mock_office")
            if isinstance(test_cfg.get("mock_home"), dict):
                home = test_cfg.get("mock_home")
            if isinstance(test_cfg.get("mock_location"), dict):
                current_gps = test_cfg.get("mock_location")
        if not isinstance(current_gps, dict):
            return {"ok": False, "error": "current_gps 값이 필요합니다."}

        home_point = {"lat": _to_float(home.get("lat")), "lng": _to_float(home.get("lng"))}
        cur_point = {"lat": _to_float(current_gps.get("lat")), "lng": _to_float(current_gps.get("lng"))}
        office_point = {"lat": _to_float(office.get("lat")), "lng": _to_float(office.get("lng"))}
        if None in {home_point["lat"], home_point["lng"], cur_point["lat"], cur_point["lng"], office_point["lat"], office_point["lng"]}:
            return {"ok": False, "error": "좌표 정보가 누락되었습니다."}

        distance_m = _haversine_meters(cur_point, home_point)
        if distance_m < 50:
            return {"ok": True, "phase": "leaving_home", "alert": "", "triggered": False, "distance_m": int(distance_m)}

        destination_weather = self._fetch_weather(office_point["lat"], office_point["lng"])
        incidents = []
        if isinstance(test_cfg, dict) and isinstance(test_cfg.get("mock_incidents"), list):
            incidents = [x for x in test_cfg.get("mock_incidents") if isinstance(x, dict)]

        poi = self.tmap.get_poi_congestion(lat=office_point["lat"], lng=office_point["lng"])
        poi_label = self._parse_poi_congestion_label(poi)
        alt_route = self.tmap.get_car_route(origin=cur_point, destination=office_point) if incidents else None
        alt_route_minutes = self._parse_car_route_minutes(alt_route)
        district = self._extract_district(cur_point["lat"], cur_point["lng"])
        local_news = self._fetch_news([district], max_count=2)
        alert = self._compose_leaving(
            destination_weather=destination_weather,
            incidents=incidents,
            poi_congestion_label=poi_label,
            alt_route_minutes=alt_route_minutes,
            district=district,
            local_news=local_news,
        )
        return {
            "ok": True,
            "phase": "leaving_home",
            "triggered": True,
            "distance_m": int(distance_m),
            "alert": alert,
            "destination_weather": destination_weather,
            "incidents": incidents,
            "poi_congestion": poi,
            "alternate_route": alt_route,
            "district": district,
            "local_news": local_news,
            "test_mode": self.config.test_mode,
        }
