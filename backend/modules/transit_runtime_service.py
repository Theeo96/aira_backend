from __future__ import annotations

import json
import math
import re
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


class TransitRuntimeService:
    def __init__(
        self,
        odsay_api_key: str | None,
        seoul_api_key: str | None,
        tmap_app_key: str | None,
        tmap_service: Any,
        log=print,
    ):
        self.odsay_api_key = str(odsay_api_key or "").strip()
        self.seoul_api_key = str(seoul_api_key or "").strip()
        self.tmap_app_key = str(tmap_app_key or "").strip()
        self.tmap_service = tmap_service
        self.log = log

    def _http_get_json(self, url: str, timeout: int = 6):
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                return json.loads(body)
        except Exception as e:
            self.log(f"[SeoulInfo] HTTP error: {e}")
            return None

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

    def round_eta_minutes(self, total_seconds: int) -> int:
        if total_seconds <= 0:
            return 0
        # Conservative rounding for boarding decisions:
        # 3m30s -> about 3 minutes (not 4), while keeping sub-1m as 1.
        return max(1, total_seconds // 60)

    def parse_eta_minutes_from_message(self, message: str):
        text = str(message or "")
        m = re.search(r"(\d+)\s*\uBD84(?:\s*(\d+)\s*\uCD08)?", text)
        if m:
            mm = int(m.group(1) or 0)
            ss = int(m.group(2) or 0)
            return self.round_eta_minutes(mm * 60 + ss)
            
        m2 = re.search(r"(\d+)[\s*]?(?:번째)?\s*전역", text)
        if m2:
            stations_away = int(m2.group(1))
            return stations_away * 2

        if re.search(r"\uC804\uC5ED\s*\uB3C4\uCC29", text):
            return 2
        if re.search(r"\uACF3\s*\uB3C4\uCC29|\uC7A0\uC2DC\s*\uD6C4|\uC9C4\uC785|\uB3C4\uCC29", text):
            return 1
        if re.search(r"\uACF3\s*\uB3C4\uCC29|\uC7A0\uC2DC\s*\uD6C4|\uC9C4\uC785|\uB3C4\uCC29", text):
            return 0
        return None

    def extract_arrival_minutes(self, row: dict, allow_zero: bool = True):
        raw_seconds = self.to_int(row.get("barvlDt"))
        if raw_seconds is not None and raw_seconds > 0:
            return self.round_eta_minutes(raw_seconds)
        if raw_seconds == 0 and allow_zero:
            return 0
        parsed = self.parse_eta_minutes_from_message(str(row.get("arvlMsg2", "")))
        if parsed == 0 and not allow_zero:
            return None
        return parsed

    def format_eta_phrase(self, minutes: int | None) -> str | None:
        if minutes is None:
            return None
        if minutes <= 2:
            return "\uACF3 \uB3C4\uCC29"
        return f"\uC57D {minutes}\uBD84"

    def haversine_meters(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371000.0
        p1 = math.radians(lat1)
        p2 = math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c

    def estimate_walk_minutes(self, lat: float, lng: float, station_lat: float | None, station_lng: float | None):
        if station_lat is None or station_lng is None:
            return None
        distance_m = self.haversine_meters(lat, lng, station_lat, station_lng)
        # Inflate straight-line distance to approximate real walking path.
        path_m = distance_m * 1.25
        speed_m_per_min = 4200 / 60  # ~4.2km/h
        return max(1, int(round(path_m / speed_m_per_min)))

    def pick_station_from_odsay_response(self, data):
        if not isinstance(data, dict):
            return None

        if data.get("error"):
            self.log(f"[SeoulInfo] ODSAY error: {data.get('error')}")
        if data.get("result", {}).get("error"):
            self.log(f"[SeoulInfo] ODSAY result error: {data.get('result', {}).get('error')}")

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

    def get_nearby_station(self, lat: float, lng: float, station_class: int | None = 2, log_label: str = "station"):
        if not self.odsay_api_key:
            return None

        # Try wider search radii and flexible parameter sets because pointSearch
        # responses vary by account tier/region and nearby station density.
        for radius in (800, 1500, 3000):
            for include_station_class in (True, False):
                params = {
                    "apiKey": self.odsay_api_key,
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
                data = self._http_get_json(url)
                picked = self.pick_station_from_odsay_response(data)
                if picked:
                    return picked

        self.log(f"[SeoulInfo] ODSAY nearby {log_label} not found (lat={lat}, lng={lng})")
        return None

    def get_nearby_bus_stop(self, lat: float, lng: float):
        return self.get_nearby_station(lat, lng, station_class=1, log_label="bus stop")

    def get_subway_arrival(self, station_name: str):
        if not self.seoul_api_key:
            return []

        safe_station = urllib.parse.quote(station_name)
        url = (
            f"http://swopenapi.seoul.go.kr/api/subway/{self.seoul_api_key}/json/"
            f"realtimeStationArrival/0/5/{safe_station}"
        )
        data = self._http_get_json(url)
        if not isinstance(data, dict):
            return []

        rows = data.get("realtimeArrivalList", [])
        return rows if isinstance(rows, list) else []

    def weekday_to_tmap_dow(self, dt: datetime) -> int:
        # Tmap subway congestion uses 1~7, Monday=1.
        return int(dt.weekday()) + 1

    def normalize_route_name_for_tmap(self, line_text: str | None) -> str | None:
        s = str(line_text or "").strip()
        if not s:
            return None
        m = re.search(r"(\d+)\s*\uD638\uC120", s)
        if m:
            return f"{m.group(1)}\uD638\uC120"
        m2 = re.search(r"(\d+)\s*line", s, flags=re.IGNORECASE)
        if m2:
            return f"{m2.group(1)}\uD638\uC120"
        return s

    def extract_tmap_congestion_rows(self, payload: dict | None) -> list[dict]:
        if not isinstance(payload, dict):
            return []

        rows = []
        # Common wrappers seen across SK open APIs.
        for key in ("data", "result", "contents", "response", "body"):
            value = payload.get(key)
            if isinstance(value, list):
                rows.extend([x for x in value if isinstance(x, dict)])
            elif isinstance(value, dict):
                for inner in ("data", "list", "items", "cars", "car", "contents"):
                    v2 = value.get(inner)
                    if isinstance(v2, list):
                        rows.extend([x for x in v2 if isinstance(x, dict)])

        # Fallback: payload itself might already represent a row-ish object list under unknown key.
        if not rows:
            for _, value in payload.items():
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    rows.extend([x for x in value if isinstance(x, dict)])

        # Normalize car/score fields.
        normalized = []
        for row in rows:
            car_no = None
            for ck in ("carNo", "carNum", "car_number", "car"):
                raw = row.get(ck)
                if raw is not None:
                    car_no = str(raw).strip()
                    break
            score = None
            for sk in ("score", "congestion", "congestionScore", "crowd", "value"):
                raw = row.get(sk)
                if raw is not None:
                    score = self.to_float(raw)
                    if score is not None:
                        break
            if car_no and score is not None:
                normalized.append({"car": car_no, "score": score, "raw": row})
        return normalized

    def get_tmap_subway_car_congestion(self, route_name: str | None, station_name: str | None):
        if not self.tmap_app_key:
            return None
        route_nm = self.normalize_route_name_for_tmap(route_name)
        station_nm = str(station_name or "").strip()
        if not route_nm or not station_nm:
            return None

        now = datetime.now(ZoneInfo("Asia/Seoul"))
        data = self.tmap_service.get_subway_car_congestion(
            route_name=route_nm,
            station_name=station_nm,
            dow=self.weekday_to_tmap_dow(now),
            hh=now.hour,
        )
        rows = self.extract_tmap_congestion_rows(data)
        if not rows:
            return None
        least = min(rows, key=lambda x: float(x.get("score") or 9999.0))
        return {
            "routeNm": route_nm,
            "stationNm": station_nm,
            "leastCar": least.get("car"),
            "leastScore": least.get("score"),
            "cars": rows,
        }

    def get_odsay_path(self, sx: float, sy: float, ex: float, ey: float, search_path_type: int = 0):
        if not self.odsay_api_key:
            return None
        query = urllib.parse.urlencode(
            {
                "apiKey": self.odsay_api_key,
                "SX": sx,
                "SY": sy,
                "EX": ex,
                "EY": ey,
                "SearchPathType": search_path_type,  # 0=all, 1=subway
            }
        )
        url = f"https://api.odsay.com/v1/api/searchPubTransPathT?{query}"
        data = self._http_get_json(url, timeout=8)
        if not isinstance(data, dict):
            return None
        if data.get("error"):
            self.log(f"[SeoulInfo] ODSAY path error: {data.get('error')}")
        result = data.get("result", {})
        paths = result.get("path") if isinstance(result, dict) else None
        if isinstance(paths, list) and paths:
            return paths[0] if isinstance(paths[0], dict) else None
        return None

    def parse_odsay_strategy(self, path_obj: dict):
        if not isinstance(path_obj, dict):
            return {}
        info = path_obj.get("info", {}) if isinstance(path_obj.get("info"), dict) else {}
        sub_paths = path_obj.get("subPath", []) if isinstance(path_obj.get("subPath"), list) else []

        first_ride = None
        for seg in sub_paths:
            if not isinstance(seg, dict):
                continue
            traffic_type = self.to_int(seg.get("trafficType"))
            if traffic_type in (1, 2):
                first_ride = seg
                break

        transfer_bus = self.to_int(info.get("busTransitCount"))
        transfer_subway = self.to_int(info.get("subwayTransitCount"))
        strategy = {
            "totalTimeMinutes": self.to_int(info.get("totalTime")),
            "payment": self.to_int(info.get("payment")),
            "transferCount": transfer_bus if transfer_bus is not None else transfer_subway,
            "firstMode": None,
            "firstBoardName": None,
            "firstDirection": None,
            "firstStartLat": self.to_float(first_ride.get("startY")) if isinstance(first_ride, dict) else None,
            "firstStartLng": self.to_float(first_ride.get("startX")) if isinstance(first_ride, dict) else None,
            "busNumbers": [],
            "subwayLine": None,
            "subwayLegs": [],
            "firstEtaMinutes": None,
            "nextEtaMinutes": None,
        }

        if isinstance(first_ride, dict):
            tt = self.to_int(first_ride.get("trafficType"))
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
            if self.to_int(seg.get("trafficType")) != 1:
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

    def _coerce_tmap_eta_minutes(self, raw) -> int | None:
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            n = float(raw)
            if n <= 0:
                return None
            if n > 7200:
                return None
            if n > 240:
                return max(1, int(round(n / 60.0)))
            return max(1, int(round(n)))
        text = str(raw).strip()
        if not text:
            return None
        parsed = self.parse_eta_minutes_from_message(text)
        if parsed is not None:
            return parsed
        direct = self.to_int(text)
        if direct is None or direct <= 0:
            return None
        if direct > 7200:
            return None
        if direct > 240:
            return max(1, int(round(direct / 60.0)))
        return max(1, direct)

    def _extract_tmap_eta_candidates(self, data_obj) -> list[int]:
        key_re = re.compile(r"(remain|left|wait|arrival|arrive|eta)", flags=re.IGNORECASE)
        out: list[int] = []
        stack = [data_obj]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                for k, v in cur.items():
                    if isinstance(v, (dict, list)):
                        stack.append(v)
                    if key_re.search(str(k)):
                        val = self._coerce_tmap_eta_minutes(v)
                        if val is not None:
                            out.append(val)
            elif isinstance(cur, list):
                stack.extend(cur)
        uniq = sorted({int(x) for x in out if isinstance(x, int) and x > 0})
        return [x for x in uniq if x <= 120]

    def parse_tmap_strategy(self, route_obj: dict | None, search_dttm: str | None = None, search_label: str | None = None):
        if not isinstance(route_obj, dict):
            return {}
        meta = route_obj.get("metaData", {}) if isinstance(route_obj.get("metaData"), dict) else {}
        plan = meta.get("plan", {}) if isinstance(meta.get("plan"), dict) else {}
        itineraries = plan.get("itineraries") if isinstance(plan.get("itineraries"), list) else []
        if not itineraries or not isinstance(itineraries[0], dict):
            return {}
        it0 = itineraries[0]
        legs = it0.get("legs") if isinstance(it0.get("legs"), list) else []

        first_ride = None
        bus_numbers: list[str] = []
        subway_legs: list[dict[str, str]] = []
        service_vals: list[int] = []

        for leg in legs:
            if not isinstance(leg, dict):
                continue
            mode = str(leg.get("mode") or "").strip().upper()
            if mode in {"WALK", "TRANSFER", "ETC", ""}:
                continue
            if first_ride is None:
                first_ride = leg

            svc = self.to_int(leg.get("service"))
            if svc is not None:
                service_vals.append(svc)

            route_name = str(leg.get("route") or "").strip()
            start = leg.get("start", {}) if isinstance(leg.get("start"), dict) else {}
            end = leg.get("end", {}) if isinstance(leg.get("end"), dict) else {}
            start_name = str(start.get("name") or leg.get("startName") or "").strip()
            end_name = str(end.get("name") or leg.get("endName") or "").strip()
            direction = str(leg.get("routeDirection") or leg.get("direction") or leg.get("desc") or "").strip()

            if mode == "BUS":
                if route_name:
                    bus_numbers.append(route_name)
            if mode == "SUBWAY":
                subway_legs.append(
                    {
                        "line": route_name,
                        "start": start_name,
                        "end": end_name,
                        "direction": direction,
                    }
                )

        first_mode = None
        first_board = None
        first_direction = None
        first_start_lat = None
        first_start_lng = None
        subway_line = None
        if isinstance(first_ride, dict):
            mode = str(first_ride.get("mode") or "").strip().upper()
            if mode == "SUBWAY":
                first_mode = "subway"
            elif mode == "BUS":
                first_mode = "bus"
            start = first_ride.get("start", {}) if isinstance(first_ride.get("start"), dict) else {}
            first_board = str(start.get("name") or first_ride.get("startName") or "").strip() or None
            first_direction = str(first_ride.get("routeDirection") or first_ride.get("direction") or first_ride.get("desc") or "").strip() or None
            first_start_lat = self.to_float(start.get("lat") if isinstance(start, dict) else None)
            first_start_lng = self.to_float(start.get("lon") if isinstance(start, dict) else None)
            if first_mode == "subway":
                subway_line = str(first_ride.get("route") or "").strip() or None

        if not subway_line and subway_legs:
            line0 = str(subway_legs[0].get("line") or "").strip()
            subway_line = line0 or None

        total = self.to_int(it0.get("totalTime"))
        total_min = None
        if total is not None:
            total_min = int(round(total / 60)) if total > 240 else total
        fare = it0.get("fare", {}) if isinstance(it0.get("fare"), dict) else {}
        regular = fare.get("regular", {}) if isinstance(fare.get("regular"), dict) else {}
        payment = self.to_int(regular.get("totalFare"))

        service_known = bool(service_vals)
        service_available = None
        if service_known:
            service_available = any(v == 1 for v in service_vals)

        first_eta = None
        next_eta = None
        if first_mode == "subway" and isinstance(first_ride, dict):
            eta_candidates = self._extract_tmap_eta_candidates(first_ride)
            if not eta_candidates:
                eta_candidates = self._extract_tmap_eta_candidates(it0)
            if eta_candidates:
                first_eta = eta_candidates[0]
                larger = [x for x in eta_candidates[1:] if x > first_eta]
                if larger:
                    next_eta = larger[0]

        return {
            "totalTimeMinutes": total_min,
            "payment": payment,
            "transferCount": self.to_int(it0.get("transferCount")),
            "firstMode": first_mode,
            "firstBoardName": first_board,
            "firstDirection": first_direction,
            "firstStartLat": first_start_lat,
            "firstStartLng": first_start_lng,
            "busNumbers": [x for x in bus_numbers if x],
            "subwayLine": subway_line,
            "subwayLegs": [x for x in subway_legs if x.get("line") and x.get("start") and x.get("end")],
            "provider": "tmap",
            "serviceKnown": service_known,
            "serviceAvailable": service_available,
            "firstEtaMinutes": first_eta,
            "nextEtaMinutes": next_eta,
            "searchDttm": str(search_dttm or "").strip() or None,
            "searchDttmLabel": str(search_label or "").strip() or None,
        }

    def strategy_needs_odsay_backfill(self, strategy: dict) -> bool:
        if not isinstance(strategy, dict) or not strategy:
            return True
        first_mode = str(strategy.get("firstMode") or "").strip()
        if not first_mode:
            return True
        if not str(strategy.get("firstBoardName") or "").strip():
            return True
        if first_mode == "subway" and not str(strategy.get("subwayLine") or "").strip():
            return True
        if first_mode == "bus":
            nums = strategy.get("busNumbers")
            if not isinstance(nums, list) or not nums:
                return True
        return False

    def merge_strategy_with_fallback(self, primary: dict, fallback: dict) -> dict:
        if not isinstance(primary, dict):
            return fallback if isinstance(fallback, dict) else {}
        if not isinstance(fallback, dict):
            return primary
        merged = dict(primary)
        keys = [
            "totalTimeMinutes",
            "payment",
            "transferCount",
            "firstMode",
            "firstBoardName",
            "firstDirection",
            "firstStartLat",
            "firstStartLng",
            "subwayLine",
            "firstEtaMinutes",
            "nextEtaMinutes",
        ]
        for k in keys:
            v = merged.get(k)
            if v is None or (isinstance(v, str) and not v.strip()):
                fv = fallback.get(k)
                if fv is not None and (not isinstance(fv, str) or fv.strip()):
                    merged[k] = fv
        if (not isinstance(merged.get("busNumbers"), list)) or (not merged.get("busNumbers")):
            if isinstance(fallback.get("busNumbers"), list):
                merged["busNumbers"] = [x for x in fallback.get("busNumbers") if x]
        if (not isinstance(merged.get("subwayLegs"), list)) or (not merged.get("subwayLegs")):
            if isinstance(fallback.get("subwayLegs"), list):
                merged["subwayLegs"] = [x for x in fallback.get("subwayLegs") if isinstance(x, dict)]
        if merged.get("provider") == "tmap":
            merged["provider"] = "tmap+odsay"
        return merged
