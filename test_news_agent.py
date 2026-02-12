
# .env 로드
load_dotenv()

# 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.modules.news_agent import NewsAgent, NewsConfig

def test_news_agent():
    print("[NewsAgent] Testing...")
    
    # 설정: 테스트를 위해 짧은 주기로 변경
    config = NewsConfig()
    config.URGENT_CHECK_INTERVAL = 0 # 즉시 확인
    config.NORMAL_CHECK_INTERVAL = 0 # 즉시 확인
    config.USE_LOCATION = True # 위치 기반 테스트
    
    agent = NewsAgent(config)
    
    # 1. 위치 확인 테스트
    print("\n--- 1. Location Test ---")
    location = agent.get_current_location()
    print(f"Current Location: {location}")
    if location:
        print("[Location] Fetched successfully.")
    else:
        print("[Location] Fetch failed (Check Azure Key or Network).")

    # 2. 뉴스 가져오기 테스트
    print("\n--- 2. Fetch News Test ---")
    urgent = agent.fetch_and_sort_news()
    if urgent:
        print(f"[Urgent] {urgent}")
    else:
        print("[Urgent] No urgent news found (Normal).")
        
    # 3. 스토리 포켓 테스트
    print("\n--- 3. Story Pocket Test ---")
    print(f"Pocket Size: {len(agent.story_pocket)}")
    for i, story in enumerate(agent.story_pocket):
        print(f"[{i+1}] {story}")
        
    # 4. 필러 꺼내기 테스트
    print("\n--- 4. Filler Test ---")
    # 확률 무시하고 강제로 꺼내기 위해 임시 조작
    agent.config.FILLER_PROBABILITY = 1.0 
    filler = agent.get_story_from_pocket()
    print(f"Pop Story: {filler}")

if __name__ == "__main__":
    try:
        # 윈도우 인코딩 설정
        if sys.platform == 'win32':
             sys.stdout.reconfigure(encoding='utf-8')
        test_news_agent()
    except Exception as e:
        print(f"[Error] Test Failed: {e}")
        import traceback
        traceback.print_exc()
