from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def extract_destination_from_text(text: str) -> str | None:
    s = str(text or "").strip()
    if not s:
        return None

    patterns = [
        r"([가-힣A-Za-z0-9\s]{1,30})\s*까지",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*(?:으로|로)\s*가",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*가려면",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*가는",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*가는\s*길",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*가는길",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*(?:가는|갈|가능)\s*방법",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*에서\s*약속",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*쪽(?:으로)?",
        r"([가-힣A-Za-z0-9\s]{1,30})\s*(?:에|에서)\s*가",
    ]
    for p in patterns:
        m = re.search(p, s)
        if m:
            cand = re.sub(r"\s+", " ", m.group(1)).strip()
            cand = re.sub(r"(쪽|근처|부근|방향)$", "", cand).strip()
            if cand and cand not in ("집", "회사", "학교", "거기", "여기"):
                return cand

    m2 = re.search(r"([가-힣A-Za-z0-9]{2,20})(?:역)?\s*(?:으로|로)$", s)
    if m2:
        cand = m2.group(1).strip()
        if cand:
            return cand

    m3 = re.search(r"([가-힣A-Za-z0-9]{2,20})\s*(?:방법|경로)$", s)
    if m3:
        cand = m3.group(1).strip()
        if cand:
            return cand

    m4 = re.search(r"([가-힣A-Za-z0-9]{2,20})\s*역", s)
    if m4:
        cand = m4.group(1).strip()
        if cand:
            return cand
    return None


def normalize_place_name(name: str | None) -> str:
    if not name:
        return ""
    return re.sub(r"\s+", "", str(name)).lower()


def is_congestion_query(text: str) -> bool:
    t = str(text or "").lower()
    if not t:
        return False
    keys = [
        "혼잡", "붐", "여유", "덜 붐비", "칸", "인파", "crowd", "congestion",
    ]
    return any(k in t for k in keys)


def is_schedule_query(text: str) -> bool:
    t = str(text or "").lower()
    if not t:
        return False
    keys = [
        "시간표", "운행 일정", "운행일정", "운행 시간", "운행시간",
        "첫차", "막차", "운행", "timetable", "schedule",
    ]
    return any(k in t for k in keys)


def is_arrival_eta_query(text: str) -> bool:
    t = str(text or "").lower()
    if not t:
        return False
    # Use exact same logic defined in AIRA_FIX_PLAN
    transit_tokens = ["지하철", "전철", "열차", "subway", "train", "호선", "버스"]
    eta_tokens = [
        "몇 분", "몇분", "언제 와", "언제와", "도착", "남았", "어디 쯤", "어디쯤", "어디야",
        "도착 예정", "도착예정", "다음 열차", "다음열차", "첫 열차", "첫차", "막차"
    ]
    has_transit = any(k in t for k in transit_tokens)
    has_eta = any(k in t for k in eta_tokens)
    return has_transit and has_eta


def extract_schedule_search_dttm(
    text: str,
    now_kst: datetime | None = None,
) -> tuple[str, str]:
    now = now_kst or datetime.now(ZoneInfo("Asia/Seoul"))
    t = str(text or "")
    day_offset = 0
    if "내일" in t:
        day_offset = 1
    elif "모레" in t:
        day_offset = 2

    hh = now.hour
    mm = now.minute
    m = re.search(r"(오전|오후|아침|저녁|밤)?\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분?)?", t)
    if m:
        ap = str(m.group(1) or "")
        hh = int(m.group(2))
        mm = int(m.group(3) or 0)
        if ap in {"오후", "저녁", "밤"} and hh < 12:
            hh += 12
        if ap == "오전" and hh == 12:
            hh = 0
        hh = max(0, min(23, hh))
        mm = max(0, min(59, mm))

    target = now.replace(second=0, microsecond=0, hour=hh, minute=mm)
    if day_offset:
        target = target + timedelta(days=day_offset)
    label = f"{target.month}월 {target.day}일 {target.hour:02d}:{target.minute:02d}"
    return target.strftime("%Y%m%d%H%M"), label
