import asyncio
from typing import List, Any
from modules.module_interface import BaseModule

class ModuleManager:
    """
    여러 모듈을 등록하고 관리하는 클래스
    aira_main.py는 이 클래스만 알면 됩니다.
    """
    def __init__(self):
        self.modules: List[BaseModule] = []
        self.session = None

    def register_module(self, module: BaseModule):
        """모듈을 등록합니다."""
        if not isinstance(module, BaseModule):
            raise ValueError(f"Module {module} must inherit from BaseModule")
        
        self.modules.append(module)
        print(f"[ModuleManager] Registered: {module.name}")
        
        # 이미 세션이 시작된 상태라면 늦게라도 초기화
        if self.session:
            module.initialize(self.session)

    def initialize_session(self, session: Any):
        """Gemini 세션 연결 시 호출하여 모든 모듈에 전파합니다."""
        self.session = session
        print("[ModuleManager] Initializing all modules with session...")
        for module in self.modules:
            module.initialize(session)

    async def run_updates(self):
        """메인 루프에서 주기적으로 호출하여 각 모듈의 update()를 실행합니다."""
        if not self.modules:
            return

        # 모든 모듈의 update를 비동기로 실행 (병렬)
        await asyncio.gather(*(module.update() for module in self.modules))

    async def on_user_input(self, text: str):
        """사용자 입력 발생 시 모든 모듈에 전파합니다."""
        await asyncio.gather(*(module.on_user_input(text) for module in self.modules))

    # --- Tool Use Support ---
    def get_all_tools(self) -> List[dict]:
        """모든 모듈의 도구 정의를 합쳐서 반환합니다."""
        tools = []
        for module in self.modules:
            tools.extend(module.get_tools())
        return tools

    async def handle_tool_call(self, tool_call) -> dict:
        """
        Gemini의 도구 호출 요청을 처리하고 결과를 반환합니다.
        :param tool_call: google.genai.types.ToolCall 객체 (또는 유사 구조)
        :return: {'name': ..., 'content': ...} 형태의 결과 딕셔너리
        """
        if not tool_call or not tool_call.function_calls:
            return None

        for fc in tool_call.function_calls:
            name = fc.name
            args = fc.args
            print(f"[ModuleManager] 🛠️ Tool Call: {name}({args})")

            # 각 모듈에게 실행 기회 부여
            for module in self.modules:
                result = await module.execute_tool(name, args)
                if result is not None:
                    print(f"[{module.name}] Tool Executed: {result[:50]}...")
                    return {
                        "name": name,
                        "content": {"result": result}
                    }
            
            print(f"[ModuleManager] ⚠️ Unknown Tool: {name}")
            return {
                "name": name,
                "content": {"error": f"Tool '{name}' not found."}
            }
        return None
