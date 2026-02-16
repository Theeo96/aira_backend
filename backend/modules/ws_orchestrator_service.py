import time


class WsOrchestratorService:
    ROUTING_INTENTS = {
        "subway_route",
        "bus_route",
        "commute_overview",
        "weather",
        "air_quality",
        "news",
        "news_detail",
        "news_followup",
    }

    TRANSIT_INTENTS = {"subway_route", "bus_route", "commute_overview"}

    CONTEXT_PRIORITY_INTENTS = {
        "subway_route",
        "bus_route",
        "commute_overview",
        "weather",
        "air_quality",
        "news",
        "news_detail",
        "news_followup",
    }

    def arm_live_response_gate(self, response_guard: dict, transit_turn_gate: dict, intent: str):
        env_intent = intent in {"weather", "air_quality"}
        response_guard["active"] = True
        response_guard["context_sent"] = False
        response_guard["suppressed_audio_seen"] = False
        response_guard["block_direct_audio"] = True
        response_guard["block_direct_audio_until"] = time.monotonic() + (5.0 if env_intent else 4.0)
        response_guard["forced_intent_turn"] = intent
        if not env_intent:
            transit_turn_gate["until"] = max(
                float(transit_turn_gate.get("until") or 0.0),
                time.monotonic() + 1.2,
            )
        else:
            transit_turn_gate["until"] = time.monotonic()

    def extend_post_context_gate(self, transit_turn_gate: dict):
        transit_turn_gate["until"] = max(
            float(transit_turn_gate.get("until") or 0.0),
            time.monotonic() + 0.8,
        )

    def build_action_instruction(self, intent: str):
        action_instruction = (
            "사용자의 최신 질문에 지금 바로 한국어로 답하세요. "
            "최종 답변은 한 번만, 간결하게 말하세요. "
            "요약/반복/재확인 질문을 추가하지 마세요. "
            "제공된 요약에 데이터가 있으면 바로 그 값을 말하고, "
            "요약이 명시적으로 데이터 없음일 때만 없다고 말하세요."
        )
        if intent in {"weather", "air_quality"}:
            action_instruction += " 목적지 관련 질문은 하지 마세요."
        if intent in {"news_detail", "news_followup"}:
            action_instruction += (
                " 기사 전문을 낭독하지 말고, 핵심만 2~3문장으로 요약하세요. "
                "추가 질문에는 같은 기사 맥락에서 이어서 답하세요."
            )
        return action_instruction

    def merge_context_summary(self, live_summary: str, guidance: list[str]):
        context_summary = str(live_summary or "").strip()
        if guidance:
            context_summary = (
                context_summary
                + "\n[GUIDE] "
                + " ".join(guidance)
            ).strip()
        return context_summary

