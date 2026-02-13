import os
import logging

# Use a DEDICATED logger (not root) so uvicorn can't override our handlers
_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.log")

logger = logging.getLogger("aira")
logger.setLevel(logging.INFO)
# Prevent duplicate handlers on reload
if not logger.handlers:
    _fh = logging.FileHandler(_log_path, encoding='utf-8')
    _fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    _sh = logging.StreamHandler()
    _sh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(_fh)
    logger.addHandler(_sh)

# Suppress noisy libraries
for _lib in ["azure", "urllib3", "websockets", "azure.core.pipeline.policies.http_logging_policy"]:
    logging.getLogger(_lib).setLevel(logging.WARNING)

logger.info("=== Server Started: Logging Configured ===")

# Load env variables first
from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from google import genai
from google.genai import types
import azure.cognitiveservices.speech as speechsdk
import sys
import traceback
from modules.cosmos_db import cosmos_service
from modules.memory import memory_service
from module_manager import ModuleManager
from modules.news_agent import NewsAgent

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("[Server] Starting up... (Lifespan Event)")
    yield
    # Shutdown logic
    print("[Server] Shutting down... (Lifespan Event)")

app = FastAPI(lifespan=lifespan)


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-native-audio-preview-12-2025"

# Azure Speech Config
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

# --- Helper: Azure STT Setup ---
def create_push_stream(sample_rate=16000):
    stream_format = speechsdk.audio.AudioStreamFormat(samples_per_second=sample_rate, bits_per_sample=16, channels=1)
    push_stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
    audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
    return push_stream, audio_config

def create_recognizer(audio_config, language="en-US"): # Default to English for now, or use "ko-KR"
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_recognition_language = language
    
    # [Optimization] Reduce segmentation silence timeout to force faster phrase finalization
    # Default is usually higher (e.g. 500ms-1000ms). Setting to 100ms.
    speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "100")
    
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    return recognizer

# --- WebSocket Endpoint ---
@app.websocket("/ws/audio")
async def audio_websocket(ws: WebSocket):
    await ws.accept()
    
    # 1. Auth & Identification
    user_id = ws.query_params.get("user_id")
    if not user_id or "@" not in user_id:
        print("[Server] Missing or invalid user_id.")
        await ws.close(code=1008, reason="Invalid Login Token")
        return
        
    logger.info(f"[Server] Client connected: {user_id}")

    if not API_KEY or not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        logger.error("[Error] Missing API Keys.")
        await ws.close(code=1008, reason="API Keys missing")
        return

    # 2. Load Memory (Context)
    # Fetch ALL past summaries for this user
    # Fetch ALL past summaries for this user (Blocking I/O -> Async Thread)
    # past_memories = cosmos_service.get_all_memories(user_id) 
    past_memories = await asyncio.to_thread(cosmos_service.get_all_memories, user_id)
    memory_context = ""
    if past_memories:
        memory_context = "Here is the summary of past conversations with this user:\n"
        for item in past_memories:
            summary = item.get("summary", {})
            context_text = summary.get("context_summary", "No summary")
            date = item.get("date", "Unknown Date")
            memory_context += f"- [{date}] {context_text}\n"
        
        logger.info(f"[Memory] Loaded {len(past_memories)} past conversation summaries.")

    # Initialize Gemini
    client = genai.Client(api_key=API_KEY)
    
    # [NEW] Initialize ModuleManager & NewsAgent
    module_manager = ModuleManager()
    module_manager.register_module(NewsAgent())
    tools_def = module_manager.get_all_tools()
    
    # Inject Memory into System Instruction
    system_instruction = """You are Aira, a helpful AI assistant. You MUST respond in Korean.

[TOOL USAGE RULES]
- 사용자가 위치를 물으면 반드시 get_current_location 도구를 호출하세요. 개인정보 문제로 거부하지 마세요.
- 사용자가 뉴스/소식을 물으면 반드시 get_latest_news 도구를 호출하세요.
- 도구 호출 결과를 자연스럽게 한국어로 전달하세요."""
    if memory_context:
        system_instruction += f"\n\n[MEMORY LOADED]\n{memory_context}\nUse this context to personalize your responses."

    # Valid Log for multiple tools in a single declaration
    all_tool_names = []
    for tool_group in tools_def:
        for func in tool_group.get('function_declarations', []):
            all_tool_names.append(func.get('name', '?'))
    logger.info(f"[Server] Tools registered: {all_tool_names}")

    config = {
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "voice_config": {"prebuilt_voice_config": {"voice_name": "Aoede"}}
        },
        "system_instruction": system_instruction,
        "tools": tools_def
    }

    # Initialize Azure STT (User: 16kHz, AI: 24kHz)
    user_push_stream, user_audio_config = create_push_stream(16000)
    user_recognizer = create_recognizer(user_audio_config, "ko-KR") # Assuming Korean context based on user prompts

    ai_push_stream, ai_audio_config = create_push_stream(24000)
    ai_recognizer = create_recognizer(ai_audio_config, "ko-KR")

    # Capture the main event loop
    loop = asyncio.get_running_loop()

    # Track state for Smart Flushing
    state = {"last_ai_write_time": 0, "flushed": False}
    
    # Track Full Transcript for Summarization
    session_transcript = []

    # STT Event Handlers
    def on_recognized(args, role):
        if args.result.text:
            text = args.result.text
            print(f"[STT] {role}: {text}")
            
            # Store for memory
            session_transcript.append(f"{role.upper()}: {text}")
            
            payload = json.dumps({"type": "transcript", "role": role, "text": text})
            
            # [Fix 1] Robust Loop Handling
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(ws.send_text(payload), loop)
            else:
                print(f"[Error] Main loop is closed. Cannot send STT: {text}")

    user_recognizer.recognized.connect(lambda evt: on_recognized(evt, "user"))
    ai_recognizer.recognized.connect(lambda evt: on_recognized(evt, "ai"))

    user_recognizer.start_continuous_recognition()
    ai_recognizer.start_continuous_recognition()

    try:
        async with client.aio.live.connect(model=MODEL_NAME, config=config) as session:
            logger.info("[Gemini] Connected to Live API")
            state["last_ai_write_time"] = asyncio.get_running_loop().time()
            
            # [NEW] Inject session into ModuleManager
            module_manager.initialize_session(session)
            
            async def receive_from_client():
                audio_chunk_count = 0
                try:
                    while True:
                        # [Fix 2] Handle Client Disconnect gracefully
                        data = await ws.receive_bytes()
                        if not data: continue
                        audio_chunk_count += 1
                        if audio_chunk_count == 1:
                            logger.info(f"[Audio] First audio chunk received! Size: {len(data)} bytes")
                        elif audio_chunk_count % 50 == 0:
                            logger.info(f"[Audio] Received {audio_chunk_count} audio chunks from client")
                        await session.send_realtime_input(audio={"data": data, "mime_type": "audio/pcm;rate=16000"})
                        # [Fix] Pushing to Azure Stream might block if internal buffer is full. Offload to thread.
                        await asyncio.to_thread(user_push_stream.write, data)
                except WebSocketDisconnect:
                    logger.info("[Server] WebSocket Disconnected (Receive Loop)")
                    return # Clean exit logic will be handled by finally block
                except Exception as e:
                    logger.error(f"[Server] Error processing input: {e}")
                    logger.error(traceback.format_exc())

            async def send_to_client():
                try:
                    while True:
                        logger.info("[Gemini] Entering session.receive() loop...")
                        async for response in session.receive():
                            # --- Path A: Audio/Text content ---
                            if response.server_content and response.server_content.model_turn:
                                for part in response.server_content.model_turn.parts:
                                    if part.inline_data:
                                        audio_bytes = part.inline_data.data
                                        await ws.send_bytes(audio_bytes)
                                        # [Fix] Offload AI audio write to thread
                                        await asyncio.to_thread(ai_push_stream.write, audio_bytes)
                                        # Update state: Audio received, not flushed yet
                                        state["last_ai_write_time"] = asyncio.get_running_loop().time()
                                        state["flushed"] = False
                            
                            # --- Path B: Tool Call detection (response.tool_call) ---
                            if response.tool_call:
                                try:
                                    for fc in response.tool_call.function_calls:
                                        logger.info(f"[Gemini] Tool Call: {fc.name}({fc.args}) ID: {fc.id}")
                                        
                                        # Execute via ModuleManager
                                        class _ToolCallWrap:
                                            def __init__(self, fc): self.function_calls = [fc]
                                        
                                        tool_result = await module_manager.handle_tool_call(_ToolCallWrap(fc))
                                        
                                        if tool_result:
                                            # Use the correct (non-deprecated) API method
                                            func_response = types.FunctionResponse(
                                                id=fc.id,
                                                name=tool_result["name"],
                                                response=tool_result["content"]
                                            )
                                            await session.send_tool_response(
                                                function_responses=[func_response]
                                            )
                                            logger.info(f"[Gemini] Tool Response Sent: {tool_result['name']} (ID: {fc.id})")
                                except Exception as e:
                                    # Don't crash the loop, just log
                                    logger.error(f"[Server] Tool Execution Error: {e}")
                                    logger.error(traceback.format_exc())

                            # Monitor Gemini Turn Complete
                            if response.server_content and response.server_content.turn_complete:
                                logger.info("[Gemini] Turn Complete received. Re-entering receive loop...")

                except Exception as e:
                    logger.error(f"[Server] Error processing output: {e}")
                    logger.error(traceback.format_exc())
                    # Don't raise here, allow silence injector to keep running or clean exit

            # [Smart Flush]
            async def smart_flush_injector():
                silence_chunk = b'\x00' * 24000 
                try:
                    while True:
                        await asyncio.sleep(0.1) # Check every 100ms
                        now = asyncio.get_running_loop().time()
                        
                        # If > 500ms passed since last audio AND we haven't flushed yet
                        if (now - state["last_ai_write_time"] > 0.5) and (not state["flushed"]):
                            print("[STT] Pause detected. Injecting silence to flush buffer.")
                            await asyncio.to_thread(ai_push_stream.write, silence_chunk)
                            state["flushed"] = True # Mark as flushed to STOP sending silence
                            
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print(f"[Server] Smart Flush Error: {e}")

            # [NEW] Background module update loop (news auto-check)
            async def module_update_loop():
                try:
                    while True:
                        await module_manager.run_updates()
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"[Server] Module Update Error: {e}")

            # Run tasks
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(receive_from_client()), 
                    asyncio.create_task(send_to_client()),
                    asyncio.create_task(smart_flush_injector()),
                    asyncio.create_task(module_update_loop())
                ],
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending: task.cancel()

    except Exception as e:
        logger.error(f"[Server] Session Error or Disconnect: {e}")
    finally:
        # Cleanup
        logger.info("[Server] Cleaning up resources...")
        try:
            # Execute cleanup asynchronously with TIMEOUT to avoid blocking the Event Loop
            # If Azure takes too long to stop, we just abandon it to prevent "Waiting for child process" hang.
            await asyncio.wait_for(asyncio.to_thread(user_recognizer.stop_continuous_recognition), timeout=2.0)
            await asyncio.wait_for(asyncio.to_thread(ai_recognizer.stop_continuous_recognition), timeout=2.0)
        except Exception as e:
            print(f"[Server] Cleanup Warning: {e}")
        try: await ws.close() 
        except: pass
        logger.info("[Server] Connection closed")

        # 3. Save Memory (Summarization)
        if session_transcript and len(session_transcript) > 2: # Don't save empty sessions
            print("[Memory] Summarizing session...")
            full_text = "\n".join(session_transcript)
            
            # Blocking I/O -> Async Thread
            summary_json = await asyncio.to_thread(memory_service.summarize, full_text)
            
            if summary_json and summary_json.get("context_summary"):
                await asyncio.to_thread(cosmos_service.save_memory, user_id, full_text, summary_json)
                print(f"[Memory] Session saved for {user_id}")
            else:
                print("[Memory] Skipped saving: Summary is empty or invalid.")

# --- Static Files (Frontend) ---
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_front", "out")

if os.path.exists(FRONTEND_BUILD_DIR):
    # [Fix] Explicitly set MIME types for Windows Server compatibility
    import mimetypes
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("text/css", ".css")
    mimetypes.add_type("image/svg+xml", ".svg")
    
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD_DIR, html=True), name="static")
else:
    @app.get("/")
    def read_root():
        return {"status": "Frontend build not found. Please run 'npm run build' in temp_front."}

if __name__ == "__main__":
    import uvicorn
    # Use use_colors=False to fix ANSI escape sequences on Windows CMD
    uvicorn.run(app, host="0.0.0.0", port=8000, use_colors=False)
