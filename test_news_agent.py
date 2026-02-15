import asyncio
import os
import sys
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.modules.news_agent import NewsAgent, NewsConfig

# Mock Session Class
class MockSession:
    async def send(self, input, end_of_turn=True):
        print(f"[MockSession] Sending to Gemini: {input}")

async def test_news_agent():
    print("[NewsAgent] Testing Update Loop...")
    
    # 1. 설정 (즉시 실행되도록)
    config = NewsConfig()
    config.URGENT_CHECK_INTERVAL = 0 # 항상 체크
    config.NORMAL_CHECK_INTERVAL = 0 # 항상 체크
    config.USE_LOCATION = True 
    
    agent = NewsAgent(config)
    
    # 2. 세션 주입 (Mock)
    mock_session = MockSession()
    agent.initialize(mock_session)
    
    print("\n--- Running agent.update() ---")
    # 3. update() 실행 (비동기)
    await agent.update()
    
    # 4. 결과 확인
    # 로그를 통해 확인 가능 (fetch 성공 여부 등)
    print("\n[Test] Update finished. Check logs above for '[Urgent]...' or '[Pocket]...' messages.")

    # 추가 테스트: 포켓 확인
    print(f"\n[Test] Story Pocket Size: {len(agent.story_pocket)}")
    if agent.story_pocket:
        print(f"[Test] First story in pocket: {agent.story_pocket[0]}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    asyncio.run(test_news_agent())
