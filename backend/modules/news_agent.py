
import requests
import feedparser
import urllib.parse
import random
import time
import os
from typing import List, Optional, Tuple

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
    FILLER_PROBABILITY = 0.3        # 침묵 시 뉴스를 꺼낼 확률 (30%)
    MAX_POCKET_SIZE = 5             # 스토리 포켓에 저장할 최대 뉴스 개수
    
    # 4. 위치 기반 필터링 설정
    USE_LOCATION = True             # 위치 기반 뉴스 필터링 사용 여부
    AZURE_MAPS_KEY_ENV = "AZURE_MAPS_SUBSCRIPTION_KEY" # 환경변수 키 이름


class NewsAgent:
    def __init__(self, config: NewsConfig = None):
        self.config = config if config else NewsConfig()
        
        # 상태 관리
        self.last_urgent_check = 0
        self.last_normal_check = 0
        self.seen_news_ids = set()
        self.story_pocket = []  # 🎒 이야기 주머니
        
        # 위치 정보
        self.current_location = None # (lat, lon, address)
        self.azure_maps_key = os.getenv(self.config.AZURE_MAPS_KEY_ENV)

        print("[NewsAgent] Initialized with config:")
        print(f" - Urgent Interval: {self.config.URGENT_CHECK_INTERVAL}s")
        print(f" - Location Enabled: {self.config.USE_LOCATION}")

    def fetch_and_sort_news(self) -> Optional[str]:
        """
        주기적으로 호출되어 긴급 뉴스를 체크하고, 일반 뉴스는 주머니에 넣습니다.
        반환값:
            - str: "🚨 [속보] ..." (즉시 인터럽트 필요)
            - None: 긴급한 내용 없음
        """
        now = time.time()
        
        # 1. 긴급 속보 체크 (짧은 주기)
        if now - self.last_urgent_check > self.config.URGENT_CHECK_INTERVAL:
            self.last_urgent_check = now
            urgent_news = self._check_urgent_news()
            if urgent_news:
                return urgent_news # 즉시 반환 (인터럽트 요청)

        # 2. 일반 관심사 체크 (긴 주기) -> 주머니 채우기
        if now - self.last_normal_check > self.config.NORMAL_CHECK_INTERVAL:
            self.last_normal_check = now
            self._fill_story_pocket()

        return None

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
        Azure Maps를 이용해 현재 위치를 텍스트로 반환 (예: '서울시 마포구')
        캐싱하여 재사용
        """
        if self.current_location:
            return self.current_location[2] # address returning
            
        if not self.config.USE_LOCATION or not self.azure_maps_key:
            print(f"[NewsAgent] ⚠️ Location Skipped. UseLocation={self.config.USE_LOCATION}, KeyLoaded={bool(self.azure_maps_key)}")
            return None

        try:
            # 1. 내 공용 IP 확인 (Azure Maps가 IP 파라미터를 요구할 경우를 대비)
            try:
                ip_response = requests.get('https://api.ipify.org?format=json', timeout=3)
                my_ip = ip_response.json()['ip']
            except Exception:
                my_ip = None

            # 2. IP 기반 위치 추적 (Azure Maps)
            # IP가 없으면 요청자의 IP를 사용하도록 되어있으나, 명시적으로 주는 것이 정확함
            url = f"https://atlas.microsoft.com/geolocation/ip/json?api-version=1.0&subscription-key={self.azure_maps_key}"
            if my_ip:
                url += f"&ip={my_ip}"
                
            response = requests.get(url, timeout=3)
            data = response.json()
            
            if "position" in data:
                lat = data["position"]["lat"]
                lon = data["position"]["lon"]
                
                # 좌표 -> 주소 변환 (Reverse Geocoding)
                address = self._reverse_geocode(lat, lon)
                self.current_location = (lat, lon, address)
                # print(f"[NewsAgent] 📍 Location Detected: {address}")
                return address
            
            elif "countryRegion" in data:
                # 좌표를 못 구했을 경우 국가 코드라도 반환
                country = data["countryRegion"].get("isoCode", "KR")
                # print(f"[NewsAgent] 📍 Location Fallback: {country}")
                return f"Region-{country}"
                
        except Exception as e:
            # print(f"[NewsAgent] ⚠️ Location Check Failed: {e}")
            pass
            
        return None

    def _reverse_geocode(self, lat, lon) -> str:
        """좌표를 주소(시/구)로 변환"""
        try:
            url = f"https://atlas.microsoft.com/search/address/reverse/json?api-version=1.0&query={lat},{lon}&subscription-key={self.azure_maps_key}"
            response = requests.get(url, timeout=3)
            data = response.json()
            
            if "addresses" in data and data["addresses"]:
                addr = data["addresses"][0]["address"]
                # 시/구 정도만 추출 (예: Seoul, Mapo-gu)
                city = addr.get("municipality") or addr.get("countrySubdivision", "")
                return city
        except Exception:
            pass
        return "Unknown Location"

    def _check_urgent_news(self) -> Optional[str]:
        for keyword in self.config.URGENT_KEYWORDS:
            # 위치 정보가 있다면 "지역명 + 키워드"로 검색 (예: "서울 태풍")
            query = keyword
            location = self.get_current_location()
            if self.config.USE_LOCATION and location:
                query = f"{location} {keyword}"
                
            story = self._fetch_rss(query)
            if story:
                print(f"[NewsAgent] 🚨 Urgent Fetch: {story}")
                return f"🚨 [속보] {story}"
        return None

    def _fill_story_pocket(self):
        if len(self.story_pocket) >= self.config.MAX_POCKET_SIZE:
            return

        # 관심사 중 랜덤 선택
        topic = random.choice(self.config.INTEREST_TOPICS)
        story = self._fetch_rss(topic)
        
        if story:
            self.story_pocket.append(story)
            print(f"[NewsAgent] 🎒 Pocket Added ({len(self.story_pocket)}/{self.config.MAX_POCKET_SIZE}): {story[:30]}...")

    def _fetch_rss(self, keyword: str) -> Optional[str]:
        encoded = urllib.parse.quote(keyword)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"
        
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                for entry in feed.entries[:3]: # 상위 3개만 검사
                    if entry.id in self.seen_news_ids:
                        continue
                    
                    self.seen_news_ids.add(entry.id)
                    return f"[{keyword}] {entry.title}"
        except Exception as e:
            print(f"[NewsAgent] ⚠️ Feed Error ({keyword}): {e}")
            
        return None

if __name__ == "__main__":
    # 간단 테스트
    agent = NewsAgent()
    print("Testing News Fetch...")
    print(agent.fetch_and_sort_news())
