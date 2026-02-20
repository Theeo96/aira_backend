from __future__ import annotations

import re
from typing import Callable


def fast_route_intent(
    text: str,
    active_timer: bool = False,
    destination_extractor: Callable[[str], str | None] | None = None,
    arrival_eta_query_checker: Callable[[str], bool] | None = None,
) -> dict | None:
    t = str(text or "").strip()
    if not t:
        return None
    norm = re.sub(r"\s+", "", t.lower())
    destination_extractor = destination_extractor or (lambda _text: None)
    arrival_eta_query_checker = arrival_eta_query_checker or (lambda _text: False)

    if active_timer and any(k in norm for k in ["지금말해", "바로말해", "바로", "지금", "취소", "그만", "중지"]):
        return {"intent": "timer_cancel", "destination": None, "source": "fast", "home_update": False, "timer_seconds": None}

    timer_match = re.search(r"(\d{1,3})\s*(초|분|시간)\s*(뒤|후)", t)
    if timer_match:
        n = int(timer_match.group(1))
        unit = timer_match.group(2)
        sec = n if unit == "초" else n * 60 if unit == "분" else n * 3600
        if 5 <= sec <= 21600:
            return {"intent": "timer", "destination": None, "source": "fast", "home_update": False, "timer_seconds": sec}

    if any(k in norm for k in ["미세먼지", "초미세", "대기질", "aqi"]):
        return {"intent": "air_quality", "destination": None, "source": "fast", "home_update": False, "timer_seconds": None}

    if any(k in norm for k in ["날씨", "기온", "강수", "비와", "비와?", "덥", "춥"]):
        return {"intent": "weather", "destination": None, "source": "fast", "home_update": False, "timer_seconds": None}

    if any(k in norm for k in ["맛집", "음식점", "식당", "밥집", "점심", "저녁", "먹을만한", "restaurant", "food"]):
        return {"intent": "restaurant", "destination": None, "source": "fast", "home_update": False, "timer_seconds": None}

    if any(k in norm for k in ["뉴스", "헤드라인", "기사"]):
        return {"intent": "news", "destination": None, "source": "fast", "home_update": False, "timer_seconds": None}

    if arrival_eta_query_checker(t):
        return {"intent": "subway_route", "destination": destination_extractor(t), "source": "fast", "home_update": False, "timer_seconds": None}

    if any(k in norm for k in ["시간표", "운행일정", "운행시간", "첫차", "막차"]):
        return {"intent": "subway_route", "destination": destination_extractor(t), "source": "fast", "home_update": False, "timer_seconds": None}

    return None
