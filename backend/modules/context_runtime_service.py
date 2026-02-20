from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from typing import Any, Callable


class ContextRuntimeService:
    def __init__(
        self,
        odsay_api_key: str | None,
        tmap_service: Any,
        env_cache_ttl_sec: float,
        haversine_meters: Callable[[float, float, float, float], float],
        home_lat: str | None = None,
        home_lng: str | None = None,
        log=print,
    ):
        self.odsay_api_key = str(odsay_api_key or "").strip()
        self.tmap_service = tmap_service
        self.env_cache_ttl_sec = float(env_cache_ttl_sec)
        self.haversine_meters = haversine_meters
        self.home_lat = home_lat
        self.home_lng = home_lng
        self.log = log

    def to_float(self, value):
        try:
            return float(value)
        except Exception:
            return None

    def to_int(self, value):
        try:
            return int(float(value))
        except Exception:
            return None

    def http_get_json(self, url: str, timeout: int = 6):
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                return json.loads(body)
        except Exception as e:
            self.log(f"[SeoulInfo] HTTP error: {e}")
            return None

    def http_get_json_with_headers(self, url: str, headers: dict | None = None, timeout: int = 6):
        try:
            req = urllib.request.Request(url, method="GET", headers=headers or {})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                return json.loads(body)
        except Exception as e:
            self.log(f"[SeoulInfo] HTTP error: {e}")
            return None

    def resolve_home_coords(self):
        lat = self.to_float(self.home_lat)
        lng = self.to_float(self.home_lng)
        if lat is None or lng is None:
            return None, None
        return lat, lng

    def extract_restaurant_keyword(self, text: str) -> str:
        t = str(text or "").strip()
        if not t:
            return "맛집"
        patterns = [
            (r"(한식|중식|일식|양식|분식|치킨|피자|버거|카페|디저트|고기|국밥|라멘|파스타)", None),
        ]
        for p, _ in patterns:
            m = re.search(p, t, flags=re.IGNORECASE)
            if m:
                return str(m.group(1)).strip()
        for token in ["맛집", "음식점", "식당", "점심", "저녁", "밥집"]:
            if token in t:
                return token
        return "맛집"

    def search_restaurants_nearby(self, lat: float, lng: float, user_text: str | None = None, limit: int = 5):
        keyword = self.extract_restaurant_keyword(user_text or "")
        try:
            rows = self.tmap_service.search_nearby_restaurants(
                lat=float(lat),
                lng=float(lng),
                keyword=keyword,
                count=max(1, min(int(limit), 10)),
                radius_m=1500,
            )
        except Exception as e:
            self.log(f"[Restaurant] search failed: {e}")
            return []
        normalized = []
        for r in rows or []:
            if not isinstance(r, dict):
                continue
            name = str(r.get("name") or "").strip()
            if not name:
                continue
            normalized.append(
                {
                    "name": name,
                    "category": str(r.get("category") or "").strip() or None,
                    "distance_m": self.to_int(r.get("distance_m")),
                    "address": str(r.get("address") or "").strip() or None,
                    "lat": self.to_float(r.get("lat")),
                    "lng": self.to_float(r.get("lng")),
                }
            )
        normalized.sort(key=lambda x: (x.get("distance_m") is None, x.get("distance_m") or 999999))
        return normalized[: max(1, min(int(limit), 10))]

    def build_destination_candidates(self, name: str | None):
        raw = str(name or "").strip()
        if not raw:
            return []
        cands = []
        seen = set()

        def _add(value: str):
            v = str(value or "").strip()
            if not v:
                return
            if v not in seen:
                seen.add(v)
                cands.append(v)

        base = raw
        _add(base)
        cleaned = re.sub(r"(으로|로|에|에서|쪽|근처|부근|방향|가는길|가는 길|가는|갈|방법|경로)$", "", base).strip()
        _add(cleaned)
        compact = re.sub(r"\s+", "", cleaned)
        _add(compact)

        for seed in [base, cleaned, compact]:
            if seed and not seed.endswith("역"):
                _add(seed + "역")
        return [x for x in cands if x]

    def resolve_destination_coords_from_name(self, name: str):
        if not self.odsay_api_key or not name:
            return None, None

        def _search_station(station_name: str):
            query = urllib.parse.urlencode({"apiKey": self.odsay_api_key, "stationName": station_name})
            url = f"https://api.odsay.com/v1/api/searchStation?{query}"
            data = self.http_get_json(url, timeout=6)
            if not isinstance(data, dict):
                return None, None
            result = data.get("result", {})
            station_list = result.get("station") if isinstance(result, dict) else None
            if isinstance(station_list, list) and station_list:
                first = station_list[0] if isinstance(station_list[0], dict) else {}
                x = self.to_float(first.get("x"))
                y = self.to_float(first.get("y"))
                return y, x
            return None, None

        candidates = self.build_destination_candidates(name)
        for cand in candidates:
            y, x = _search_station(cand)
            if y is not None and x is not None:
                return y, x
        return None, None

    def get_weather_only(self, lat: float, lng: float):
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
        w = self.http_get_json(w_url, timeout=6)
        if isinstance(w, dict):
            cur = w.get("current", {}) if isinstance(w.get("current"), dict) else {}
            daily = w.get("daily", {}) if isinstance(w.get("daily"), dict) else {}
            daily_max = daily.get("temperature_2m_max") if isinstance(daily.get("temperature_2m_max"), list) else []
            daily_min = daily.get("temperature_2m_min") if isinstance(daily.get("temperature_2m_min"), list) else []
            daily_pop = daily.get("precipitation_probability_max") if isinstance(daily.get("precipitation_probability_max"), list) else []
            cloud_cover = self.to_float(cur.get("cloud_cover"))
            weather_code = self.to_int(cur.get("weather_code"))
            is_cloudy = (cloud_cover is not None and cloud_cover >= 60) or (
                weather_code in {2, 3, 45, 48} if weather_code is not None else False
            )
            weather = {
                "tempC": self.to_float(cur.get("temperature_2m")),
                "precipitationMm": self.to_float(cur.get("precipitation")),
                "rainMm": self.to_float(cur.get("rain")),
                "cloudCoverPct": cloud_cover,
                "weatherCode": weather_code,
                "isCloudy": bool(is_cloudy),
                "skyText": "흐림" if is_cloudy else "대체로 맑음",
                "todayMaxC": self.to_float(daily_max[0]) if daily_max else None,
                "todayMinC": self.to_float(daily_min[0]) if daily_min else None,
                "precipProbPct": self.to_int(daily_pop[0]) if daily_pop else None,
                "fetchedAtTs": int(time.time()),
            }
        return weather

    def get_air_only(self, lat: float, lng: float):
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
        aq = self.http_get_json(aq_url, timeout=6)
        air = {}
        if isinstance(aq, dict) and isinstance(aq.get("current"), dict):
            cur = aq.get("current")
            us_aqi = self.to_int(cur.get("us_aqi"))
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
                "pm10": self.to_float(cur.get("pm10")),
                "pm25": self.to_float(cur.get("pm2_5")),
                "grade": grade,
                "fetchedAtTs": int(time.time()),
            }
        return air

    def get_weather_and_air(self, lat: float, lng: float):
        weather = self.get_weather_only(lat, lng)
        air = self.get_air_only(lat, lng)
        return weather, air

    def is_env_cache_fresh(self, env_cache: dict | None, lat: float | None, lng: float | None) -> bool:
        if not isinstance(env_cache, dict):
            return False
        ts = float(env_cache.get("ts") or 0.0)
        if ts <= 0:
            return False
        if (time.monotonic() - ts) > self.env_cache_ttl_sec:
            return False
        cache_lat = self.to_float(env_cache.get("lat"))
        cache_lng = self.to_float(env_cache.get("lng"))
        if lat is None or lng is None or cache_lat is None or cache_lng is None:
            return True
        return self.haversine_meters(cache_lat, cache_lng, lat, lng) < 200
