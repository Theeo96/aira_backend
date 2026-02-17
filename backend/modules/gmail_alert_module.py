import os
import re
import json
import time
import socket
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import List, Dict, Set, Tuple
from openai import AzureOpenAI


def _decode_mime_header(value: str) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    decoded = []
    for text, enc in parts:
        if isinstance(text, bytes):
            try:
                decoded.append(text.decode(enc or "utf-8", errors="ignore"))
            except Exception:
                decoded.append(text.decode("utf-8", errors="ignore"))
        else:
            decoded.append(str(text))
    return "".join(decoded).strip()


def _extract_text_body(msg: email.message.Message, max_len: int = 1200) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ctype = str(part.get_content_type() or "").lower()
            disp = str(part.get("Content-Disposition") or "").lower()
            if ctype == "text/plain" and "attachment" not in disp:
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                try:
                    text = payload.decode(charset, errors="ignore")
                except Exception:
                    text = payload.decode("utf-8", errors="ignore")
                return re.sub(r"\s+", " ", text).strip()[:max_len]
        return ""
    payload = msg.get_payload(decode=True) or b""
    charset = msg.get_content_charset() or "utf-8"
    try:
        text = payload.decode(charset, errors="ignore")
    except Exception:
        text = payload.decode("utf-8", errors="ignore")
    return re.sub(r"\s+", " ", text).strip()[:max_len]


def _safe_email_ts(msg: email.message.Message) -> float:
    raw = str(msg.get("Date") or "").strip()
    if not raw:
        return 0.0
    try:
        dt = parsedate_to_datetime(raw)
        if not dt:
            return 0.0
        return float(dt.timestamp())
    except Exception:
        return 0.0


class GmailAlertModule:
    def __init__(self):
        self.user = os.getenv("GMAIL_IMAP_USER", "").strip()
        self.app_password = os.getenv("GMAIL_IMAP_APP_PASSWORD", "").strip()
        self.mailbox = os.getenv("GMAIL_IMAP_MAILBOX", "INBOX").strip() or "INBOX"
        self.keyword_raw = os.getenv(
            "GMAIL_URGENT_KEYWORDS",
            "긴급,중요,즉시,ASAP,urgent,action required,deadline,마감,에러,장애,failure,보안,security,결제,청구,환불,승인요청,미납",
        )
        self.urgent_keywords = [x.strip().lower() for x in self.keyword_raw.split(",") if x.strip()]
        self.classify_mode = os.getenv("GMAIL_URGENT_CLASSIFY_MODE", "llm_only").strip().lower()
        self.use_llm = os.getenv("GMAIL_URGENT_USE_LLM", "true").strip().lower() in {"1", "true", "yes", "on"}
        self.require_llm = os.getenv("GMAIL_URGENT_REQUIRE_LLM", "true").strip().lower() in {"1", "true", "yes", "on"}
        self.llm_model = os.getenv("GMAIL_URGENT_LLM_MODEL") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or "gpt-4o-mini"
        try:
            self.llm_threshold = float(os.getenv("GMAIL_URGENT_LLM_CONFIDENCE", "0.55"))
        except Exception:
            self.llm_threshold = 0.55
        self.debug = os.getenv("GMAIL_ALERT_DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}

        self._llm_warned = False
        self._llm_debug_count = 0
        self.llm_client = self._build_llm_client()

        self.state_file = os.path.join(os.path.dirname(__file__), "gmail_alert_state.json")
        self.delivered_ids: Set[str] = set()
        self.last_disconnect_by_user: Dict[str, float] = {}
        self.session_poll_from: Dict[str, float] = {}
        self._load_state()
        try:
            self.live_poll_fallback_sec = float(os.getenv("GMAIL_LIVE_POLL_FALLBACK_SEC", "20"))
        except Exception:
            self.live_poll_fallback_sec = 20.0
        try:
            self.backlog_scan_limit = int(os.getenv("GMAIL_BACKLOG_SCAN_LIMIT", "40"))
        except Exception:
            self.backlog_scan_limit = 40
        try:
            self.live_scan_limit = int(os.getenv("GMAIL_LIVE_SCAN_LIMIT", "25"))
        except Exception:
            self.live_scan_limit = 25

    @property
    def enabled(self) -> bool:
        return bool(self.user and self.app_password)

    def _build_llm_client(self):
        if not self.use_llm:
            return None
        api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "").strip()
        if not api_key or not endpoint:
            return None
        base_endpoint = endpoint
        if "/openai/v1" in base_endpoint:
            base_endpoint = base_endpoint.split("/openai/v1")[0]
        try:
            kwargs = {"api_key": api_key, "azure_endpoint": base_endpoint, "timeout": 5.0}
            if api_version:
                kwargs["api_version"] = api_version
            return AzureOpenAI(**kwargs)
        except Exception:
            return None

    def _load_state(self):
        try:
            if not os.path.exists(self.state_file):
                return
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            ids = data.get("delivered_ids", [])
            if isinstance(ids, list):
                self.delivered_ids = set(str(x) for x in ids if x)
            dmap = data.get("last_disconnect_by_user", {})
            if isinstance(dmap, dict):
                self.last_disconnect_by_user = {
                    str(k): float(v)
                    for k, v in dmap.items()
                    if v is not None
                }
        except Exception as e:
            print(f"[GmailAlert] state load failed: {e}")

    def _save_state(self):
        try:
            payload = {
                "delivered_ids": list(self.delivered_ids)[-5000:],
                "last_disconnect_by_user": self.last_disconnect_by_user,
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
        except Exception as e:
            print(f"[GmailAlert] state save failed: {e}")

    def _keyword_candidate(self, subject: str, body: str, sender: str) -> bool:
        text = f"{subject} {body} {sender}".lower()
        return any(k in text for k in self.urgent_keywords)

    def _tone_hint(self, subject: str, body: str) -> str:
        t = f"{subject} {body}".lower()
        if any(k in t for k in ["축하", "congrats", "congratulation", "합격", "승진", "당첨"]):
            return "celebratory"
        if any(k in t for k in ["부고", "조의", "삼가", "sad", "condolence", "별세", "사망"]):
            return "empathetic"
        if any(k in t for k in ["긴급", "urgent", "즉시", "보안", "security", "마감", "장애", "결제 실패"]):
            return "urgent"
        return "neutral"

    def _llm_is_urgent(self, subject: str, body: str, sender: str) -> Tuple[bool, float, str, str, str]:
        if not self.llm_client:
            return (False, 0.0, "llm_unavailable", self._tone_hint(subject, body), "")
        prompt = (
            "Classify whether this email is urgent enough for proactive voice alert. "
            "Return JSON only with keys: urgent(boolean), confidence(number 0..1), reason(string), "
            "tone(one of urgent|celebratory|empathetic|neutral), style(string). "
            "Urgent examples: security alert, payment failure, deadline today, outage, manager immediate action. "
            "Non-urgent examples: newsletter, marketing, general updates, event notice."
        )
        user_payload = {"subject": subject[:240], "sender": sender[:200], "body_preview": body[:900]}
        try:
            resp = self.llm_client.chat.completions.create(
                model=self.llm_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
                ],
            )
            content = resp.choices[0].message.content if resp and resp.choices else ""
            data = json.loads(content) if content else {}
            urgent = bool(data.get("urgent")) if isinstance(data, dict) else False
            conf = float(data.get("confidence")) if isinstance(data, dict) and data.get("confidence") is not None else 0.0
            reason = str(data.get("reason") or "") if isinstance(data, dict) else ""
            tone = str(data.get("tone") or "").strip().lower() if isinstance(data, dict) else ""
            style = str(data.get("style") or "").strip() if isinstance(data, dict) else ""
            if tone not in {"urgent", "celebratory", "empathetic", "neutral"}:
                tone = self._tone_hint(subject, body)
            decision = urgent and conf >= self.llm_threshold
            if self.debug:
                self._llm_debug_count += 1
                # Throttle noisy non-urgent logs to avoid flooding console during backlog scans.
                if decision or (self._llm_debug_count % 20 == 0):
                    print(
                        f"[GmailAlert] llm decision={decision} conf={conf:.2f} threshold={self.llm_threshold:.2f} "
                        f"tone={tone} reason={reason}"
                    )
            return (decision, conf, reason, tone, style)
        except Exception as e:
            return (False, 0.0, f"llm_error:{e}", self._tone_hint(subject, body), "")

    def _build_alert_text(self, sender: str, subject: str) -> str:
        sender_short = sender.split("<")[0].strip() if sender else "보낸 사람 미상"
        return f"긴급 메일이 왔어요. {sender_short}에서 '{subject}' 관련 메일입니다."

    def _is_urgent(self, subject: str, body: str, sender: str) -> Tuple[bool, float, str, str, str]:
        # hybrid mode: keyword -> llm
        if self.classify_mode == "hybrid":
            if not self._keyword_candidate(subject=subject, body=body, sender=sender):
                return (False, 0.0, "keyword_filtered", self._tone_hint(subject, body), "")

        # llm_only or hybrid (llm stage)
        if self.use_llm:
            if self.llm_client:
                return self._llm_is_urgent(subject=subject, body=body, sender=sender)
            if not self._llm_warned:
                print("[GmailAlert] LLM classifier unavailable.")
                self._llm_warned = True
            return ((not self.require_llm), 0.0, "llm_unavailable", self._tone_hint(subject, body), "")

        # keyword-only fallback
        return (
            self._keyword_candidate(subject=subject, body=body, sender=sender),
            0.0,
            "keyword_only",
            self._tone_hint(subject, body),
            "",
        )

    def _fetch_messages_between(self, start_ts: float, end_ts: float, max_scan: int = 80) -> List[Dict[str, str]]:
        if not self.enabled:
            return []
        alerts: List[Dict[str, str]] = []
        mail = None
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            mail.login(self.user, self.app_password)
            mail.select(self.mailbox, readonly=True)

            typ, data = mail.search(None, "ALL")
            if typ != "OK" or not data or not data[0]:
                if self.debug:
                    print("[GmailAlert] search returned empty")
                return []

            msg_nums = data[0].split()
            if self.debug:
                print(f"[GmailAlert] mailbox_count={len(msg_nums)} scan_limit={max_scan} window=({int(start_ts)}~{int(end_ts)})")
            for num in reversed(msg_nums[-max_scan:]):
                fetch_typ, fetch_data = mail.fetch(num, "(RFC822)")
                if fetch_typ != "OK" or not fetch_data:
                    continue
                raw = None
                for row in fetch_data:
                    if isinstance(row, tuple) and len(row) >= 2:
                        raw = row[1]
                        break
                if not raw:
                    continue
                msg = email.message_from_bytes(raw)
                msg_ts = _safe_email_ts(msg)
                if msg_ts <= 0:
                    if self.debug:
                        print("[GmailAlert] skip: invalid date header")
                    continue
                if msg_ts < start_ts or msg_ts > end_ts:
                    continue

                msg_id = str(msg.get("Message-ID") or f"num:{num.decode(errors='ignore')}")
                if msg_id in self.delivered_ids:
                    if self.debug:
                        print(f"[GmailAlert] skip: already delivered id={msg_id}")
                    continue

                subject = _decode_mime_header(str(msg.get("Subject") or "제목 없음"))
                sender = _decode_mime_header(str(msg.get("From") or "보낸 사람 미상"))
                body = _extract_text_body(msg)
                ok, conf, reason, tone, style = self._is_urgent(subject=subject, body=body, sender=sender)
                if not ok:
                    if self.debug:
                        print(f"[GmailAlert] skip: non-urgent subject='{subject[:80]}' reason={reason} conf={conf}")
                    continue
                self.delivered_ids.add(msg_id)
                alerts.append(
                    {
                        "id": msg_id,
                        "sender": sender,
                        "subject": subject,
                        "summary": self._build_alert_text(sender=sender, subject=subject),
                        "llm_confidence": conf,
                        "llm_reason": reason,
                        "tone": tone,
                        "style": style,
                    }
                )
        except Exception as e:
            print(f"[GmailAlert] fetch error: {e}")
        finally:
            try:
                if mail is not None:
                    mail.logout()
            except Exception:
                pass
        if alerts:
            self._save_state()
        return alerts

    def _fetch_unseen_recent(self, max_scan: int = 60) -> List[Dict[str, str]]:
        """
        Date header 파싱 실패/지연 케이스 보완용:
        UNSEEN 메일 중 최신 max_scan개를 긴급 판정한다.
        """
        if not self.enabled:
            return []
        alerts: List[Dict[str, str]] = []
        mail = None
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            mail.login(self.user, self.app_password)
            mail.select(self.mailbox, readonly=True)

            typ, data = mail.search(None, "UNSEEN")
            if typ != "OK" or not data or not data[0]:
                return []
            msg_nums = data[0].split()
            for num in reversed(msg_nums[-max_scan:]):
                fetch_typ, fetch_data = mail.fetch(num, "(RFC822)")
                if fetch_typ != "OK" or not fetch_data:
                    continue
                raw = None
                for row in fetch_data:
                    if isinstance(row, tuple) and len(row) >= 2:
                        raw = row[1]
                        break
                if not raw:
                    continue
                msg = email.message_from_bytes(raw)
                msg_id = str(msg.get("Message-ID") or f"num:{num.decode(errors='ignore')}")
                if msg_id in self.delivered_ids:
                    continue
                subject = _decode_mime_header(str(msg.get("Subject") or "제목 없음"))
                sender = _decode_mime_header(str(msg.get("From") or "보낸 사람 미상"))
                body = _extract_text_body(msg)
                ok, conf, reason, tone, style = self._is_urgent(subject=subject, body=body, sender=sender)
                if not ok:
                    continue
                self.delivered_ids.add(msg_id)
                alerts.append(
                    {
                        "id": msg_id,
                        "sender": sender,
                        "subject": subject,
                        "summary": self._build_alert_text(sender=sender, subject=subject),
                        "llm_confidence": conf,
                        "llm_reason": reason,
                        "tone": tone,
                        "style": style,
                    }
                )
        except Exception as e:
            print(f"[GmailAlert] unseen fetch error: {e}")
        finally:
            try:
                if mail is not None:
                    mail.logout()
            except Exception:
                pass
        if alerts:
            self._save_state()
        return alerts

    def begin_session(self, user_id: str, connected_at_ts: float | None = None) -> List[Dict[str, str]]:
        now_ts = float(connected_at_ts or time.time())
        uid = str(user_id or "").strip().lower()
        default_lookback = float(os.getenv("GMAIL_BACKLOG_DEFAULT_LOOKBACK_SEC", "21600"))  # 6h
        start_ts = float(self.last_disconnect_by_user.get(uid, now_ts - default_lookback))
        self.session_poll_from[uid] = now_ts
        if start_ts > now_ts:
            start_ts = now_ts - 60.0
        alerts = self._fetch_messages_between(
            start_ts=start_ts,
            end_ts=now_ts,
            max_scan=max(10, int(self.backlog_scan_limit)),
        )
        # 보완: 시간 헤더 이슈로 window 필터에서 빠진 UNSEEN 긴급 메일도 한 번 더 확인
        if not alerts:
            fallback_alerts = self._fetch_unseen_recent(max_scan=max(10, int(self.live_scan_limit)))
            if fallback_alerts:
                alerts = fallback_alerts
        return alerts

    def poll_live_alerts(self, user_id: str, max_alerts: int = 1) -> List[Dict[str, str]]:
        uid = str(user_id or "").strip().lower()
        now_ts = time.time()
        start_ts = float(self.session_poll_from.get(uid, now_ts - 120.0))
        alerts = self._fetch_messages_between(
            start_ts=start_ts,
            end_ts=now_ts,
            max_scan=max(10, int(self.live_scan_limit)),
        )
        self.session_poll_from[uid] = now_ts
        if max_alerts and len(alerts) > max_alerts:
            return alerts[:max_alerts]
        return alerts

    def wait_next_live_alert(self, user_id: str, idle_timeout_sec: float = 120.0, max_alerts: int = 1) -> List[Dict[str, str]]:
        """
        Wait for new mail event using IMAP IDLE, then fetch urgent alerts in the new window.
        Returns [] when timeout/no new mail.
        """
        uid = str(user_id or "").strip().lower()
        if uid not in self.session_poll_from:
            self.session_poll_from[uid] = time.time()
        start_ts = float(self.session_poll_from.get(uid) or time.time())

        if not self.enabled:
            return []

        mail = None
        exists_event = False
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            mail.login(self.user, self.app_password)
            mail.select(self.mailbox, readonly=True)

            # Enter IDLE (best-effort, using imaplib low-level calls).
            tag = mail._new_tag()
            if isinstance(tag, str):
                tag = tag.encode()
            mail.send(tag + b" IDLE\r\n")
            _ = mail.readline()  # continuation: + idling

            try:
                if hasattr(mail, "sock") and mail.sock:
                    mail.sock.settimeout(float(idle_timeout_sec))
                line = mail.readline()
                if isinstance(line, bytes) and b"EXISTS" in line.upper():
                    exists_event = True
            except socket.timeout:
                exists_event = False
            finally:
                try:
                    mail.send(b"DONE\r\n")
                    _ = mail.readline()
                except Exception:
                    pass
        except Exception as e:
            print(f"[GmailAlert] idle wait error: {e}")
            exists_event = False
        finally:
            try:
                if mail is not None:
                    mail.logout()
            except Exception:
                pass

        end_ts = time.time()
        self.session_poll_from[uid] = end_ts

        if not exists_event:
            return []

        alerts = self._fetch_messages_between(
            start_ts=start_ts,
            end_ts=end_ts,
            max_scan=max(10, int(self.live_scan_limit)),
        )
        if max_alerts and len(alerts) > max_alerts:
            return alerts[:max_alerts]
        return alerts

    def end_session(self, user_id: str, disconnected_at_ts: float | None = None):
        uid = str(user_id or "").strip().lower()
        now_ts = float(disconnected_at_ts or time.time())
        self.last_disconnect_by_user[uid] = now_ts
        if uid in self.session_poll_from:
            del self.session_poll_from[uid]
        self._save_state()
