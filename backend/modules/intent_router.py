import json
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

    def _fallback(self, text: str):
        t = str(text or "")
        if any(k in t for k in ["뉴스", "헤드라인", "속보", "기사"]):
            return {"intent": "news", "destination": self.destination_extractor(t), "source": "fallback", "home_update": False}
        if any(k in t for k in ["지하철", "역", "방면", "열차", "몇 분"]):
            return {"intent": "subway_route", "destination": self.destination_extractor(t), "source": "fallback", "home_update": False}
        if any(k in t for k in ["버스", "정류장"]):
            return {"intent": "bus_route", "destination": self.destination_extractor(t), "source": "fallback", "home_update": False}
        if any(k in t for k in ["날씨", "비", "기온"]):
            return {"intent": "weather", "destination": self.destination_extractor(t), "source": "fallback", "home_update": False}
        if any(k in t for k in ["대기질", "미세먼지", "aqi"]):
            return {"intent": "air_quality", "destination": self.destination_extractor(t), "source": "fallback", "home_update": False}
        return {"intent": "commute_overview", "destination": self.destination_extractor(t), "source": "fallback", "home_update": False}

    def route(self, text: str):
        if not self.client:
            return self._fallback(text)

        system = (
            "Classify Korean commuter query intent. Return JSON only with keys: "
            "intent, destination, home_update. intent one of "
            "[subway_route,bus_route,weather,air_quality,news,commute_overview,general]. "
            "destination should be a concise place/station name or null. "
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
                    {"role": "user", "content": str(text or "")},
                ],
            )
            content = resp.choices[0].message.content
            data = json.loads(content) if content else {}
            intent = data.get("intent") if isinstance(data, dict) else None
            destination = data.get("destination") if isinstance(data, dict) else None
            home_update = bool(data.get("home_update")) if isinstance(data, dict) else False
            if intent not in {"subway_route", "bus_route", "weather", "air_quality", "news", "commute_overview", "general"}:
                return self._fallback(text)
            return {"intent": intent, "destination": destination, "source": "llm", "home_update": home_update}
        except Exception as e:
            print(f"[IntentRouter] route failed: {e}")
            if "DeploymentNotFound" in str(e):
                print("[IntentRouter] Disabling Azure router due to missing deployment. Using fallback routing.")
                self.client = None
            return self._fallback(text)

