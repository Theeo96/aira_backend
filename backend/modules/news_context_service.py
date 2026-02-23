import re
from typing import Any


class NewsContextService:
    def __init__(self, news_agent=None, log=print):
        self.news_agent = news_agent
        self.log = log

    def extract_topic(self, text: str | None):
        t = str(text or "").strip()
        if not t:
            return None
        t = re.sub(r"(알려줘|말해줘|보여줘|찾아줘|브리핑|요약|어때|뭐야|줘)$", "", t).strip()
        t = re.sub(r"(오늘|지금|최신)\s*", "", t).strip()
        t = re.sub(r"(뉴스|헤드라인|속보|기사)", "", t).strip()
        t = re.sub(r"\s+", " ", t)
        return t if t else None

    def get_items(self, topic: str | None, limit: int = 3):
        if self.news_agent is None:
            return []
        query = str(topic or "").strip() or "최신 뉴스"
        try:
            items = self.news_agent._search_naver_news(query, display=max(limit, 5))
        except Exception as e:
            self.log(f"[News] fetch failed: {e}")
            return []
        rows = []
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title") or "").strip()
                desc = str(item.get("description") or "").strip()
                link = str(item.get("link") or "").strip()
                pub_date = str(item.get("pubDate") or "").strip()
                if title:
                    rows.append(
                        {
                            "title": title,
                            "description": desc,
                            "link": link,
                            "pubDate": pub_date,
                        }
                    )
                if len(rows) >= limit:
                    break
        return rows

    def get_headlines(self, topic: str | None, limit: int = 3):
        items = self.get_items(topic=topic, limit=limit)
        headlines = []
        for item in items:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            if title:
                headlines.append(title)
        return headlines

    def is_detail_query(self, text: str | None) -> bool:
        t = str(text or "").strip().lower()
        if not t:
            return False
        keys = [
            "자세히",
            "상세",
            "무슨 내용",
            "어떤 내용",
            "디테일",
            "요약",
            "더 알려",
            "더 말해",
            "그 기사",
            "그 뉴스",
            "첫 기사",
            "첫 뉴스",
            "1번",
            "2번",
            "3번",
            "첫번째",
            "두번째",
            "세번째",
            "관련 뉴스",
        ]
        return any(k in t for k in keys)

    def is_followup_query(self, text: str | None) -> bool:
        t = str(text or "").strip().lower()
        if not t:
            return False
        keys = [
            "그럼",
            "그건",
            "왜",
            "언제",
            "누가",
            "어디",
            "어떻게",
            "무슨 의미",
            "영향",
            "결과",
            "정리",
            "다시 설명",
            "추가로",
        ]
        return any(k in t for k in keys)

    def select_item_by_text(self, text: str | None, items: list[dict[str, Any]]):
        t = str(text or "").strip().lower()
        if not t or not items:
            return None

        explicit_idx = None
        if "1번" in t or "첫번째" in t:
            explicit_idx = 0
        elif "2번" in t or "두번째" in t:
            explicit_idx = 1
        elif "3번" in t or "세번째" in t:
            explicit_idx = 2
        if explicit_idx is not None and 0 <= explicit_idx < len(items):
            return items[explicit_idx]

        tokens = [tok for tok in re.split(r"[\s,./!?]+", t) if len(tok) >= 2]
        stop_tokens = {
            "뉴스",
            "기사",
            "자세히",
            "상세",
            "요약",
            "내용",
            "그거",
            "그럼",
            "왜",
            "알려줘",
        }
        tokens = [tok for tok in tokens if tok not in stop_tokens]

        best = None
        best_score = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").lower()
            desc = str(item.get("description") or "").lower()
            score = 0
            for tok in tokens:
                if tok in title:
                    score += 3
                if tok in desc:
                    score += 1
            if score > best_score:
                best = item
                best_score = score
        return best if best_score > 0 else None

    def build_detail_summary(self, item: dict[str, Any] | None) -> str:
        if not isinstance(item, dict):
            return "해당 뉴스의 상세 내용을 찾지 못했어요."
        title = str(item.get("title") or "").strip()
        desc = re.sub(r"\s+", " ", str(item.get("description") or "").strip())
        pub_date = str(item.get("pubDate") or "").strip()
        date_str = f" (발행일: {pub_date})" if pub_date else ""
        if len(desc) > 220:
            desc = desc[:220].rstrip() + "..."
        if title and desc:
            return f"기사 제목은 '{title}'{date_str}이고, 핵심 내용은 다음과 같아요. {desc}"
        if title:
            return f"기사 제목은 '{title}'{date_str}입니다. 제목 기준으로 핵심만 간단히 설명드릴게요."
        return "기사 상세 요약을 만들 수 없어요."

