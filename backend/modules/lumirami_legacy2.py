import asyncio
import os
import time
import traceback
from typing import Callable, Dict, Optional
from google import genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-native-audio-preview-12-2025"

# --- Detailed Instructions from Legacy ---
# --- Detailed Instructions from Legacy (Korean) ---
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
너는 '루미'(Lumi)라는 이름의 남성 AI 페르소나야.
- 역할: 감성적 지지, 공감, 따뜻함, 친구 같은 동료.
- 말투: 반말, 따뜻하고 부드러움, 말 속도 약간 빠름.
- 상호작용 규칙:
    1. 사용자가 "루미야", "루미" 부르면 즉시 대답.
    2. 사용자가 "라미야" 부르면 즉시 침묵(Stop Talking).
    3. 이름 호명이 없으면?
        - 라미가 방금 말을 마쳤다면(System 메시지 확인), 네가 이어서 자연스럽게 반응해.
        - 네가 방금 말을 많이 했다면(독점 금지), 라미에게 턴을 넘기고 침묵해.

{COMMON_INSTRUCTION}
"""

RAMI_INSTRUCTION = f"""
너는 '라미'(Rami)라는 이름의 여성 AI 페르소나야.
- 역할: 이성적 조언, 사실 기반, 현실적, 실질적 도움, 냉철함.
- 말투: 반말, 시원시원하고 직설적, 말 속도 약간 빠름.
- 상호작용 규칙:
    1. 사용자가 "라미야", "라미" 부르면 즉시 대답.
    2. 사용자가 "루미야" 부르면 즉시 침묵(Stop Talking).
    3. 이름 호명이 없으면?
        - 루미가 방금 말을 마쳤다면(System 메시지 확인), 네가 이어서 자연스럽게 반응해.
        - 네가 방금 말을 많이 했다면(독점 금지), 루미에게 턴을 넘기고 침묵해.

{COMMON_INSTRUCTION}
"""

# --- Tool Definitions ---
# --- Tool Definitions ---
# [REMOVED] Tool Use Disabled for Stability Testing
# SWITCH_SPEAKER_TOOL = { ... }

# --- Turn Manager ---
class TurnManager:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.current_speaker: Optional[str] = None
        self.last_speech_time = 0
        self.waiting_for_user = False # [NEW] Block AI until user speaks
        
    async def try_acquire(self, who: str) -> bool:
        async with self.lock:
            # [NEW] If waiting for user, DENY all AI turns
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
            if self.waiting_for_user:
                print("   >>> [Logic] User detected! Breaking infinite wait.")
                self.waiting_for_user = False

class LumiRamiManager:
    def __init__(self, ws_send_func: Callable[[bytes, str], None], flush_stt_func: Callable[[str], None] = None):
        self.ws_send = ws_send_func
        self.flush_stt = flush_stt_func # [NEW]
        self.turn_manager = TurnManager()
        self.running = False
        self.last_ai_speaker = "lumi" 
        self.primary_speaker = "lumi" 
        self.ai_turn_count = 0 # [NEW] Track AI-to-AI turns 
        
        self.queues: Dict[str, asyncio.Queue] = {
            "lumi": asyncio.Queue(),
            "rami": asyncio.Queue()
        }
        self.loser_muted = {"lumi": False, "rami": False} 
        
        self.configs = {
            "lumi": {"voice": "Puck", "instruction": RUMI_INSTRUCTION}, 
            "rami": {"voice": "Aoede", "instruction": RAMI_INSTRUCTION}  
        }

    async def start(self):
        self.running = True
        print("[LumiRami] Starting Simplified Dual Sessions...")
        if not API_KEY:
            print("[LumiRami] ERROR: GEMINI_API_KEY is missing!")
            return
        asyncio.create_task(self._run_persona("lumi"))
        asyncio.create_task(self._run_persona("rami"))
        asyncio.create_task(self._auto_release_task())

    async def stop(self):
        self.running = False
        print("[LumiRami] Stopping Sessions...")

    async def _auto_release_task(self):
        """Watchdog to release turns if silence for too long"""
        while self.running:
            await asyncio.sleep(0.1)
            async with self.turn_manager.lock:
                current = self.turn_manager.current_speaker
                last = self.turn_manager.last_speech_time
            
            if current:
                # If silence > 1.5s (Tuned), assume turn over
                if time.time() - last > 1.5:
                    print(f"[LumiRami] Silence detected for {current}. Force releasing turn & flushing STT.")
                    if self.flush_stt:
                        await self.flush_stt(current) 
                    await self.turn_manager.force_release()

    async def push_audio(self, audio_data: bytes):
        # [Sequential Logic]
        # Only the PRIMARY speaker hears the audio.
        # The Secondary speaker will "read" the situation via STT.
        
        # await self.turn_manager.force_release() # Barge-in Disabled to prevent thrashing
        
        # [Legacy Restore] Send audio to ALL AIs to keep their sessions alive (Base Stream)
        for name, q in self.queues.items():
            await q.put(("audio", audio_data))

    async def handle_stt_result(self, text: str, role: str):
        if not text: return
        
        # 1. Identify Speaker
        speaker = role
        if role == "ai":
             speaker = self.last_ai_speaker if self.last_ai_speaker else "AI"
             
        print(f"[STT] {speaker.upper()}: {text}")

        # [Turn Counting Logic]
        if role == "user":
            self.ai_turn_count = 0 # Reset count on user input
            await self.turn_manager.set_user_turn() # Unlock AI turns
            
            # [NEW] Keyword Primary Switching (Since Tools are removed)
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

        # 2. AI speech: Inject as Text to the OTHER AI (Peer) so they know what was said.
        # Format: [System] Peer(Name) said: "..."
        message = f"[System] Peer({speaker}) said: \"{text}\""
        
        # [Infinite Loop Prevention]
        # If AIs have exchanged 3+ turns, FORCE them to include the user.
        if self.ai_turn_count >= 3:
            print("[Logic] Max AI turns reached! Forcing User Inclusion via WAIT MODE.")
            message += "\n\n[SYSTEM INSTRUCTION] You have exchanged enough views with your peer. NOW, STOP debating between yourselves. SUMMARIZE the discussion briefly and ASK THE USER for their opinion/decision."
            # [NEW] Lock the turn manager so AIs cannot speak again until User speaks
            await self.turn_manager.set_waiting(True)
            
        # Send to everyone EXCEPT the speaker
        for name, q in self.queues.items():
            if name != speaker and name != "ai": 
                await q.put(("text", message))

    async def _run_persona(self, name: str):
        config_data = self.configs[name]
        client = genai.Client(api_key=API_KEY)
        
        # Re-enable speech_config for voices
        config = {
            # "tools": [SWITCH_SPEAKER_TOOL], # [REMOVED]
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {"prebuilt_voice_config": {"voice_name": config_data["voice"]}}
            },
            "system_instruction": config_data["instruction"]
        }
        
        my_queue = self.queues[name]

        while self.running:
            try:
                print(f"[LumiRami] {name.upper()} Connecting...")
                async with client.aio.live.connect(model=MODEL_NAME, config=config) as session:
                    print(f"[LumiRami] {name.upper()} CONNECTED.")
                    
                    # Sender Task
                    async def sender():
                        while self.running:
                            try:
                                # [Refactor] No Heartbeat as requested.
                                item_type, content = await my_queue.get()
                                
                                if item_type == "audio":
                                    await session.send_realtime_input(audio={"data": content, "mime_type": "audio/pcm"})
                                elif item_type == "text":
                                    await session.send_realtime_input(text=content)
                                # elif item_type == "function_response":
                                #     await session.send_realtime_input(function_response=content)
                                my_queue.task_done()
                            except asyncio.CancelledError:
                                break
                            except Exception as e:
                                print(f"[LumiRami] {name} Sender Error: {e}")
                                break
                    
                    sender_task = asyncio.create_task(sender())

                    try:
                        print(f"[LumiRami] {name.upper()} Receiving...")
                        async for response in session.receive():
                            if not self.running: break
                            
                            if response.server_content and response.server_content.model_turn:
                                for part in response.server_content.model_turn.parts:
                                    if part.inline_data:
                                        # [NEW] Double-Speak Prevention
                                        # If Turn Count is 0 (User just spoke), ONLY Primary can speak.
                                        if self.ai_turn_count == 0 and name != self.primary_speaker:
                                            continue 

                                        # Turn Logic: Try to acquire turn
                                        if await self.turn_manager.try_acquire(name):
                                            self.last_ai_speaker = name # Track who is speaking for STT
                                            await self.turn_manager.update_timestamp(name)
                                            await self.ws_send(part.inline_data.data, name)
                                    
                                            await self.turn_manager.update_timestamp(name)
                                            await self.ws_send(part.inline_data.data, name)
                                    
                                    # 2. Handle Function Calls (Speaker Switching) - [REMOVED]
                                    # if part.function_call:
                                    #     pass
                        
                        print(f"[LumiRami] {name.upper()} stream ended (Loop Finished).")

                    except asyncio.CancelledError:
                        print(f"[LumiRami] {name.upper()} Cancelled.")
                        break
                    except Exception as e:
                        print(f"[LumiRami] {name} Receiver Error: {traceback.format_exc()}")
                    finally:
                        sender_task.cancel()
                        
            except Exception as e:
                print(f"[LumiRami] {name} Connection Setup Error: {traceback.format_exc()}")
                await asyncio.sleep(2)
