import os
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
import azure.cognitiveservices.speech as speechsdk
import sys
from modules.cosmos_db import cosmos_service
from modules.memory import memory_service

app = FastAPI()

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
        
    print(f"[Server] Client connected: {user_id}")

    if not API_KEY or not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        print("[Error] Missing API Keys.")
        await ws.close(code=1008, reason="API Keys missing")
        return

    # 2. Load Memory (Context)
    # Fetch ALL past summaries for this user
    past_memories = cosmos_service.get_all_memories(user_id)
    memory_context = ""
    if past_memories:
        memory_context = "Here is the summary of past conversations with this user:\n"
        for item in past_memories:
            summary = item.get("summary", {})
            context_text = summary.get("context_summary", "No summary")
            date = item.get("date", "Unknown Date")
            memory_context += f"- [{date}] {context_text}\n"
        
        print(f"[Memory] Loaded {len(past_memories)} past conversation summaries.")

    # Initialize Gemini
    client = genai.Client(api_key=API_KEY)
    
    # Inject Memory into System Instruction
    system_instruction = "You are Aira, a helpful AI assistant."
    if memory_context:
        system_instruction += f"\n\n[MEMORY LOADED]\n{memory_context}\nUse this context to personalize your responses."

    config = {
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "voice_config": {"prebuilt_voice_config": {"voice_name": "Aoede"}}
        },
        "system_instruction": system_instruction
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
            print("[Gemini] Connected to Live API")
            state["last_ai_write_time"] = asyncio.get_running_loop().time()
            
            async def receive_from_client():
                try:
                    while True:
                        # [Fix 2] Handle Client Disconnect gracefully
                        data = await ws.receive_bytes()
                        if not data: continue
                        await session.send_realtime_input(audio={"data": data, "mime_type": "audio/pcm;rate=16000"})
                        user_push_stream.write(data)
                except WebSocketDisconnect:
                    print("[Server] WebSocket Disconnected (Receive Loop)")
                    return # Clean exit logic will be handled by finally block
                except Exception as e:
                    print(f"[Server] Error processing input: {e}")

            async def send_to_client():
                try:
                    while True:
                        async for response in session.receive():
                            if response.server_content and response.server_content.model_turn:
                                for part in response.server_content.model_turn.parts:
                                    if part.inline_data:
                                        audio_bytes = part.inline_data.data
                                        await ws.send_bytes(audio_bytes)
                                        ai_push_stream.write(audio_bytes)
                                        # Update state: Audio received, not flushed yet
                                        state["last_ai_write_time"] = asyncio.get_running_loop().time()
                                        state["flushed"] = False
                            
                            # [Fix 3] Monitor Gemini Turn Complete
                            if response.server_content and response.server_content.turn_complete:
                                pass

                except Exception as e:
                    print(f"[Server] Error processing output: {e}")
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
                            ai_push_stream.write(silence_chunk)
                            state["flushed"] = True # Mark as flushed to STOP sending silence
                            
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print(f"[Server] Smart Flush Error: {e}")

            # Run tasks
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(receive_from_client()), 
                    asyncio.create_task(send_to_client()),
                    asyncio.create_task(smart_flush_injector())
                ],
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending: task.cancel()

    except Exception as e:
        print(f"[Server] Session Error or Disconnect: {e}")
    finally:
        # Cleanup
        print("[Server] Cleaning up resources...")
        user_recognizer.stop_continuous_recognition()
        ai_recognizer.stop_continuous_recognition()
        try: await ws.close() 
        except: pass
        print("[Server] Connection closed")

        # 3. Save Memory (Summarization)
        if session_transcript and len(session_transcript) > 2: # Don't save empty sessions
            print("[Memory] Summarizing session...")
            full_text = "\n".join(session_transcript)
            summary_json = memory_service.summarize(full_text)
            
            if summary_json:
                cosmos_service.save_memory(user_id, full_text, summary_json)
                print(f"[Memory] Session saved for {user_id}")
            else:
                print("[Memory] Summarization failed or returned empty.")

# --- Static Files (Frontend) ---
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_front", "out")

if os.path.exists(FRONTEND_BUILD_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD_DIR, html=True), name="static")
else:
    @app.get("/")
    def read_root():
        return {"status": "Frontend build not found. Please run 'npm run build' in temp_front."}

if __name__ == "__main__":
    import uvicorn
    # Use use_colors=False to fix ANSI escape sequences on Windows CMD
    uvicorn.run(app, host="0.0.0.0", port=8000, use_colors=False)
