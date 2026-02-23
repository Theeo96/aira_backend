from __future__ import annotations

import re


def is_vision_related_query(text: str) -> bool:
    t = str(text or "")
    if not t:
        return False
    keywords = [
        "화면",
        "보여",
        "보이",
        "보여줘",
        "사진",
        "이미지",
        "이거",
        "저거",
        "무엇",
        "뭐야",
        "무슨",
        "읽어",
        "글자",
        "문서",
        "차트",
        "표",
        "슬라이드",
        "색",
        "옷",
        "어울려",
        "보이는",
        "scene",
        "screen",
        "image",
        "what do you see",
    ]
    t_lower = t.lower()
    return any(k in t_lower for k in keywords)


def is_vision_followup_utterance(text: str) -> bool:
    t = str(text or "").strip()
    if not t:
        return False
    compact = re.sub(r"[\s\W_]+", "", t)
    if len(compact) <= 8:
        return True
    hints = [
        "지금",
        "이번엔",
        "그럼",
        "다시",
        "이건",
        "저건",
        "그건",
        "어때",
        "맞아",
        "아니",
        "들고",
        "보여",
        "보이나",
        "잘안",
    ]
    return any(h in t for h in hints)


def is_home_update_utterance(text: str) -> bool:
    t = str(text or "")
    if not t:
        return False
    keywords = [
        "이사",
        "집은",
        "우리 집",
        "우리집",
        "집 주소",
        "집 위치",
        "집 도착역",
        "집 근처 역",
        "집이 ",
        "내 집",
        "내집",
        "집 앞",
        "집앞",
    ]
    return any(k in t for k in keywords)
