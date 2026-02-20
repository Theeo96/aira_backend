import time


class WsOrchestratorService:
    ROUTING_INTENTS = {
        "subway_route",
        "bus_route",
        "commute_overview",
        "weather",
        "air_quality",
        "restaurant",
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
        "restaurant",
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
        # Keep this short to reduce latency while still blocking stale pre-context audio.
        response_guard["block_direct_audio_until"] = time.monotonic() + (2.2 if env_intent else 2.0)
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
            "Answer the user's latest question directly in Korean. "
            "Use provided live context first. "
            "Give exactly one final answer turn. "
            "Do not repeat the same content. "
            "Do not add fallback lines like 'cannot check now' if context already contains usable values. "
            "Only say data is unavailable when context explicitly indicates missing data."
        )
        if intent in {"weather", "air_quality"}:
            action_instruction += " Do not ask destination-related follow-up questions."
        if intent in {"news_detail", "news_followup"}:
            action_instruction += (
                " Do not read article text verbatim. "
                "Summarize 핵심만 2~3문장으로 전달하고, "
                "follow-up 질문은 같은 기사 맥락으로 이어서 답변하세요."
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
