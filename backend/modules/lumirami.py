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
# MODEL_NAME = "gemini-2.0-flash-exp" # Legacy?
MODEL_NAME = "gemini-2.5-flash-native-audio-preview-12-2025"

# --- Detailed Instructions from Legacy 2 ---
COMMON_INSTRUCTION = """
[CRITICAL INSTRUCTION: FACTUALITY & PROACTIVITY]

0. **LANGUAGE**: 
    - **ALWAYS speak in KOREAN.** (한국어로만 말할 것)
    - Do NOT use English unless explicitly asked to translate.


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
    - Otherwise, **yield the turn without saying anything (DO NOT SAY "침묵" OR ANY WORDS. JUST YIELD).**

3. **CONVERSATION STYLE**:
   - **LENGTH**: **EXTREMELY CRITICAL: Keep ALL responses extremely short, conversational, and natural. DO NOT speak more than 1 or 2 short sentences.**
   - **NO REPETITION**: 절대 "루미 말대로", "라미가 말한 것처럼" 등 동료의 말을 반복하거나 상투적인 맞장구를 치지 마.
   - **INITIATION**: DO NOT SPEAK FIRST. When the connection opens, WAIT in silence until the human user explicitly speaks or asks a question. Do not assume any pre-existing conversation. If you must respond, be vague and brief (max 1 sentence). "Are you coding?", "Error?"
   - **NATURAL DISAGREEMENT**: 동료 AI의 의견에 반박하거나 다른 의견을 낼 때는 "맞아", "그래" 처럼 영혼 없이 동의하는 단어로 시작하지 마. 자연스럽게 "음 나는 그래도...", "하지만~" 처럼 의견을 전개해.
   - **RESPONSE**: Be conversational but ultra-brief. Answer the question directly without long winded explanations.
"""

RUMI_INSTRUCTION = f"""
너는 '루미'(Lumi)라는 이름의 남성 AI 페르소나야.
- 역할: 감성적 지지, 공감, 따뜻함, 친구 같은 동료.
- 말투: 반말, 따뜻하고 부드러움, 말 속도 약간 빠름.
- 상호작용 규칙:
    1. 사용자가 "루미야", "루미" 부르면 즉시 대답.
    2. 사용자가 "라미야" 부르면 대답하지 마 (절대 "침묵"이라고 말하지 말고 말을 아예 꺼내지 마).
    3. 이름 호명이 없으면?
        - 라미가 방금 말을 마쳤다면(System 메시지 확인), 네가 이어서 자연스럽게 반응해.
        - 네가 방금 말을 많이 했다면(독점 금지), 라미에게 턴을 넘기고 아무 말도 하지 마.

{COMMON_INSTRUCTION}
"""

RAMI_INSTRUCTION = f"""
너는 '라미'(Rami)라는 이름의 여성 AI 페르소나야.
- 역할: 이성적 조언, 사실 기반, 현실적, 실질적 도움, 냉철함.
- 말투: 반말, 시원시원하고 직설적, 말 속도 약간 빠름.
- 상호작용 규칙:
    1. 사용자가 "라미야", "라미" 부르면 즉시 대답.
    2. 사용자가 "루미야" 부르면 대답하지 마 (절대 "침묵"이라고 말하지 말고 말을 아예 꺼내지 마).
    3. 이름 호명이 없으면?
        - 루미가 방금 말을 마쳤다면(System 메시지 확인), 네가 이어서 자연스럽게 반응해.
        - 네가 방금 말을 많이 했다면(독점 금지), 루미에게 턴을 넘기고 아무 말도 하지 마.

{COMMON_INSTRUCTION}
"""

# --- Tool Definitions (Optional, kept for strict port if needed) ---
tools_def = [
    {
        "function_declarations": [
            {
                "name": "save_memory",
                "description": "Save events.",
                "parameters": {"type": "OBJECT", "properties": {"content": {"type": "STRING"}}, "required": ["content"]}
            }
        ]
    }
]

# --- Turn Manager (Legacy 2 Dynamic Logic) ---
class TurnManager:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.current_speaker: Optional[str] = None
        self.last_speech_time = 0
        self.waiting_for_user = False # Block AI until user speaks
        print("   >>> [TurnManager] Initialized (Dynamic).")
        
    async def try_acquire(self, who: str) -> bool:
        async with self.lock:
            # If waiting for user, DENY all AI turns
            if self.waiting_for_user:
                return False

            # If I already have the turn, keep it
            if self.current_speaker == who:
                self.last_speech_time = time.time()
                return True
            
            # If turn is free, take it
            if self.current_speaker is None:
                self.current_speaker = who
                self.last_speech_time = time.time()
                print(f"[TurnManager] Turn acquired by {who}")
                return True
            
            # Someone else has the turn
            return False

    async def update_timestamp(self, who: str):
        async with self.lock:
            if self.current_speaker == who:
                self.last_speech_time = time.time()

    async def release(self, who: str):
        async with self.lock:
            if self.current_speaker == who:
                self.current_speaker = None
                print(f"[TurnManager] Turn released by {who}")

    async def force_release(self):
        async with self.lock:
            if self.current_speaker:
                print(f"[TurnManager] Turn FORCED released (was {self.current_speaker})")
                self.current_speaker = None

    async def set_waiting(self, enabled: bool):
        async with self.lock:
            if self.waiting_for_user != enabled:
                self.waiting_for_user = enabled
                if enabled: 
                    print("   >>> [Logic] Entering WAIT_FOR_USER mode. AI will be silent.")
                else: 
                    print("   >>> [Logic] Exiting WAIT_FOR_USER mode.")

    async def set_user_turn(self):
        """Called when user speaks to break the wait"""
        async with self.lock:
            # Force release AI to let user speak freely
            self.current_speaker = None 
            if self.waiting_for_user:
                print("   >>> [Logic] User detected! Breaking infinite wait.")
                self.waiting_for_user = False

# --- Manager Class (Merged) ---
class LumiRamiManager:
    def __init__(self, ws_send_func: Callable[[bytes, str], None], flush_stt_func: Callable[[str], None] = None):
        self.ws_send = ws_send_func
        self.flush_stt = flush_stt_func
        self.turn_manager = TurnManager()
        self.running = False
        
        # Legacy State
        self.last_ai_speaker = "lumi" 
        self.primary_speaker = "lumi" 
        self.ai_turn_count = 0 
        
        self.queues: Dict[str, asyncio.Queue] = {
            "lumi": asyncio.Queue(),
            "rami": asyncio.Queue()
        }
        
        self.configs = {
            "lumi": {"voice": "Puck", "instruction": RUMI_INSTRUCTION}, 
            "rami": {"voice": "Aoede", "instruction": RAMI_INSTRUCTION}  
        }
        self.memory_context = {"lumi": "", "rami": ""}

    async def start(self, lumi_memory: str = "", rami_memory: str = ""):
        self.running = True
        self.memory_context["lumi"] = lumi_memory
        self.memory_context["rami"] = rami_memory
        
        print("[LumiRami] Starting Merged Dual Sessions (Legacy Logic + Stable Loop)...")
        if not API_KEY:
             print("[Error] No GEMINI_API_KEY")
             return
        
        asyncio.create_task(self._run_persona("lumi"))
        asyncio.create_task(self._run_persona("rami"))
        asyncio.create_task(self._auto_release_task())

    async def stop(self):
        self.running = False
        print("[LumiRami] Stopping...")

    async def _auto_release_task(self):
        """Watchdog to release turns if silence for too long (Legacy Logic)"""
        while self.running:
            await asyncio.sleep(0.1)
            async with self.turn_manager.lock:
                current = self.turn_manager.current_speaker
                last = self.turn_manager.last_speech_time
            
            if current:
                # If silence > 1.5s (Legacy Tuned), assume turn over
                if time.time() - last > 1.5:
                    # [Legacy logic with Fix]
                    # print(f"[LumiRami] Silence detected for {current}. Force releasing.")
                    if self.flush_stt: await self.flush_stt(current) 
                    await self.turn_manager.force_release()

    async def push_audio(self, audio_data: bytes):
        # [Legacy Logic] Send to ALL AIs
        # Using "audio" type key as per legacy
        for name, q in self.queues.items():
            await q.put(("audio", audio_data))

    async def handle_stt_result(self, text: str, role: str):
        if not text: return
        
        # 1. Identify Speaker
        speaker = role
        if role == "ai":
             speaker = self.last_ai_speaker if self.last_ai_speaker else "AI"
             
        # [Log Cleanup] Server already logs this as "STT Recorded".
        # print(f"[STT] {speaker.upper()}: {text}")

        # [Legacy Logic]
        if role == "user":
            self.ai_turn_count = 0 # Reset count
            await self.turn_manager.set_user_turn() # Unlock
            
            # Keyword Switching
            if "라미" in text or "나미" in text: 
                 self.primary_speaker = "rami"
                 print(f"[LumiRami] Primary Switched to RAMI (Keyword)")
            elif "루미" in text:
                 self.primary_speaker = "lumi"
                 print(f"[LumiRami] Primary Switched to LUMI (Keyword)")
            return

        # AI Turn Handling
        self.ai_turn_count += 1
        print(f"[Logic] AI Turn Count: {self.ai_turn_count}")

        # Inject to Peer
        message = f"[System] Peer({speaker}) said: \"{text}\""
        
        # Infinite Loop Prevention
        if self.ai_turn_count >= 3:
            print("[Logic] Max AI turns reached! Forcing User Inclusion.")
            message += "\n\n[SYSTEM INSTRUCTION] STOP debating. SUMMARIZE and ASK USER."
            await self.turn_manager.set_waiting(True)
            
        for name, q in self.queues.items():
            if name != speaker and name != "ai": 
                await q.put(("text", message))

    async def handle_multimodal_input(self, text: str, image_bytes: bytes = None):
        """Processes text and optional image payload from the frontend directly into Gemini"""
        print(f"[LumiRami] Multimodal Input Received. Text: {text[:20]} Image: {'Yes' if image_bytes else 'No'}")
        
        # 1. Reset user turns (same as voice STT)
        self.ai_turn_count = 0
        await self.turn_manager.set_user_turn()
        
        from google.genai import types
        
        # 2. Build the turn natively for google-genai 0.3.0
        parts = []
        if image_bytes:
            parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))
        if text:
            # Add contextual text tag indicating it was sent as an image prompt
            prefix = "[VISION_UPLOAD] " if image_bytes else "[USER_TEXT_INPUT] "
            parts.append(types.Part.from_text(text=f"{prefix}{text}"))
            
        turn = [{"role": "user", "parts": parts}]
        
        # 3. Queue into all running AI personas
        for name, q in self.queues.items():
            await q.put(("turns", turn))

    async def _run_persona(self, name: str):
        config_data = self.configs[name]
        client = genai.Client(api_key=API_KEY)
        my_queue = self.queues[name]
        
        # [Memory Injection]
        full_instruction = config_data["instruction"]
        if self.memory_context.get(name):
            full_instruction += f"\n\n[REMEMBERED MEMORY from Past Conversations]:\n{self.memory_context[name]}"
            print(f"[{name}] Injected Long-Term Memory ({len(self.memory_context[name])} chars).")

        # [Config Fix] Use Strict Dict Structure from Stable version
        config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {"prebuilt_voice_config": {"voice_name": config_data["voice"]}}
            },
            "system_instruction": {"parts": [{"text": full_instruction}]}, 
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
                                    source, content = item # "audio"/"text"
                                    
                                    # [Legacy Type Handling]
                                    if source == "audio":
                                        await session.send_realtime_input(audio={"data": content, "mime_type": "audio/pcm;rate=16000"})
                                    elif source == "context":
                                        print(f"[{name}] Sending SILENT CTX: {content[:30]}...")
                                        await session.send_client_content(
                                            turns=[{"role": "user", "parts": [{"text": content}]}],
                                            turn_complete=False
                                        )
                                    elif source == "text":
                                        print(f"[{name}] Sending TEXT CTX: {content[:30]}...")
                                        await session.send_client_content(
                                            turns=[{"role": "user", "parts": [{"text": content}]}],
                                            turn_complete=True
                                        )
                                    elif source == "turns":
                                        print(f"[{name}] Sending TURNS CTX...")
                                        await session.send_client_content(
                                            turns=content,
                                            turn_complete=True
                                        )
                                    elif source == "TOOL_RESPONSE":
                                        print(f"[{name}] Sending TOOL_RESPONSE")
                                        from google.genai import types
                                        parts = []
                                        for f in content["function_responses"]:
                                            fc_resp = types.FunctionResponse(
                                                id=f["id"],
                                                name=f["name"],
                                                response=f["response"]
                                            )
                                            parts.append(types.Part(function_response=fc_resp))
                                        
                                        await session.send_client_content(
                                            turns=[{"role": "user", "parts": parts}],
                                            turn_complete=True
                                        )
                                    
                                    my_queue.task_done()
                                except asyncio.CancelledError: raise
                            except asyncio.CancelledError: break
                            except Exception as e:
                                print(f"[{name}] Send Loop Error: {e}")
                                # [Reliability Fix] Re-queue
                                if 'item' in locals():
                                    print(f"[{name}] Re-queueing failed item.")
                                    await my_queue.put(item) 
                                break

                    sender_task = asyncio.create_task(send_loop())
                    
                    try:
                        print(f"[{name}] Receive Loop Starting...")
                        
                        # [STABLE ARCHITECTURE] Persistent Loop
                        while self.running:
                            try:
                                async for response in session.receive():
                                    if not self.running: break
                                    
                                    # 1. Model Turn (Audio)
                                    if response.server_content and response.server_content.model_turn:
                                        for part in response.server_content.model_turn.parts:
                                            if part.inline_data:
                                                # [Legacy Logic] Double-Speak Check
                                                if self.ai_turn_count == 0 and name != self.primary_speaker:
                                                    continue # Respect Primary

                                                # [Legacy Logic] Turn Acquisition
                                                if await self.turn_manager.try_acquire(name):
                                                    self.last_ai_speaker = name
                                                    await self.turn_manager.update_timestamp(name)
                                                    await self.ws_send(part.inline_data.data, name)
                                    
                                    # 2. Turn Complete Signal (New Fit)
                                    if response.server_content and response.server_content.turn_complete:
                                         if self.current_speaker_is(name):
                                             if self.flush_stt: await self.flush_stt(name)
                                    
                                    # 3. Tool Call
                                    if response.tool_call:
                                        await self._handle_tool_call(session, response.tool_call, my_queue)

                                print(f"[{name}] Iterator ended (Natural). Re-entering loop...")
                                
                            except asyncio.CancelledError: raise
                            except Exception as e:
                                print(f"[{name}] Inner Receive Error: {e}")
                                break # Trigger reconnect

                    except asyncio.CancelledError: break
                    except Exception as e:
                        print(f"[{name}] Receiver Error: {e}")
                    finally:
                        sender_task.cancel()

                print(f"[{name}] Async Context Exited.") 

            except Exception as e:
                print(f"[{name}] Connection Error: {e}")
                traceback.print_exc() 
                await asyncio.sleep(2)

    def current_speaker_is(self, name):
        # Helper for check
        return self.turn_manager.current_speaker == name

    async def _handle_tool_call(self, session, tool_call, queue):
        print(f"   >>> [Tool] Gemini Request: {tool_call}")
        function_responses = []
        for fc in tool_call.function_calls:
            print(f"      Call: {fc.name}({fc.args})")
            result = {"result": "success", "message": "Tool executed"}
            function_responses.append({"id": fc.id, "name": fc.name, "response": result})
        await queue.put(("TOOL_RESPONSE", {"function_responses": function_responses}))
