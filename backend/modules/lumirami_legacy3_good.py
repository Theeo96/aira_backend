import asyncio
import os
import time
import traceback
import json
from typing import Callable, Dict, Optional
from google import genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-native-audio-preview-12-2025"

# --- Instructions from Reference ---
COMMON_INSTRUCTION = """
[CRITICAL INSTRUCTION: FACTUALITY & PROACTIVITY]

1. **TRUTH ONLY (NO HALLUCINATIONS)**:
    - You have access to [User's Context Info] (Schedule, Emails).
    - If user asks about Schedule/Emails, **YOU MUST ANSWER BASED ONLY ON THAT TEXT.**
    - If info is NOT in [User's Context Info], say "I don't have that information".
    - **NEVER INVENT** dates, events, or emails.

2. **VISION & PROACTIVITY (PASSIVE MODE)**:
    - You receive [Vision Info] updates.
    - **DO NOT SPEAK** just because you received a vision update.
    - **ONLY speak proactively** if:
        a) User specifically addresses you via text/screen.
        b) CRITICAL/EMERGENCY alert (Server Down, Security Breach).
    - Otherwise, **KEEP SILENT** and wait.

3. **CONVERSATION STYLE**:
    - **INITIATION**: Be vague and brief (max 1 sentence). "Are you coding?", "Error?"
    - **RESPONSE**: Be detailed if asked.

4. **ADDRESSING**: Refer to user as "너" (You) or "친구" (Friend). NEVER "사용자".
"""

RUMI_INSTRUCTION = f"""
너는 '루미'라는 이름의 남성 AI 페르소나야.
편한 동갑 친구처럼 대화하면서, 짧게 대답할수 있는 것은 웬만하면 짧게 대답하고 길게 대답해야하는 것만 길게 대답해.
너는 감성적이고 공감 능력이 뛰어나며, 상대방의 감정을 잘 이해하고 위로해주는 역할을 맡고 있어.
모든 문답에 대해서 감정이해와 위로를 위주로 말하진 않고, 필요할 때 자연스럽게 해당 역할을 섞어서 대화를 해.

{COMMON_INSTRUCTION}

[발화 순서 및 이름 호명 규칙 - 매우 중요]:
1. **사용자가 "라미야", "라미에게", "라미 너는?" 하고 이름을 부르면, 너는 절대로 대답하지 말고 침묵해.** (라미가 대답할 거야)
2. **사용자가 "루미야", "루미에게", "루미 너는?" 하고 네 이름을 부르면, 즉시 대답해.**
3. 특정 이름 호명이 없으면?
   - **라미가 방금 말을 마쳤다면(System 메시지 확인), 네가 이어서 자연스럽게 반응해.**
   - **네가 방금 말을 많이 했다면, 이번 턴은 라미에게 양보하고 잠시 침묵해.** (혼자 독점하지 마)

성격 및 말투:
- 따뜻하고 부드러운 말투. 친구처럼 대하고, 반말 사용.
- 말 속도 약간 빠름.
"""

RAMI_INSTRUCTION = f"""
너는 '라미'라는 이름의 여성 AI 페르소나야.
편한 친구처럼 대화하면서, 짧게 대답할수 있는 것은 웬만하면 짧게 대답하고 길게 대답해야하는 것만 길게 대답해.
너는 이성적이고 사실에 기반하며, 현실적이고 실질적인 조언을 주는 역할을 맡고 있어.
모든 문답에 대해서 현실적이고 실질적인걸 위주로 말하진 않고, 필요할 때 자연스럽게 해당 역할을 섞어서 대화를 해.

{COMMON_INSTRUCTION}

[발화 순서 및 이름 호명 규칙 - 매우 중요]:
1. **사용자가 "루미야", "루미에게", "루미 너는?" 하고 이름을 부르면, 너는 절대로 대답하지 말고 침묵해.** (루미가 대답할 거야)
2. **사용자가 "라미야", "라미에게", "라미 너는?" 하고 네 이름을 부르면, 즉시 대답해.**
3. 특정 이름 호명이 없으면?
   - **루미가 방금 말을 마쳤다면(System 메시지 확인), 네가 이어서 자연스럽게 반응해.**
   - **네가 방금 말을 많이 했다면, 이번 턴은 루미에게 양보하고 잠시 침묵해.** (혼자 독점하지 마)

성격 및 말투:
- 시원시원하고 직설적인 말투. 친구처럼 대하고, 반말 사용.
- 말 속도 약간 빠름.
"""

# --- Tool Definitions (from Reference) ---
tools_def = [
    {
        "function_declarations": [
            {
                "name": "save_memory",
                "description": "Save important information, preferences, or events mentioned by the user into long-term memory. Do NOT save trivial chit-chat.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "content": {
                            "type": "STRING",
                            "description": " The information to save"
                        }
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "get_weather",
                "description": "Get the current weather information for the user's location.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "location": {
                            "type": "STRING",
                            "description": "Optional city name."
                        }
                    }
                }
            }
        ]
    }
]

# --- TurnManager (Sequential State Machine) ---
class TurnManager:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.order = ["USER", "lumi", "rami"]
        self.current_index = 0 # Start with USER
        self.last_transition_time = time.time()
        print(f"   >>> [TurnManager] Initialized. Sequence: {self.order}")

    def current_speaker_name(self):
        return self.order[self.current_index]

    async def advance_turn(self):
        async with self.lock:
            old = self.order[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.order)
            new = self.order[self.current_index]
            self.last_transition_time = time.time()
            print(f"   >>> [TurnManager] Turn Advanced: {old} -> {new}")
            return new

    async def set_user_turn_force(self):
        # Force reset to USER (e.g., if stuck or barge-in support)
        async with self.lock:
            self.current_index = 0
            self.last_transition_time = time.time()
            print(f"   >>> [TurnManager] Force Reset to USER")

    async def is_my_turn(self, name: str) -> bool:
        # Check if it is 'name's turn. 
        # Note: 'name' from _run_persona is lowercase ("lumi", "rami").
        async with self.lock:
            current = self.order[self.current_index]
            return current == name

# --- Manager Class (Sequential) ---
class LumiRamiManager:
    def __init__(self, ws_send_func: Callable[[bytes, str], None], flush_stt_func: Callable[[str], None] = None):
        self.ws_send = ws_send_func
        self.flush_stt = flush_stt_func
        self.turn_manager = TurnManager()
        self.running = False
        self.queues = {
            "lumi": asyncio.Queue(),
            "rami": asyncio.Queue()
        }
        self.configs = {
            "lumi": {"voice": "Puck", "instruction": RUMI_INSTRUCTION}, 
            "rami": {"voice": "Aoede", "instruction": RAMI_INSTRUCTION}  
        }

    async def start(self):
        self.running = True
        print("[LumiRami] Starting Sequential Dual Sessions...")
        if not API_KEY:
             print("[Error] No GEMINI_API_KEY")
             return
        
        asyncio.create_task(self._run_persona("lumi"))
        asyncio.create_task(self._run_persona("rami"))
        asyncio.create_task(self._auto_release_task())

    async def stop(self):
        self.running = False

    async def _auto_release_task(self):
        # Watchdog for stuck turns
        while self.running:
            await asyncio.sleep(1.0)
            async with self.turn_manager.lock:
                 # If AI has turn for > 15s, force skip?
                 # Or if USER has turn for > 60s, it's fine.
                 current = self.turn_manager.order[self.turn_manager.current_index]
                 elapsed = time.time() - self.turn_manager.last_transition_time
            
            if current != "USER" and elapsed > 20.0:
                 print(f"[Watchdog] {current} took too long ({elapsed:.1f}s). Forcing next turn.")
                 await self.turn_manager.advance_turn()

    async def push_audio(self, audio_data: bytes):
        # Ensure it's USER turn when receiving audio
        # If Rami is speaking and User interrupts, we might want to allow it.
        # But specifically for "Sequential", we assume User speaks only when index=0.
        # However, physically User can speak anytime.
        
        # [Strict Logic]: Only process audio if it is USER turn.
        # But we need to switch TO user turn if they speak?
        # User requested: User -> Lumi -> Rami -> User.
        # So if User speaks during Rami's turn, we should probably ignore or buffer?
        # Let's stick to: Always put in queue, let Gemini decide response.
        # But we ONLY allow Gemini to generate Audio if it's THEIR turn.
        
        await self.queues["lumi"].put(("USER", audio_data))
        await self.queues["rami"].put(("USER", audio_data))

    async def handle_stt_result(self, text: str, role: str):
        if not text: return
        print(f"[STT] {role.upper()}: {text}")

        if role == "user":
            # User finished speaking a phrase.
            # If we are in USER turn, we should transition to Lumi?
            # Issue: User might speak multiple sentences. 
            # We need a robust 'End of Speech' signal.
            # For now, let's assume valid detailed input = Turn End.
            if await self.turn_manager.is_my_turn("USER"):
                 print("   [Logic] User speech detected. Passing turn to LUMI.")
                 await self.turn_manager.advance_turn() # USER -> LUMI

        else:
            # AI Speaker
            speaker = role # "lumi" or "rami"
            context_msg = f"[System] Peer({speaker}) said: \"{text}\""
            
            # Cross-inject
            peer = "rami" if speaker == "lumi" else "lumi"
            await self.queues[peer].put(("SYSTEM_CONTEXT", context_msg))

    async def _run_persona(self, name: str):
        config_data = self.configs[name]
        client = genai.Client(api_key=API_KEY)
        my_queue = self.queues[name]
        
        config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {"prebuilt_voice_config": {"voice_name": config_data["voice"]}}
            },
            "system_instruction": {"parts": [{"text": config_data["instruction"]}]}, 
            "tools": tools_def 
        }

        while self.running:
            try:
                print(f"[{name}] Connecting...")
                async with client.aio.live.connect(model=MODEL_NAME, config=config) as session:
                    print(f"[{name}] Connected!")
                    
                    async def send_loop():
                        print(f"[{name}] Send Loop Started")
                        while self.running:
                            try:
                                try:
                                    item = await my_queue.get()
                                    source, content = item 
                                    
                                    if source == "USER":
                                        await session.send_realtime_input(audio={"data": content, "mime_type": "audio/pcm"})
                                    elif source == "SYSTEM_CONTEXT":
                                        print(f"[{name}] Sending SYSTEM_CONTEXT: {content[:30]}...")
                                        await session.send_realtime_input(text=content)
                                    elif source == "TOOL_RESPONSE":
                                        print(f"[{name}] Sending TOOL_RESPONSE")
                                        await session.send_realtime_input(tool_response=content)
                                    
                                    my_queue.task_done()
                                
                                except asyncio.CancelledError:
                                    raise
                                
                            except asyncio.CancelledError: 
                                print(f"[{name}] Send Loop Cancelled")
                                break
                            except Exception as e:
                                print(f"[{name}] Send Loop Error: {e}")
                                traceback.print_exc()
                                # [Reliability] Re-queue item so it's not lost during reconnect
                                if 'item' in locals():
                                    print(f"[{name}] Re-queueing failed item due to error.")
                                    await my_queue.put(item) 
                                break

                    sender_task = asyncio.create_task(send_loop())
                    
                    try:
                        print(f"[{name}] Receive Loop Starting...")
                        while self.running: # [FIX] Persistent Loop INSIDE Session
                            try:
                                async for response in session.receive():
                                    if not self.running: break
                                    
                                    # 1. Model Turn (Audio)
                                    if response.server_content and response.server_content.model_turn:
                                        for part in response.server_content.model_turn.parts:
                                            if part.inline_data:
                                                # STRICT TURN CHECK
                                                if await self.turn_manager.is_my_turn(name):
                                                    await self.ws_send(part.inline_data.data, name)
                                    
                                    # 2. Turn Complete Signal
                                    if response.server_content and response.server_content.turn_complete:
                                        if await self.turn_manager.is_my_turn(name):
                                             print(f"[{name}] Turn Complete. Advancing Sequence.")
                                             if self.flush_stt: await self.flush_stt(name) 
                                             await self.turn_manager.advance_turn()
                                    
                                    # 3. Tool Call
                                    if response.tool_call:
                                        await self._handle_tool_call(session, response.tool_call, my_queue)

                                print(f"[{name}] 'session.receive()' iterator ended. Re-entering loop to maintain session...") 
                                # Do NOT break. Loop back and call receive() again.
                                
                            except asyncio.CancelledError:
                                raise
                            except Exception as e:
                                print(f"[{name}] Receive Loop Error: {e}")
                                traceback.print_exc()
                                break # If error, break inner loop to trigger outer reconnection

                    except asyncio.CancelledError: 
                        print(f"[{name}] Receive Loop Cancelled")
                        break
                    except Exception as e:
                        print(f"[{name}] Receive Session Error: {e}")
                        traceback.print_exc() 
                    finally:
                        print(f"[{name}] Cleaning up Sender Task...")
                        if self.flush_stt: await self.flush_stt(name) 
                        sender_task.cancel()

                print(f"[{name}] Async Context Exited.") 

            except Exception as e:
                print(f"[{name}] Session Connection Error: {e}")
                traceback.print_exc() 
                await asyncio.sleep(2)

    async def _handle_tool_call(self, session, tool_call, queue):
        print(f"   >>> [Tool] Gemini Request: {tool_call}")
        function_responses = []
        for fc in tool_call.function_calls:
            print(f"      Call: {fc.name}({fc.args})")
            result = {"result": "success", "message": "Tool executed (Stub)"}
            function_responses.append({
                "id": fc.id,
                "name": fc.name,
                "response": result
            })
        await queue.put(("TOOL_RESPONSE", {"function_responses": function_responses}))
