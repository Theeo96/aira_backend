import json
import re
from typing import Callable, Optional

from openai import AzureOpenAI


class IntentRouter:
    def __init__(
        self,
        api_key: str | None,
        endpoint: str | None,
        api_version: str | None,
        model: str,
        destination_extractor: Optional[Callable[[str], str | None]] = None,
    ):
        self.client = None
        self.model = model
        self.destination_extractor = destination_extractor or (lambda _text: None)

        if not api_key or not endpoint:
            print("[IntentRouter] Azure OpenAI credentials missing. Fallback routing only.")
            return

        base_endpoint = endpoint
        if "/openai/v1" in base_endpoint:
            base_endpoint = base_endpoint.split("/openai/v1")[0]

        try:
            kwargs = {
                "api_key": api_key,
                "azure_endpoint": base_endpoint,
                "timeout": 4.0,
            }
            if api_version:
                kwargs["api_version"] = api_version
            self.client = AzureOpenAI(**kwargs)
            print("[IntentRouter] Azure OpenAI router initialized.")
        except Exception as e:
            print(f"[IntentRouter] init failed: {e}")
            self.client = None

    def _extract_timer_seconds(self, text: str):
        t = str(text or "").strip()
        if not t:
            return None
        has_timer_intent = any(
            k in t for k in ["말걸어", "알려줘", "알림", "깨워", "리마인드", "다시 말", "다시말", "브리핑"]
        )
        if not has_timer_intent:
            return None
        m = re.search(r"(\d{1,3})\s*(초|분|시간)\s*(뒤|후)", t)
        if not m:
            return None
        n = int(m.group(1))
        unit = m.group(2)
        sec = n if unit == "초" else n * 60 if unit == "분" else n * 3600
        if sec < 5 or sec > 21600:
            return None
        return sec

    def _fallback(self, text: str, active_timer: bool = False):
        t = str(text or "")
        if active_timer and any(k in t for k in ["지금", "바로", "지금 말", "지금 알려", "지금 해", "바로 해"]):
            return {
                "intent": "timer_cancel",
                "destination": None,
                "source": "fallback",
                "home_update": False,
                "timer_seconds": None,
            }
        if any(k in t for k in ["타이머 취소", "알림 취소", "타이머 꺼", "알림 꺼", "취소해", "취소", "해제", "그만"]):
            return {
                "intent": "timer_cancel",
                "destination": None,
                "source": "fallback",
                "home_update": False,
                "timer_seconds": None,
            }
        timer_sec = self._extract_timer_seconds(t)
        if timer_sec is not None:
            return {
                "intent": "timer",
                "destination": None,
                "source": "fallback",
                "home_update": False,
                "timer_seconds": timer_sec,
            }
        if any(k in t for k in ["뉴스", "헤드라인", "속보", "기사"]):
            return {"intent": "news", "destination": self.destination_extractor(t), "source": "fallback", "home_update": False, "timer_seconds": None}
        if any(k in t for k in ["지하철", "역", "방면", "열차", "몇 분"]):
            return {"intent": "subway_route", "destination": self.destination_extractor(t), "source": "fallback", "home_update": False, "timer_seconds": None}
        if any(k in t for k in ["버스", "정류장"]):
            return {"intent": "bus_route", "destination": self.destination_extractor(t), "source": "fallback", "home_update": False, "timer_seconds": None}
        if any(k in t for k in ["날씨", "비", "기온"]):
            return {"intent": "weather", "destination": self.destination_extractor(t), "source": "fallback", "home_update": False, "timer_seconds": None}
        if any(k in t for k in ["대기질", "미세먼지", "aqi"]):
            return {"intent": "air_quality", "destination": self.destination_extractor(t), "source": "fallback", "home_update": False, "timer_seconds": None}
        if any(k in t.lower() for k in ["restaurant", "food", "lunch", "dinner"]) or any(
            k in t for k in ["맛집", "음식점", "식당", "밥집", "먹을", "먹을만한", "추천해줘"]
        ):
            return {"intent": "restaurant", "destination": None, "source": "fallback", "home_update": False, "timer_seconds": None}
        return {"intent": "commute_overview", "destination": self.destination_extractor(t), "source": "fallback", "home_update": False, "timer_seconds": None}

    def route(self, text: str, active_timer: bool = False):
        if not self.client:
            return self._fallback(text, active_timer=active_timer)

        system = (
            "Classify Korean commuter query intent. Return JSON only with keys: "
            "intent, destination, home_update, timer_seconds. "
            "intent must be one of "
            "[subway_route,bus_route,weather,air_quality,restaurant,news,commute_overview,general,timer,timer_cancel]. "
            "destination should be a concise place/station name or null. "
            "For timer intent, set destination=null and timer_seconds as integer seconds from now. "
            "For timer_cancel intent, set destination=null and timer_seconds=null. "
            "If active_timer=true and user asks to do it now/immediately (e.g., '지금 말해줘', '바로 알려줘'), "
            "classify as timer_cancel. "
            "For non-timer intents, timer_seconds must be null. "
            "home_update must be true only when the user explicitly indicates home relocation/change "
            "(e.g., moved house, changed home location, says 'my home is now ...'). "
            "If user is just asking route to another place (friend's home, visit, outing), home_update must be false."
        )

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"active_timer={str(bool(active_timer)).lower()}\nuser_text={str(text or '')}"},
                ],
            )
            content = resp.choices[0].message.content
            data = json.loads(content) if content else {}
            intent = data.get("intent") if isinstance(data, dict) else None
            destination = data.get("destination") if isinstance(data, dict) else None
            home_update = bool(data.get("home_update")) if isinstance(data, dict) else False
            timer_seconds = None
            if isinstance(data, dict):
                raw_timer = data.get("timer_seconds")
                try:
                    timer_seconds = int(raw_timer) if raw_timer is not None else None
                except Exception:
                    timer_seconds = None

            if intent not in {"subway_route", "bus_route", "weather", "air_quality", "restaurant", "news", "commute_overview", "general", "timer", "timer_cancel"}:
                return self._fallback(text, active_timer=active_timer)

            if intent == "timer" and (timer_seconds is None or timer_seconds < 5 or timer_seconds > 21600):
                timer_seconds = self._extract_timer_seconds(text)

            return {
                "intent": intent,
                "destination": destination,
                "source": "llm",
                "home_update": home_update,
                "timer_seconds": timer_seconds,
            }
        except Exception as e:
            print(f"[IntentRouter] route failed: {e}")
            if "DeploymentNotFound" in str(e):
                print("[IntentRouter] Disabling Azure router due to missing deployment. Using fallback routing.")
                self.client = None
            return self._fallback(text, active_timer=active_timer)
