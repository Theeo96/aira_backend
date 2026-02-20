import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class TmapService:
    def __init__(self, app_key: str | None, timeout_sec: int = 6, log=print):
        self.app_key = str(app_key or "").strip()
        self.timeout_sec = timeout_sec
        self.log = log

    @property
    def enabled(self) -> bool:
        return bool(self.app_key)

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
        return self._request_json(
            method="GET",
            url="https://apis.openapi.sk.com/transit/puzzle/subway/congestion/stat/car",
            query={
                "routeNm": route_name,
                "stationNm": station_name,
                "dow": dow,
                "hh": hh,
            },
        )

    def get_poi_congestion(self, lat: float, lng: float) -> dict[str, Any] | None:
        return self._request_json(
            method="GET",
            url="https://apis.openapi.sk.com/puzzle/congestion/poi/rltm",
            query={"lat": lat, "lon": lng},
        )

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

    def get_transit_route(self, origin: dict[str, float], destination: dict[str, float]) -> dict[str, Any] | None:
        return self._request_json(
            method="POST",
            url="https://apis.openapi.sk.com/transit/routes",
            body={
                "startX": origin.get("lng"),
                "startY": origin.get("lat"),
                "endX": destination.get("lng"),
                "endY": destination.get("lat"),
                "lang": 0,
                "format": "json",
                "count": 1,
            },
        )
