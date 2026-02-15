import time
from typing import Callable, Optional


class SeoulLiveService:
    def __init__(
        self,
        default_destination: str,
        normalize_place_name: Callable[[str | None], str],
        build_live_summary: Callable[..., dict],
        get_weather_only: Callable[[float, float], dict],
        get_air_only: Callable[[float, float], dict],
        get_weather_and_air: Callable[[float, float], tuple],
        is_env_cache_fresh: Callable[[dict | None, float | None, float | None], bool],
        extract_news_topic: Optional[Callable[[str], str | None]] = None,
        get_news_headlines: Optional[Callable[[str | None, int], list]] = None,
    ):
        self.default_destination = default_destination
        self.normalize_place_name = normalize_place_name
        self.build_live_summary = build_live_summary
        self.get_weather_only = get_weather_only
        self.get_air_only = get_air_only
        self.get_weather_and_air = get_weather_and_air
        self.is_env_cache_fresh = is_env_cache_fresh
        self.extract_news_topic = extract_news_topic
        self.get_news_headlines = get_news_headlines

    def execute_tools_for_intent(
        self,
        intent: str,
        lat: float | None,
        lng: float | None,
        destination_name: str | None,
        env_cache: dict | None = None,
        user_text: str | None = None,
    ):
        if intent == "news":
            topic = ""
            if self.extract_news_topic:
                topic = str(self.extract_news_topic(user_text or "") or "").strip()
            if not topic:
                topic = str(destination_name or "").strip() or "최신 뉴스"
            headlines = []
            if self.get_news_headlines:
                headlines = self.get_news_headlines(topic=topic, limit=3) or []
            if headlines:
                summary = f"{topic} 기준 최신 뉴스입니다. " + " / ".join([f"{idx+1}. {h}" for idx, h in enumerate(headlines)])
            else:
                summary = "뉴스 데이터를 현재 받지 못했어요."
            return {
                "station": None,
                "arrivals": [],
                "speechSummary": summary,
                "firstEtaMinutes": None,
                "nextEtaMinutes": None,
                "walkToStationMinutes": None,
                "walkToBusStopMinutes": None,
                "decision": "unknown",
                "busStopName": None,
                "busNumbers": [],
                "firstMode": None,
                "firstDirection": None,
                "weather": {},
                "air": {},
                "news": {"topic": topic, "headlines": headlines},
                "homeConfigured": False,
                "destinationName": destination_name,
                "destinationRequested": bool(destination_name),
            }

        if intent in {"weather", "air_quality"}:
            weather = {}
            air = {}
            cache_weather = env_cache.get("weather") if isinstance(env_cache, dict) else None
            cache_air = env_cache.get("air") if isinstance(env_cache, dict) else None
            cache_ts = float(env_cache.get("ts") or 0.0) if isinstance(env_cache, dict) else 0.0
            cache_fresh = self.is_env_cache_fresh(env_cache, lat, lng)
            if cache_fresh:
                if isinstance(cache_weather, dict):
                    weather = cache_weather
                if isinstance(cache_air, dict):
                    air = cache_air
            elif lat is not None and lng is not None:
                weather, air = self.get_weather_and_air(lat, lng)
                if isinstance(env_cache, dict):
                    env_cache["weather"] = weather or {}
                    env_cache["air"] = air or {}
                    env_cache["lat"] = lat
                    env_cache["lng"] = lng
                    env_cache["ts"] = time.monotonic()
            live = {
                "station": None,
                "arrivals": [],
                "speechSummary": "",
                "firstEtaMinutes": None,
                "nextEtaMinutes": None,
                "walkToStationMinutes": None,
                "walkToBusStopMinutes": None,
                "decision": "unknown",
                "busStopName": None,
                "busNumbers": [],
                "firstMode": None,
                "firstDirection": None,
                "weather": weather,
                "air": air,
                "homeConfigured": False,
                "destinationName": destination_name,
                "destinationRequested": bool(destination_name),
                "envCacheFresh": cache_fresh,
                "envCacheTs": cache_ts,
            }
            parts = []
            if intent == "weather":
                w = live.get("weather") or {}
                t = w.get("tempC")
                t_max = w.get("todayMaxC")
                t_min = w.get("todayMinC")
                sky = w.get("skyText")
                pop = w.get("precipProbPct")
                rain = w.get("rainMm")
                precip = w.get("precipitationMm")
                if t is not None:
                    parts.append(f"현재 기온은 약 {int(round(float(t)))}도입니다.")
                if t_max is not None and t_min is not None:
                    parts.append(f"오늘 최고/최저는 {int(round(float(t_max)))}/{int(round(float(t_min)))}도예요.")
                if pop is not None:
                    parts.append(f"강수확률은 약 {int(pop)}%입니다.")
                if rain is not None or precip is not None:
                    parts.append(f"강수는 현재 약 {rain or precip}mm 수준입니다.")
                if sky:
                    parts.append(f"하늘 상태는 {sky}입니다.")
                if not parts:
                    parts.append("날씨 데이터를 현재 받지 못했어요.")
            else:
                a = live.get("air") or {}
                if a.get("usAqi") is not None:
                    parts.append(f"현재 대기질은 US AQI {a.get('usAqi')}입니다.")
                if a.get("grade"):
                    parts.append(f"수준은 {a.get('grade')}입니다.")
                if a.get("pm25") is not None:
                    parts.append(f"초미세먼지는 {a.get('pm25')}입니다.")
                if a.get("pm10") is not None:
                    parts.append(f"미세먼지는 {a.get('pm10')}입니다.")
                if not parts:
                    parts.append("대기질 데이터를 현재 받지 못했어요.")
            live["speechSummary"] = " ".join([p for p in parts if p]).strip()
            return live

        is_default_destination = (
            self.normalize_place_name(destination_name) == self.normalize_place_name(self.default_destination)
            if destination_name
            else True
        )
        prefer_subway = intent == "subway_route" or (intent == "commute_overview" and is_default_destination)
        detailed_subway = (intent in {"subway_route", "commute_overview"}) and (not is_default_destination)
        live = self.build_live_summary(
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
        else:
            parts.append(str(live.get("speechSummary", "")))

        merged = " ".join([p for p in parts if p]).strip()
        live["speechSummary"] = merged or str(live.get("speechSummary", ""))
        return live
