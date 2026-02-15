import asyncio
import time
from typing import Awaitable, Callable


async def run_gmail_alert_loop(
    *,
    gmail_alert,
    user_id: str,
    bind_user: bool,
    idle_timeout_sec: float,
    live_poll_fallback_sec: float,
    user_activity: dict,
    response_guard: dict,
    send_proactive_announcement: Callable[[str, str, str], Awaitable[None]],
    log: Callable[[str], None] = print,
):
    if not gmail_alert or (not getattr(gmail_alert, "enabled", False)):
        return

    if bind_user:
        bound = str(getattr(gmail_alert, "user", "") or "").strip().lower()
        if bound and str(user_id).strip().lower() != bound:
            log(f"[GmailAlert] skipped: connected user {user_id} does not match bound gmail user")
            return

    log(f"[GmailAlert] loop started (idle_timeout={idle_timeout_sec}s, user={user_id})")
    try:
        # 1) Backlog check: previous disconnect ~ current connect
        backlog_alerts = await asyncio.to_thread(gmail_alert.begin_session, user_id, time.time())
        if backlog_alerts:
            sent = 0
            for alert in backlog_alerts[:2]:
                summary = str(alert.get("summary") or "").strip()
                if not summary:
                    continue
                tone = str(alert.get("tone") or "neutral")
                style = str(alert.get("style") or "")
                sent += 1
                await send_proactive_announcement(summary, tone, style)
            if sent > 0:
                log(f"[GmailAlert] backlog urgent detected: {sent}")
                user_activity["last_user_ts"] = time.monotonic()
        else:
            log("[GmailAlert] backlog urgent detected: 0")

        while True:
            # Don't interrupt active user turn.
            if (time.monotonic() - float(user_activity.get("last_user_ts") or 0.0)) < 5.0:
                await asyncio.sleep(1.0)
                continue
            if response_guard.get("active"):
                await asyncio.sleep(1.0)
                continue

            try:
                alerts = await asyncio.wait_for(
                    asyncio.to_thread(
                        gmail_alert.wait_next_live_alert,
                        user_id,
                        idle_timeout_sec,
                        1,
                    ),
                    timeout=idle_timeout_sec + 8.0,
                )
            except asyncio.TimeoutError:
                log("[GmailAlert] idle wait hard-timeout, using fallback poll")
                alerts = []

            # Fallback polling for environments where IDLE event can be missed.
            if not alerts:
                alerts = await asyncio.to_thread(gmail_alert.poll_live_alerts, user_id, 1)

            if alerts:
                alert = alerts[0]
                summary = str(alert.get("summary") or "").strip()
                if summary:
                    log(f"[GmailAlert] urgent mail detected: {summary}")
                    await send_proactive_announcement(
                        summary,
                        str(alert.get("tone") or "neutral"),
                        str(alert.get("style") or ""),
                    )
                    user_activity["last_user_ts"] = time.monotonic()
            else:
                log("[GmailAlert] idle wait timeout/no urgent mail")

            await asyncio.sleep(max(1.0, live_poll_fallback_sec))
    except asyncio.CancelledError:
        return
    except Exception as e:
        log(f"[GmailAlert] loop error: {e}")
