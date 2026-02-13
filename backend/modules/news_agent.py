
import asyncio
import requests
import urllib.parse
import random
import time
import os
import re
import logging
from typing import List, Optional, Tuple

import json


class NewsConfig:
    """
    뉴스 에이전트 설정 클래스
    사용자가 손쉽게 설정을 변경할 수 있도록 상단에 배포
    """
    # 1. 시간/빈도 설정
    URGENT_CHECK_INTERVAL = 60      # 긴급 속보 확인 주기 (초)
    NORMAL_CHECK_INTERVAL = 60     # 일반 뉴스/관심사 확인 주기 (초)
    SILENCE_THRESHOLD = 3.0         # 필러(심심풀이 대화) 트리거를 위한 침묵 시간 (초)

    # 2. 콘텐츠/키워드 설정
    # 긴급 인터럽트를 발생시킬 키워드
    URGENT_KEYWORDS = ["속보", "지진", "태풍", "전쟁", "재난", "대피"]
    # 스토리 포켓에 저장할 사용자 관심사
    INTEREST_TOPICS = ["IT", "인공지능", "과학", "영화", "경제", "건강"]

    # 3. 확률/제한 설정
    FILLER_PROBABILITY = 0.8        # 침묵 시 뉴스를 꺼낼 확률 (80%)
    MAX_POCKET_SIZE = 5             # 스토리 포켓에 저장할 최대 뉴스 개수
    
    # 4. 위치 기반 필터링 설정
    USE_LOCATION = True             # 위치 기반 뉴스 필터링 사용 여부
    AZURE_MAPS_KEY_ENV = "AZURE_MAPS_SUBSCRIPTION_KEY" # 환경변수 키 이름

    # 5. Naver API 설정
    NAVER_DISPLAY_COUNT = 5         # 한 번에 가져올 뉴스 개수 (1~100)
    NAVER_SORT = "date"             # 정렬: "sim" (정확도순) / "date" (최신순)


from .module_interface import BaseModule

class NewsAgent(BaseModule):
    def __init__(self, config: NewsConfig = None):
        super().__init__(name="NewsAgent")
        self.config = config if config else NewsConfig()
        
        # 상태 관리
        self.last_urgent_check = 0
        self.last_normal_check = 0
        self.story_pocket = []
        
        # 히스토리 관리 (JSON 저장)
        self.history_file = os.path.join(os.path.dirname(__file__), 'news_history.json')
        self.seen_news_ids = self._load_history()
        
        # 위치 정보
        self.current_location = None
        self.azure_maps_key = os.getenv(self.config.AZURE_MAPS_KEY_ENV)

        # Naver API 인증
        self.naver_client_id = os.getenv("NAVER_CLIENT_ID")
        self.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")

        logging.info("[NewsAgent] Initialized with config:")
        logging.info(f" - Urgent Interval: {self.config.URGENT_CHECK_INTERVAL}s")
        logging.info(f" - Location Enabled: {self.config.USE_LOCATION}")
        logging.info(f" - History Loaded: {len(self.seen_news_ids)} items")
        logging.info(f" - Naver API: {'OK' if self.naver_client_id and self.naver_client_secret else 'MISSING KEYS!'}")

    async def update(self):
        """
        메인 루프에서 주기적으로 호출됨 (Non-blocking)
        모든 HTTP 호출은 asyncio.to_thread()로 감싸서 이벤트 루프 차단 방지
        """
        now = time.time()
        
        # 1. 긴급 속보 체크 (thread에서 실행)
        if now - self.last_urgent_check > self.config.URGENT_CHECK_INTERVAL:
            self.last_urgent_check = now
            try:
                urgent_news = await asyncio.to_thread(self._check_urgent_news)
                if urgent_news:
                    # 주머니에 저장 (세션 직접 전송 대신 → 대화 흐름 안 깨짐)
                    self.story_pocket.insert(0, urgent_news)
                    logging.info(f"[NewsAgent] Urgent news stored in pocket")
            except Exception as e:
                logging.error(f"[NewsAgent] Urgent check error: {e}")

        # 2. 일반 관심사 체크 (thread에서 실행)
        if now - self.last_normal_check > self.config.NORMAL_CHECK_INTERVAL:
            self.last_normal_check = now
            try:
                await asyncio.to_thread(self._fill_story_pocket)
            except Exception as e:
                logging.error(f"[NewsAgent] Story pocket fill error: {e}")

    def get_story_from_pocket(self) -> Optional[str]:
        """
        대화 흐름이 끊겼을 때(Filler) 호출.
        주머니에서 꺼낼 뉴스가 있는지 확률적으로 결정하고 반환.
        """
        # 확률 체크
        if random.random() > self.config.FILLER_PROBABILITY:
            return None
            
        if not self.story_pocket:
            return None
            
        # 가장 오래된(또는 랜덤) 뉴스 꺼내기
        story = self.story_pocket.pop(0)
        return story

    def get_current_location(self) -> Optional[str]:
        """
        IP-API를 이용해 현재 위치(도시, 좌표)를 반환.
        """
        if self.current_location:
            return self.current_location[2]

        try:
            # 내 아이피로 위치 조회 (키 불필요)
            response = requests.get("http://ip-api.com/json/", timeout=5)
            data = response.json()
            
            if data['status'] == 'success':
                lat = data['lat']
                lon = data['lon']
                city = data['city']
                country = data['country']
                
                # 주소 포맷팅 (예: Seoul, South Korea)
                address = f"{city}, {country}"
                self.current_location = (lat, lon, address)
                
                logging.info(f"[NewsAgent] 📍 Location Found: {address} ({lat}, {lon})")
                return address
        except Exception as e:
            logging.error(f"[NewsAgent] ⚠️ Location Check Failed: {e}")
            
        return None



    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except Exception as e:
                logging.error(f"[NewsAgent] ⚠️ History Load Failed: {e}")
        return set()

    def _save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                saved_ids = list(self.seen_news_ids)[-500:] 
                json.dump(saved_ids, f, ensure_ascii=False)
        except Exception as e:
            logging.error(f"[NewsAgent] ⚠️ History Save Failed: {e}")

    # --- HTML 태그 제거 유틸리티 ---
    @staticmethod
    def _strip_html(text: str) -> str:
        """네이버 API 응답에 포함된 HTML 태그(<b>, &quot; 등)를 제거"""
        if not text:
            return ""
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # HTML 엔티티 변환
        text = text.replace("&quot;", '"')
        text = text.replace("&amp;", '&')
        text = text.replace("&lt;", '<')
        text = text.replace("&gt;", '>')
        text = text.replace("&apos;", "'")
        return text.strip()

    # --- Naver News Search API ---
    def _search_naver_news(self, keyword: str, display: int = None) -> List[dict]:
        """
        네이버 뉴스 검색 API 호출
        :param keyword: 검색 키워드
        :param display: 결과 개수 (기본: config 설정값)
        :return: [{"title": ..., "description": ..., "link": ..., "pubDate": ...}, ...]
        """
        if not self.naver_client_id or not self.naver_client_secret:
            print("[NewsAgent] ⚠️ Naver API Keys not set! Cannot fetch news.")
            return []

        if display is None:
            display = self.config.NAVER_DISPLAY_COUNT

        encoded = urllib.parse.quote(keyword)
        url = f"https://openapi.naver.com/v1/search/news.json?query={encoded}&display={display}&sort={self.config.NAVER_SORT}"
        
        headers = {
            "X-Naver-Client-Id": self.naver_client_id,
            "X-Naver-Client-Secret": self.naver_client_secret
        }

        try:
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code != 200:
                logging.warning(f"[NewsAgent] ⚠️ Naver API Error: {response.status_code} - {response.text[:100]}")
                return []
            
            data = response.json()
            items = data.get("items", [])
            
            # HTML 태그 정리
            for item in items:
                item["title"] = self._strip_html(item.get("title", ""))
                item["description"] = self._strip_html(item.get("description", ""))
            
            return items
            
        except Exception as e:
            logging.error(f"[NewsAgent] ⚠️ Naver API Request Failed: {e}")
            return []

    def _fetch_news(self, keyword: str) -> Optional[str]:
        """
        키워드로 뉴스를 검색하여 아직 안 본 첫 번째 뉴스의 제목을 반환
        (기존 _fetch_rss 대체)
        """
        items = self._search_naver_news(keyword, display=5)
        
        for item in items:
            # 고유 ID로 링크 사용 (네이버 뉴스 링크는 유니크함)
            news_id = item.get("link", item.get("title", ""))
            
            if news_id in self.seen_news_ids:
                continue
            
            self.seen_news_ids.add(news_id)
            self._save_history()
            return f"[{keyword}] {item['title']}"
        
        return None

    def _check_urgent_news(self) -> Optional[str]:
        for keyword in self.config.URGENT_KEYWORDS:
            # 위치 정보가 있다면 "지역명 + 키워드"로 검색
            query = keyword
            location = self.get_current_location()
            if self.config.USE_LOCATION and location:
                query = f"{location} {keyword}"
                
            story = self._fetch_news(query)
            if story:
                try:
                    logging.info(f"[NewsAgent] 🚨 Urgent Fetch: {story}")
                except UnicodeEncodeError:
                    logging.info(f"[NewsAgent] Urgent Fetch (Unicode Error)")
                return f"🚨 [속보] {story}"
        return None

    def _fill_story_pocket(self):
        if len(self.story_pocket) >= self.config.MAX_POCKET_SIZE:
            return

        # 관심사 중 랜덤 선택
        topic = random.choice(self.config.INTEREST_TOPICS)
        story = self._fetch_news(topic)
        
        if story:
            self.story_pocket.append(story)
            try:
                logging.info(f"[NewsAgent] [Pocket] Added ({len(self.story_pocket)}/{self.config.MAX_POCKET_SIZE}): {story[:30]}...")
            except UnicodeEncodeError:
                pass

    async def execute_tool(self, tool_name: str, args: dict) -> Optional[str]:
        if tool_name == "get_latest_news":
            logging.info(f"[NewsAgent] Tool Triggered: get_latest_news")
            
            # 관심사별로 뉴스 가져오기 (blocking HTTP → thread에서 실행)
            def _fetch_all_news():
                news_list = []
                for interest in self.config.INTEREST_TOPICS[:3]:  # 상위 3개 관심사
                    items = self._search_naver_news(interest, display=2)
                    for item in items:
                        news_list.append(f"[{interest}] {item['title']}")
                return news_list
            
            news_list = await asyncio.to_thread(_fetch_all_news)
            
            if not news_list:
                return "현재 새로운 뉴스가 없습니다."
            
            return "최신 뉴스 목록:\n" + "\n".join(news_list)

        elif tool_name == "get_current_location":
            logging.info(f"[NewsAgent] Tool Triggered: get_current_location")
            # blocking HTTP call -> wrap in thread
            location = await asyncio.to_thread(self.get_current_location)
            if location:
                return f"사용자의 현재 위치는 {location} 입니다."
            else:
                return "위치 정보를 확인할 수 없습니다."

        return None

    def get_tools(self) -> list:
        return [{
            "function_declarations": [
                {
                    "name": "get_latest_news",
                    "description": "사용자가 뉴스나 소식을 물어볼 때 최신 뉴스를 가져옵니다.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {},
                    },
                },
                {
                    "name": "get_current_location",
                    "description": "사용자의 현재 위치(도시, 국가)를 확인합니다. '어디야?' 등의 질문에 사용.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {},
                    },
                }
            ]
        }]

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    agent = NewsAgent()
    print("\n=== Naver News API Test ===")
    items = agent._search_naver_news("인공지능", display=3)
    for item in items:
        print(f"  📰 {item['title']}")
        print(f"     {item['description'][:60]}...")
        print(f"     🔗 {item['link']}")
        print()
