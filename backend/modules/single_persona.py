import asyncio
import os
import traceback
from typing import Callable
from google import genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-native-audio-preview-12-2025"

SYSTEM_INSTRUCTION = """
You are 'Aira', a helpful and friendly AI assistant.
- Role: Chat with the user naturally.
- Tone: Friendly, polite, and helpful.
- Language: Korean.
"""

class SinglePersonaManager:
    def __init__(self, ws_send_func: Callable[[bytes, str], None]):
        self.ws_send = ws_send_func
        self.running = False
        self.session = None
        self.input_queue = asyncio.Queue()
        self.queues = {"lumi": self.input_queue} # Fake dict to prevent server.py errors if it tries to access queues

    async def start(self):
        self.running = True
        print("[SinglePersona] Starting Single Session...")
        asyncio.create_task(self._run_session())

    async def stop(self):
        self.running = False
        print("[SinglePersona] Stopping Session...")

    async def push_audio(self, audio_data: bytes):
        # Directly put into queue
        await self.input_queue.put(("audio", audio_data))

    async def handle_stt_result(self, text: str, role: str):
        # Optional: Feed text context if needed
        # For now, just print
        if role == "user":
            print(f"[SinglePersona] User said: {text}")
            # We could send this as text context, but let's keep it simple for now
            # await self.input_queue.put(("text", f"User said: {text}"))

    async def _run_session(self):
        client = genai.Client(api_key=API_KEY)
        config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {"prebuilt_voice_config": {"voice_name": "Kore"}}
            },
            "system_instruction": SYSTEM_INSTRUCTION
        }

        while self.running:
            try:
                print("[SinglePersona] Connecting to Gemini...")
                async with client.aio.live.connect(model=MODEL_NAME, config=config) as session:
                    self.session = session
                    print("[SinglePersona] CONNECTED.")
                    
                    # Sender Task
                    async def sender():
                        while self.running:
                            try:
                                item_type, content = await self.input_queue.get()
                                if item_type == "audio":
                                    await session.send_realtime_input(audio={"data": content, "mime_type": "audio/pcm"})
                                elif item_type == "text":
                                    await session.send_realtime_input(text=content)
                                self.input_queue.task_done()
                            except Exception as e:
                                print(f"[SinglePersona] Sender Error: {e}")
                                break
                    
                    sender_task = asyncio.create_task(sender())

                    try:
                        print("[SinglePersona] Receiving...")
                        async for response in session.receive():
                            if not self.running: break
                            if response.server_content and response.server_content.model_turn:
                                for part in response.server_content.model_turn.parts:
                                    if part.inline_data:
                                        # Directly send audio back
                                        await self.ws_send(part.inline_data.data, "aira")
                    except Exception as e:
                        print(f"[SinglePersona] Receiver Error: {e}")
                    finally:
                        sender_task.cancel()
                        
            except Exception as e:
                print(f"[SinglePersona] Connection Error: {e}")
                await asyncio.sleep(2)
