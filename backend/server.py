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
from modules.lumirami import LumiRamiManager  # [NEW] Import Dual Persona Manager

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

def create_recognizer(audio_config, language="ko-KR"): # Default to Korean
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_recognition_language = language
    
    # [Optimization] Speech Segmentation Logic
    # 500ms is the "sweet spot" (fast response).
    # 1.2s was too slow (causing lag).
    # Reverting to 500ms as requested.
    speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "500")
    
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

    # 2. Load Memory (Context) - [Dual Retrieval]
    past_memories = await asyncio.to_thread(cosmos_service.get_all_memories, user_id)
    
    lumi_mem_str = ""
    rami_mem_str = ""
    
    if past_memories:
        print(f"[Memory] Loaded {len(past_memories)} past conversation summaries.")
        
        # Build specific contexts
        lumi_items = []
        rami_items = []
        
        for item in past_memories:
            date = item.get("date", "Unknown Date")
            summary = item.get("summary", {})
            
            # [Lumi Context]
            if "lumi_summary" in summary:
                lumi_items.append(f"- [{date}] {summary['lumi_summary']}")
            elif "summary_lumi" in summary: # Legacy structure
                lumi_items.append(f"- [{date}] {summary['summary_lumi'].get('context_summary', '')}")
            else:
                # Fallback to shared context
                content = summary.get("context_summary", "")
                if content: lumi_items.append(f"- [{date}] {content}")

            # [Rami Context]
            if "rami_summary" in summary:
                rami_items.append(f"- [{date}] {summary['rami_summary']}")
            elif "summary_rami" in summary: # Legacy structure
                rami_items.append(f"- [{date}] {summary['summary_rami'].get('context_summary', '')}")
            else:
                # Fallback to shared context
                content = summary.get("context_summary", "")
                if content: rami_items.append(f"- [{date}] {content}")
        
        if lumi_items:
            lumi_mem_str = "You recall these past events:\n" + "\n".join(lumi_items)
        if rami_items:
            rami_mem_str = "You recall these past events:\n" + "\n".join(rami_items)

    # Initialize Azure STT (User: 16kHz, AI: 24kHz)
    user_push_stream, user_audio_config = create_push_stream(16000)
    user_recognizer = create_recognizer(user_audio_config, "ko-KR") 

    lumi_push_stream, lumi_audio_config = create_push_stream(24000)
    lumi_recognizer = create_recognizer(lumi_audio_config, "ko-KR") # Lumi
    rami_push_stream, rami_audio_config = create_push_stream(24000)
    rami_recognizer = create_recognizer(rami_audio_config, "ko-KR") # Rami

    loop = asyncio.get_running_loop()
    session_transcript = []

    async def send_audio_to_client(audio_bytes: bytes, speaker_name: str):
        try:
            await ws.send_bytes(audio_bytes)
            if speaker_name == "lumi":
                await asyncio.to_thread(lumi_push_stream.write, audio_bytes)
            elif speaker_name == "rami":
                await asyncio.to_thread(rami_push_stream.write, audio_bytes)
        except Exception as e:
            print(f"[Server] Error sending audio to client: {e}")

    async def flush_ai_stt(speaker_name: str):
        try:
            silence = bytes(24000 * 2 * 1) 
            if speaker_name == "lumi":
                await asyncio.to_thread(lumi_push_stream.write, silence)
            elif speaker_name == "rami":
                await asyncio.to_thread(rami_push_stream.write, silence)
            print(f"[Server] Flushed STT stream for {speaker_name}")
        except Exception as e:
            print(f"[Server] Error flushing STT: {e}")

    lumi_rami_manager = LumiRamiManager(ws_send_func=send_audio_to_client, flush_stt_func=flush_ai_stt)
    
    def on_recognized(args, role):
        if args.result.text:
            text = args.result.text
            print(f"[Server] STT Recorded ({role}): {text}")
            session_transcript.append(f"{role.upper()}: {text}")
            payload = json.dumps({"type": "transcript", "role": role, "text": text})
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(ws.send_text(payload), loop)
                asyncio.run_coroutine_threadsafe(lumi_rami_manager.handle_stt_result(text, role), loop)

    user_recognizer.recognized.connect(lambda evt: on_recognized(evt, "user"))
    lumi_recognizer.recognized.connect(lambda evt: on_recognized(evt, "lumi"))
    rami_recognizer.recognized.connect(lambda evt: on_recognized(evt, "rami"))

    user_recognizer.start_continuous_recognition()
    lumi_recognizer.start_continuous_recognition()
    rami_recognizer.start_continuous_recognition()

    try:
        # Start Lumi/Rami Manager with DUAL MEMORY
        await lumi_rami_manager.start(lumi_memory=lumi_mem_str, rami_memory=rami_mem_str)
        
        async def receive_from_client():
            try:
                while True:
                    # [Fix 2] Handle Client Disconnect gracefully
                    data = await ws.receive_bytes()
                    if not data: continue
                    
                    # Push to Manager (which pushes to both Geminis)
                    await lumi_rami_manager.push_audio(data)
                    
                    # Push to Azure STT (User stream)
                    await asyncio.to_thread(user_push_stream.write, data)
                    
            except WebSocketDisconnect:
                print("[Server] WebSocket Disconnected (Receive Loop)")
                return # Clean exit logic will be handled by finally block
            except Exception as e:
                print(f"[Server] Error processing input: {e}")
                traceback.print_exc() # [DEBUG]

        # Run tasks
        # We only need receive loop here, as send loop is handled by Manager's callbacks + internal tasks
        await receive_from_client()

    except Exception as e:
        print(f"[Server] Session Error or Disconnect: {e}")
        traceback.print_exc() # [DEBUG]
    finally:
        # Cleanup
        print("[Server] Cleaning up resources...")
        await lumi_rami_manager.stop()
        
        try:
            # Execute cleanup asynchronously with TIMEOUT to avoid blocking the Event Loop
            await asyncio.wait_for(asyncio.to_thread(user_recognizer.stop_continuous_recognition), timeout=2.0)
            await asyncio.wait_for(asyncio.to_thread(lumi_recognizer.stop_continuous_recognition), timeout=2.0)
            await asyncio.wait_for(asyncio.to_thread(rami_recognizer.stop_continuous_recognition), timeout=2.0)
        except Exception as e:
            print(f"[Server] Cleanup Warning: {e}")
        try: await ws.close() 
        except: pass
        print("[Server] Connection closed")

        # 3. Save Memory (Summarization) - DUAL
        print(f"[Memory] Transcript Length: {len(session_transcript)}") # [DEBUG]
        if session_transcript and len(session_transcript) > 0: # [Modified] Lower threshold
            print("[Memory] Summarizing session (Dual Persona)...")
            full_text = "\n".join(session_transcript)
            
            # Use `summarize_dual`
            summary_json = await asyncio.to_thread(memory_service.summarize_dual, full_text)
            
            if summary_json:
                # Save with new structure
                await asyncio.to_thread(cosmos_service.save_memory, user_id, full_text, summary_json)
                print(f"[Memory] Dual Session saved for {user_id}")
            else:
                print("[Memory] Skipped saving: Summary is empty or invalid.")

# --- Static Files (Frontend) ---
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_front", "out")

if os.path.exists(FRONTEND_BUILD_DIR):
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
