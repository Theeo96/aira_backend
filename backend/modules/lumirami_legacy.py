import asyncio
import os
import json
import time
from typing import Literal, Dict, Optional, Callable, Any
from google import genai
from dotenv import load_dotenv

# Load env variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-native-audio-preview-12-2025"

COMMON_INSTRUCTION = """
[CRITICAL INSTRUCTION: FACTUALITY & PROACTIVITY]
1. **TRUTH ONLY**: context info is the only truth. No hallucinations.
2. **VISION**: Passive mode. Only speak if addressed or CRITICAL emergency.
3. **STYLE**: Vague and brief initiation. Detailed response only when asked.
"""

RUMI_INSTRUCTION = f"""
You are 'Lumi' (루미), a male AI persona.
- Role: Emotional support, empathetic, warm, friend-like peer.
- Tone: Informal (Banmal), warm, soft, slightly fast.
- Interaction: 
  - If user calls "Lumi", answer immediately.
  - If user calls "Rami", SILENCE.
  - If no name, and Rami just spoke, you follow up naturally (don't monopolize).
  - **DO NOT SPEAK FIRST** unless the user speaks to you.

{COMMON_INSTRUCTION}
"""

RAMI_INSTRUCTION = f"""
You are 'Rami' (라미), a female AI persona.
- Role: Rational, factual, realistic advice, practical, cool-headed.
- Tone: Informal (Banmal), direct, cool, slightly fast.
- Interaction:
  - If user calls "Rami", answer immediately.
  - If user calls "Lumi", SILENCE.
  - If no name, and Lumi just spoke, you follow up naturally (don't monopolize).
  - **DO NOT SPEAK FIRST** unless the user speaks to you.

{COMMON_INSTRUCTION}
"""

class TurnManager:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.current_speaker: Optional[str] = None
        self.last_speech_time = 0
        self.waiting_for_user = False 
        self.pending_question = False 
        
    async def try_acquire(self, who: str) -> bool:
        async with self.lock:
            if self.waiting_for_user:
                return False
            if self.current_speaker is not None:
                return self.current_speaker == who
            
            # Record speech time to keep session alive in auto-release
            self.current_speaker = who
            self.last_speech_time = time.time() 
            return True

    async def update_timestamp(self, who: str):
        async with self.lock:
            if self.current_speaker == who:
                self.last_speech_time = time.time()

    async def release(self, who: str):
        async with self.lock:
            if self.current_speaker == who:
                self.current_speaker = None
                self.last_speech_time = time.time()
                if self.pending_question:
                    print(f"[TurnManager] Question detected from {who}. Waiting for user response...")
                    self.waiting_for_user = True
                    self.pending_question = False

    async def set_user_turn(self):
        async with self.lock:
            self.current_speaker = "USER" 
            self.waiting_for_user = False 
            self.pending_question = False
            self.last_speech_time = time.time()

    async def flag_question_pending(self):
        async with self.lock:
            self.pending_question = True

    async def force_release(self):
        async with self.lock:
            if self.current_speaker and self.current_speaker != "USER":
                print(f"[TurnManager] Force releasing stuck turn of {self.current_speaker}")
                self.current_speaker = None
                self.last_speech_time = time.time()

class LumiRamiManager:
    def __init__(self, ws_send_func: Callable[[bytes, str], None]):
        """
        Args:
            ws_send_func: Async function to send audio bytes to WebSocket client.
                          Signature: (audio_bytes, speaker_name)
        """
        self.ws_send = ws_send_func
        self.turn_manager = TurnManager()
        self.sessions = {}
        
        # Unified Input Queues: Tuple[Type, Data]
        # Type: "audio" or "text"
        self.queues: Dict[str, asyncio.Queue] = {
            "lumi": asyncio.Queue(),
            "rami": asyncio.Queue()
        }
        
        self.running = False
        self.last_ai_speaker = "lumi" # Default to lumi, tracks who spoke last for STT attribution
        
        self.configs = {
            "lumi": {"voice": "Aoede", "instruction": RUMI_INSTRUCTION},
            "rami": {"voice": "Puck", "instruction": RAMI_INSTRUCTION}
        }

    async def start(self):
        self.running = True
        print("[LumiRami] Starting Dual Persona Sessions...")
        if not API_KEY:
            print("[LumiRami] ERROR: GEMINI_API_KEY is missing!")
            return
        asyncio.create_task(self._run_persona("lumi"))
        # asyncio.create_task(self._run_persona("rami")) # TEST: Disable Rami to check concurrency
        asyncio.create_task(self._auto_release_task()) # Start watchdog

    async def stop(self):
        self.running = False
        print("[LumiRami] Stopping Sessions...")

    async def _auto_release_task(self):
        """Watchdog to release turns if stuck"""
        while self.running:
            await asyncio.sleep(0.1) # Fast polling to prevent cut-off
            now = time.time()
            
            async with self.turn_manager.lock:
                current = self.turn_manager.current_speaker
                last = self.turn_manager.last_speech_time
            
            if current:
                # If USER, release after silence (1.0s seems reasonable for End of Turn)
                if current == "USER":
                    if now - last > 1.0:
                        await self.turn_manager.force_release()
                
                # If AI, release after timeout (stuck protection, longer)
                elif now - last > 4.0:
                    await self.turn_manager.force_release()

    async def push_audio(self, audio_data: bytes):
        """
        Push user audio to BOTH personas via their Queues.
        This serializes access to the session.
        """
        await self.turn_manager.set_user_turn()
        
        for name in self.queues:
            # Put audio into each persona's queue. 
            # Note: We duplicate data.
            await self.queues[name].put(("audio", audio_data))

    async def handle_stt_result(self, text: str, role: str):
        """
        Process STT results.
        If role is 'ai', we infer the speaker from self.last_ai_speaker
        """
        if not text: return
        
        real_role = role
        if role == "ai":
            real_role = self.last_ai_speaker
            # verify validity
            if real_role not in ["lumi", "rami"]:
                real_role = "lumi" # fallback

        # 1. Question Detection
        if real_role in ["lumi", "rami"]:
            if "?" in text or "？" in text:
                print(f"[LumiRami] Question detected from {real_role}: {text}")
                await self.turn_manager.flag_question_pending()

        # 2. Peer Awareness
        if real_role == "lumi":
            system_msg = f"[System] Lumi said: {text}"
            await self.queues["rami"].put(("text", system_msg))
            
        elif real_role == "rami":
            system_msg = f"[System] Rami said: {text}"
            await self.queues["lumi"].put(("text", system_msg))

    async def _run_persona(self, name: str):
        config_data = self.configs[name]
        client = genai.Client(api_key=API_KEY)
        
        config = {
            "response_modalities": ["AUDIO"],
            # "speech_config": {
            #    "voice_config": {"prebuilt_voice_config": {"voice_name": config_data["voice"]}}
            # },
            "system_instruction": config_data["instruction"]
        }
        
        my_queue = self.queues[name]
        setattr(self, f"{name}_retry_count", 0)

        while self.running:
            try:
                print(f"[LumiRami] {name.upper()} connecting...")
                async with client.aio.live.connect(model=MODEL_NAME, config=config) as session:
                    self.sessions[name] = session
                    print(f"[LumiRami] {name.upper()} CONNECTED.")
                    setattr(self, f"{name}_retry_count", 0)

                    # --- Input Sender Task (Serialized) ---
                    async def input_sender():
                        while self.running:
                            try:
                                item_type, content = await my_queue.get()
                                
                                if item_type == "audio":
                                    # [Changed] Remove rate=16000, align with reference code
                                    await session.send_realtime_input(audio={"data": content, "mime_type": "audio/pcm"})
                                elif item_type == "text":
                                    print(f"[LumiRamiTRACE] {name} sending text: {content}")
                                    await session.send_realtime_input(text=content)
                                
                                my_queue.task_done()
                            except asyncio.CancelledError:
                                break
                            except Exception as e:
                                # Connection likely closed
                                print(f"[LumiRami] Sender error in {name}: {e}")
                                break
                    
                    sender_task = asyncio.create_task(input_sender())

                    try:
                        print(f"[LumiRami] {name.upper()} entered receive loop.")
                        async for response in session.receive():
                            if not self.running: break

                            if response.server_content and response.server_content.model_turn:
                                for part in response.server_content.model_turn.parts:
                                    if part.inline_data:
                                        if await self.turn_manager.try_acquire(name):
                                            # Update Last Speaker for STT attribution
                                            self.last_ai_speaker = name
                                            # Keep alive the turn
                                            await self.turn_manager.update_timestamp(name)
                                            
                                            # [DEBUG] Save Audio to File
                                            # 테스트용으로 수정함. 원상복구시 주석처리한 위의 원본코드 사용
                                            try:
                                                filename = f"backend/temp_audio/{name}_debug.pcm"
                                                with open(filename, "ab") as f:
                                                    f.write(part.inline_data.data)
                                            except Exception as write_err:
                                                print(f"[LumiRami] File write error: {write_err}")

                                            # Output Audio
                                            await self.ws_send(part.inline_data.data, name) 
                                            
                            if response.server_content and response.server_content.turn_complete:
                                await self.turn_manager.release(name)
                        
                        print(f"[LumiRami] {name.upper()} stream ended.")
                                
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                         print(f"[LumiRami] Receiver error in {name}: {e}")
                    finally:
                        sender_task.cancel()
                        # Ensure lock is released if session dies while speaking
                        await self.turn_manager.release(name)
                        
            except Exception as e:
                print(f"[LumiRami] {name} session setup error: {e}")
            
            cnt = getattr(self, f"{name}_retry_count") + 1
            setattr(self, f"{name}_retry_count", cnt)
            
            if self.running:
                print(f"[LumiRami] {name.upper()} reconnecting in 2s... (Retry {cnt})")
                await asyncio.sleep(2)
