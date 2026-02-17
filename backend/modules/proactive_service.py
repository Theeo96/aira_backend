class ProactiveService:
    def __init__(
        self,
        response_guard: dict,
        transit_turn_gate: dict,
        inject_live_context_now,
        log=print,
    ):
        self.response_guard = response_guard
        self.transit_turn_gate = transit_turn_gate
        self.inject_live_context_now = inject_live_context_now
        self.log = log

    def reset_response_gate(self, reason: str = ""):
        self.response_guard["active"] = False
        self.response_guard["context_sent"] = False
        self.response_guard["suppressed_audio_seen"] = False
        self.response_guard["block_direct_audio"] = False
        self.response_guard["block_direct_audio_until"] = 0.0
        self.response_guard["post_context_audio_hold_until"] = 0.0
        self.response_guard["active_since"] = 0.0
        self.response_guard["context_sent_at"] = 0.0
        self.response_guard["forced_intent_turn"] = None
        self.transit_turn_gate["until"] = 0.0
        if reason:
            self.log(f"[Guard] reset: {reason}")

    async def request_spoken_response_with_context(
        self,
        intent_tag: str,
        context_summary: str,
        action_instruction: str,
        tone: str = "neutral",
        style: str = "",
        complete_turn: bool = True,
    ):
        tone_key = str(tone or "neutral").strip().lower()
        tone_guide = {
            "urgent": "Tone: concise and urgent but calm.",
            "celebratory": "Tone: bright and congratulatory.",
            "empathetic": "Tone: warm and empathetic.",
            "neutral": "Tone: natural and concise.",
        }.get(tone_key, "Tone: natural and concise.")
        style_hint = str(style or "").strip()
        ctx = (
            f"[INTENT:{str(intent_tag or 'general')}]\n"
            f"[CONTEXT] {str(context_summary or '').strip()}\n"
            f"[STYLE] {tone_guide} "
            + (f"Additional style hint: {style_hint}. " if style_hint else "")
            + "\n"
            f"[ACTION] {str(action_instruction or '').strip()} "
            "Speak once only and do not repeat."
        )
        await self.inject_live_context_now(ctx, complete_turn=complete_turn)

    async def send_proactive_announcement(
        self,
        summary_text: str,
        tone: str = "neutral",
        style: str = "",
        add_followup_hint: bool = True,
    ):
        msg = str(summary_text or "").strip()
        if not msg:
            return
        self.reset_response_gate("before proactive alert")
        await self.request_spoken_response_with_context(
            intent_tag="proactive_alert",
            context_summary=msg,
            tone=tone,
            style=style,
            action_instruction=(
                "사용자에게 자연스럽게 먼저 알림을 전달하세요. "
                + ("마지막에 짧은 후속 안내 한 문장만 덧붙이세요." if add_followup_hint else "추가 멘트 없이 알림만 전달하세요.")
            ),
            complete_turn=True,
        )
        self.reset_response_gate("after proactive alert")
