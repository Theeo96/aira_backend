from abc import ABC, abstractmethod
from typing import Any, Optional

class BaseModule(ABC):
    """
    모든 Aira 모듈이 상속받아야 할 기본 인터페이스
    """
    def __init__(self, name: str):
        self.name = name
        self.session = None # Gemini Session 객체 (initialize 시 주입)
        self.config: Any = None

    def initialize(self, session: Any, config: Any = None):
        """
        Gemini 세션이 연결되었을 때 호출됩니다.
        :param session: aira_main.py의 session 객체 (send 메서드 보유)
        :param config: 전역 설정 객체 (선택)
        """
        self.session = session
        if config:
            self.config = config
        print(f"[{self.name}] Initialized.")

    @abstractmethod
    async def update(self):
        """
        메인 루프에서 주기적으로 호출됩니다. (Non-blocking 필수)
        주기적인 작업(뉴스 체크, 알림 등)을 수행합니다.
        """
        pass

    async def on_user_input(self, text: str):
        """
        사용자가 무언가 말했을 때 호출됩니다. (선택 구현)
        :param text: 사용자의 발화 텍스트 (STT 결과)
        """
        pass

    async def _send_to_gemini(self, message: str, is_system: bool = True):
        """
        Gemini에게 메시지를 보냅니다.
        :param message: 보낼 메시지 내용
        :param is_system: True이면 시스템 프롬프트로 주입
        """
        if not self.session:
            print(f"[{self.name}] [WARN] Session not initialized. Cannot send: {message}")
            return

        try:
            input_text = f"[SYSTEM] {message}" if is_system else message
            # aira_main.py의 세션 객체 구조에 맞춰 호출 (session.send)
            await self.session.send(input=input_text, end_of_turn=True)
            print(f"[{self.name}] [OUT] Sent to Gemini: {message[:50]}...")
        except Exception as e:
            print(f"[{self.name}] [ERR] Send Error: {e}")

    # --- Tool Use (Function Calling) Support ---
    def get_tools(self) -> list:
        """
        이 모듈이 제공하는 도구(Function) 정의를 반환합니다.
        Gemini의 'tools' 설정에 들어갈 딕셔너리 리스트여야 합니다.
        """
        return []

    async def execute_tool(self, tool_name: str, args: dict) -> Optional[str]:
        """
        Gemini가 도구를 호출했을 때 실행되는 메서드입니다.
        :param tool_name: 호출된 도구 이름
        :param args: 도구 인자 (dict)
        :return: 도구 실행 결과 (문자열) 또는 None (처리 안 함)
        """
        return None
