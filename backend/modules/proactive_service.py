from __future__ import annotations

import re


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。！？])\s+")
_CLAUSE_SPLIT_RE = re.compile(r"(?:,|;|:|·| 그리고 | 하지만 | 그래서 )\s*")


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
            "celebratory": "Tone: bright and celebratory.",
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

    def _split_sentences(self, text: str) -> list[str]:
        msg = re.sub(r"\s+", " ", str(text or "").strip())
        if not msg:
            return []
        parts = [p.strip() for p in _SENTENCE_SPLIT_RE.split(msg) if p and p.strip()]
        if len(parts) > 1:
            return parts
        # Fallback for very long text without terminal punctuation.
        if len(msg) >= 120:
            clauses = [p.strip() for p in _CLAUSE_SPLIT_RE.split(msg) if p and p.strip()]
            if len(clauses) > 1:
                return clauses
        return [msg]

    def _hard_wrap(self, text: str, max_chars: int) -> list[str]:
        s = str(text or "").strip()
        if not s:
            return []
        max_chars = max(30, int(max_chars))
        out = []
        cur = s
        while len(cur) > max_chars:
            cut = cur.rfind(" ", 0, max_chars + 1)
            if cut < max_chars * 0.6:
                cut = max_chars
            piece = cur[:cut].strip()
            if piece:
                out.append(piece)
            cur = cur[cut:].strip()
        if cur:
            out.append(cur)
        return out

    def _compress_for_tts(self, text: str, max_chars: int, max_sentences: int) -> str:
        sentences = self._split_sentences(text)
        if not sentences:
            return ""
        max_chars = max(1, int(max_chars))
        max_sentences = max(1, int(max_sentences))
        chosen: list[str] = []
        for s in sentences:
            if len(chosen) >= max_sentences:
                break
            candidate = " ".join(chosen + [s]).strip()
            if len(candidate) > max_chars:
                remain = max_chars - len(" ".join(chosen)) - (1 if chosen else 0)
                if remain >= 20:
                    chosen.append(s[: max(0, remain - 3)].rstrip() + "...")
                break
            chosen.append(s)
        out = " ".join(chosen).strip()
        if len(out) > max_chars:
            out = out[: max(0, max_chars - 3)].rstrip() + "..."
        return out

    def _split_for_tts(
        self,
        text: str,
        chunk_max_sentences: int = 1,
        chunk_max_chars: int = 180,
    ) -> list[str]:
        sentences = self._split_sentences(text)
        if not sentences:
            return []

        chunk_max_sentences = max(1, int(chunk_max_sentences))
        chunk_max_chars = max(30, int(chunk_max_chars))

        chunks: list[str] = []
        cur: list[str] = []
        for s in sentences:
            if len(s) > chunk_max_chars:
                if cur:
                    chunks.append(" ".join(cur).strip())
                    cur = []
                chunks.extend(self._hard_wrap(s, chunk_max_chars))
                continue

            candidate = " ".join(cur + [s]).strip()
            if len(cur) >= chunk_max_sentences or len(candidate) > chunk_max_chars:
                if cur:
                    chunks.append(" ".join(cur).strip())
                cur = [s]
            else:
                cur.append(s)

        if cur:
            chunks.append(" ".join(cur).strip())
        return [c for c in chunks if c]

    async def send_proactive_announcement(
        self,
        summary_text: str,
        tone: str = "neutral",
        style: str = "",
        add_followup_hint: bool = True,
        max_chars: int = 220,
        max_sentences: int = 5,
        split_by_sentence: bool = False,
        chunk_max_sentences: int = 1,
        chunk_max_chars: int = 180,
    ):
        raw_msg = str(summary_text or "").strip()
        if not raw_msg:
            return

        if split_by_sentence:
            chunks = self._split_for_tts(
                text=raw_msg,
                chunk_max_sentences=chunk_max_sentences,
                chunk_max_chars=chunk_max_chars,
            )
        else:
            chunks = [
                self._compress_for_tts(
                    text=raw_msg,
                    max_chars=max_chars,
                    max_sentences=max_sentences,
                )
            ]
        chunks = [c for c in chunks if c]
        if not chunks:
            return

        self.reset_response_gate("before proactive alert")
        for i, chunk in enumerate(chunks):
            is_last = i == (len(chunks) - 1)
            if split_by_sentence and (not is_last):
                action_instruction = "Speak this chunk naturally in Korean. Deliver only this chunk and stop."
            else:
                action_instruction = (
                    "Deliver this alert naturally in Korean and stop."
                    if not add_followup_hint
                    else "Deliver this alert naturally in Korean. End with one short follow-up invitation."
                )
            await self.request_spoken_response_with_context(
                intent_tag="proactive_alert",
                context_summary=chunk,
                tone=tone,
                style=style,
                action_instruction=action_instruction,
                complete_turn=True,
            )
        self.reset_response_gate("after proactive alert")
