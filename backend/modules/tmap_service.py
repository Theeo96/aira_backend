import json
import math
import os
import hashlib
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


class TmapService:
    _shared_congestion_cache: dict[str, dict[str, Any]] = {}
    _shared_quota_state: dict[str, Any] | None = None
    _shared_quota_path: str | None = None

    def __init__(self, app_key: str | None, timeout_sec: int = 6, log=print):
        self.app_key = str(app_key or "").strip()
        self.timeout_sec = timeout_sec
        self.log = log
        self.congestion_daily_limit = self._to_non_negative_int(os.getenv("TMAP_CONGESTION_DAILY_LIMIT"), 2)
        self.congestion_cache_ttl_sec = float(os.getenv("TMAP_CONGESTION_CACHE_TTL_SEC", "900"))
        self.quota_file_path = self._resolve_quota_file_path(
            os.getenv("TMAP_CONGESTION_QUOTA_FILE", "backend/data/tmap_congestion_quota.json")
        )

    @property
    def enabled(self) -> bool:
        return bool(self.app_key)

    def _to_non_negative_int(self, value: Any, default: int) -> int:
        try:
            n = int(value)
            return max(0, n)
        except Exception:
            return int(default)

    def _resolve_quota_file_path(self, raw_path: str) -> Path:
        p = Path(str(raw_path or "").strip())
        if p.is_absolute():
            return p
        project_root = Path(__file__).resolve().parents[2]
        return (project_root / p).resolve()

    def _today_kst_str(self) -> str:
        return datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")

    def _app_key_id(self) -> str:
        if not self.app_key:
            return "no-key"
        return hashlib.sha1(self.app_key.encode("utf-8")).hexdigest()[:12]

    def _read_quota_state(self) -> dict[str, Any]:
        try:
            with open(self.quota_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_quota_state(self, state: dict[str, Any]) -> None:
        try:
            self.quota_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.quota_file_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"[TmapService] quota state write failed: {e}")

    def _load_shared_quota_state(self) -> dict[str, Any]:
        cls = type(self)
        cur_path = str(self.quota_file_path)
        if cls._shared_quota_state is None or cls._shared_quota_path != cur_path:
            cls._shared_quota_state = self._read_quota_state()
            cls._shared_quota_path = cur_path
        return cls._shared_quota_state

    def _save_shared_quota_state(self, state: dict[str, Any]) -> None:
        cls = type(self)
        cls._shared_quota_state = state
        cls._shared_quota_path = str(self.quota_file_path)
        self._write_quota_state(state)

    def _consume_congestion_quota(self) -> bool:
        limit = int(self.congestion_daily_limit)
        if limit <= 0:
            return False
        today = self._today_kst_str()
        app_id = self._app_key_id()
        state = self._load_shared_quota_state()

        if str(state.get("date") or "") != today:
            state = {"date": today, "apps": {}}
        apps = state.get("apps")
        if not isinstance(apps, dict):
            apps = {}
            state["apps"] = apps
        app_stat = apps.get(app_id)
        if not isinstance(app_stat, dict):
            app_stat = {"used": 0}
            apps[app_id] = app_stat

        used = self._to_non_negative_int(app_stat.get("used"), 0)
        if used >= limit:
            return False

        app_stat["used"] = used + 1
        apps[app_id] = app_stat
        state["apps"] = apps
        state["date"] = today
        self._save_shared_quota_state(state)
        return True

    def _congestion_cache_get(self, key: str, allow_stale: bool = False) -> dict[str, Any] | None:
        cached = type(self)._shared_congestion_cache.get(key)
        if not isinstance(cached, dict):
            return None
        payload = cached.get("payload")
        ts = cached.get("ts")
        if not isinstance(payload, dict):
            return None
        if allow_stale:
            return payload
        try:
            age_sec = float(time.monotonic()) - float(ts)
            if age_sec <= float(self.congestion_cache_ttl_sec):
                return payload
        except Exception:
            return None
        return None

    def _congestion_cache_set(self, key: str, payload: dict[str, Any]) -> None:
        type(self)._shared_congestion_cache[key] = {"payload": payload, "ts": float(time.monotonic())}

    def _request_json(
        self,
        method: str,
        url: str,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        q = urllib.parse.urlencode(query or {})
        full_url = f"{url}?{q}" if q else url
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            full_url,
            data=data,
            method=method.upper(),
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "appKey": self.app_key,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            return json.loads(raw)
        except urllib.error.HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode("utf-8", errors="ignore")[:300]
            except Exception:
                body_text = ""
            self.log(f"[TmapService] HTTPError {e.code} {method} {url}: {body_text}")
            return None
        except Exception as e:
            self.log(f"[TmapService] request error {method} {url}: {e}")
            return None

    def _haversine_meters(self, lat1: float, lon1: float, lat2: float, lon2: float) -> int:
        r = 6371000.0
        p1 = math.radians(lat1)
        p2 = math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return int(round(r * c))

    def reverse_geocode_district(self, lat: float, lng: float) -> str | None:
        data = self._request_json(
            method="GET",
            url="https://apis.openapi.sk.com/tmap/geo/reversegeocoding",
            query={
                "version": "1",
                "lat": lat,
                "lon": lng,
                "coordType": "WGS84GEO",
                "addressType": "A10",
            },
        )
        if not isinstance(data, dict):
            return None
        addr = data.get("addressInfo", {}) if isinstance(data.get("addressInfo"), dict) else {}
        for key in ("gu_gun", "legalDong", "adminDong", "city_do"):
            v = str(addr.get(key) or "").strip()
            if v:
                return v
        return None

    def get_subway_car_congestion(
        self,
        route_name: str,
        station_name: str,
        dow: int,
        hh: int,
    ) -> dict[str, Any] | None:
        route_nm = str(route_name or "").strip()
        station_nm = str(station_name or "").strip()
        cache_key = f"subway:{route_nm.lower()}:{station_nm.lower()}:{int(dow)}:{int(hh)}"

        cached = self._congestion_cache_get(cache_key, allow_stale=False)
        if isinstance(cached, dict):
            return cached

        if not self._consume_congestion_quota():
            stale = self._congestion_cache_get(cache_key, allow_stale=True)
            if isinstance(stale, dict):
                self.log("[TmapService] congestion quota reached; reusing stale subway congestion cache")
                return stale
            self.log("[TmapService] congestion quota reached; skipping subway congestion request")
            return None

        data = self._request_json(
            method="GET",
            url="https://apis.openapi.sk.com/transit/puzzle/subway/congestion/stat/car",
            query={
                "routeNm": route_nm,
                "stationNm": station_nm,
                "dow": dow,
                "hh": hh,
            },
        )
        if isinstance(data, dict):
            self._congestion_cache_set(cache_key, data)
            return data
        stale = self._congestion_cache_get(cache_key, allow_stale=True)
        if isinstance(stale, dict):
            self.log("[TmapService] subway congestion request failed; reusing stale cache")
            return stale
        return None

    def get_poi_congestion(self, lat: float, lng: float) -> dict[str, Any] | None:
        lat_key = round(float(lat), 4)
        lng_key = round(float(lng), 4)
        cache_key = f"poi:{lat_key}:{lng_key}"

        cached = self._congestion_cache_get(cache_key, allow_stale=False)
        if isinstance(cached, dict):
            return cached

        if not self._consume_congestion_quota():
            stale = self._congestion_cache_get(cache_key, allow_stale=True)
            if isinstance(stale, dict):
                self.log("[TmapService] congestion quota reached; reusing stale POI congestion cache")
                return stale
            self.log("[TmapService] congestion quota reached; skipping POI congestion request")
            return None

        data = self._request_json(
            method="GET",
            url="https://apis.openapi.sk.com/puzzle/congestion/poi/rltm",
            query={"lat": lat, "lon": lng},
        )
        if isinstance(data, dict):
            self._congestion_cache_set(cache_key, data)
            return data
        stale = self._congestion_cache_get(cache_key, allow_stale=True)
        if isinstance(stale, dict):
            self.log("[TmapService] POI congestion request failed; reusing stale cache")
            return stale
        return None

    def get_car_route(self, origin: dict[str, float], destination: dict[str, float]) -> dict[str, Any] | None:
        return self._request_json(
            method="POST",
            url="https://apis.openapi.sk.com/tmap/routes",
            body={
                "startX": origin.get("lng"),
                "startY": origin.get("lat"),
                "endX": destination.get("lng"),
                "endY": destination.get("lat"),
                "reqCoordType": "WGS84GEO",
                "resCoordType": "WGS84GEO",
                "searchOption": "0",
            },
        )

    def get_transit_route(
        self,
        origin: dict[str, float],
        destination: dict[str, float],
        search_dttm: str | None = None,
        count: int = 1,
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {
            "startX": origin.get("lng"),
            "startY": origin.get("lat"),
            "endX": destination.get("lng"),
            "endY": destination.get("lat"),
            "lang": 0,
            "format": "json",
            "count": max(1, int(count)),
        }
        sd = str(search_dttm or "").strip()
        if sd:
            body["searchDttm"] = sd
        return self._request_json(
            method="POST",
            url="https://apis.openapi.sk.com/transit/routes",
            body=body,
        )

    def search_nearby_restaurants(
        self,
        lat: float,
        lng: float,
        keyword: str = "맛집",
        count: int = 5,
    ) -> list[dict[str, Any]]:
        data = self._request_json(
            method="GET",
            url="https://apis.openapi.sk.com/tmap/pois",
            query={
                "version": "1",
                "searchKeyword": keyword,
                "centerLon": lng,
                "centerLat": lat,
                "count": max(1, int(count)),
                "reqCoordType": "WGS84GEO",
                "resCoordType": "WGS84GEO",
            },
        )
        if not isinstance(data, dict):
            return []

        search_info = data.get("searchPoiInfo", {}) if isinstance(data.get("searchPoiInfo"), dict) else {}
        pois_obj = search_info.get("pois", {}) if isinstance(search_info.get("pois"), dict) else {}
        rows = pois_obj.get("poi")
        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list):
            rows = []

        results: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            category = str(row.get("bizCatName") or row.get("upperBizName") or "").strip()
            poi_lat = None
            poi_lng = None
            try:
                for lat_key in ("noorLat", "frontLat", "newAddressList.lat", "lat"):
                    if row.get(lat_key) is not None:
                        poi_lat = float(row.get(lat_key))
                        break
                for lng_key in ("noorLon", "frontLon", "newAddressList.lon", "lon", "lng"):
                    if row.get(lng_key) is not None:
                        poi_lng = float(row.get(lng_key))
                        break
            except Exception:
                poi_lat, poi_lng = None, None

            dist = None
            # Use explicit distance-like fields first.
            for k in ("distance", "dist", "straightLineDistance"):
                try:
                    if row.get(k) is not None:
                        cand = int(float(row.get(k)))
                        if cand >= 0:
                            dist = cand
                        break
                except Exception:
                    pass
            # Some payloads include radius but this is often search radius, not actual POI distance.
            if (dist is None or dist == 0) and poi_lat is not None and poi_lng is not None:
                dist = self._haversine_meters(lat, lng, poi_lat, poi_lng)
            if dist is None:
                try:
                    if row.get("radius") is not None:
                        cand = int(float(row.get("radius")))
                        if cand > 0:
                            dist = cand
                except Exception:
                    pass

            addr = " ".join(
                [
                    str(row.get("upperAddrName") or "").strip(),
                    str(row.get("middleAddrName") or "").strip(),
                    str(row.get("lowerAddrName") or "").strip(),
                    str(row.get("detailAddrName") or "").strip(),
                ]
            ).strip()
            results.append(
                {
                    "name": name,
                    "category": category,
                    "distance_m": dist,
                    "address": addr,
                    "lat": poi_lat,
                    "lng": poi_lng,
                }
            )

        return results[: max(1, int(count))]
