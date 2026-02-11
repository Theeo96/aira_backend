import asyncio
import os
import sys
import queue
import threading
import time
import struct
import gradio as gr
import numpy as np
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")

# Model
MODEL_NAME_ACTOR = "gemini-2.5-flash-native-audio-preview-12-2025"

# Global Queues
# input_q: (sample_rate, pcm_bytes)
input_q = queue.Queue()
output_q = queue.Queue()
shutdown_event = threading.Event()

# --- Gemini Background Worker ---
async def gemini_worker():
    print("[Gemini] Worker started.")
    client = genai.Client(api_key=API_KEY)
    config = {
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "voice_config": {"prebuilt_voice_config": {"voice_name": "Aoede"}}
        },
    }

    while not shutdown_event.is_set():
        try:
            async with client.aio.live.connect(model=MODEL_NAME_ACTOR, config=config) as session:
                print("[Gemini] Connection established!")
                
                async def send_loop():
                    while True:
                        try:
                            # Non-blocking check for shutdown
                            if shutdown_event.is_set(): break
                            
                            try:
                                # Get audio from user (input_q)
                                sr, audio_bytes = await asyncio.to_thread(input_q.get, timeout=0.1)
                                
                                # Send to Gemini directly
                                mime = f"audio/pcm;rate={sr}"
                                await session.send_realtime_input(audio={"data": audio_bytes, "mime_type": mime})
                                
                            except queue.Empty:
                                continue
                            except Exception as e:
                                print(f"[Send Error] {e}")
                                break
                        except Exception:
                            break

                async def receive_loop():
                    while True:
                        try:
                            async for response in session.receive():
                                if response.server_content and response.server_content.model_turn:
                                    for part in response.server_content.model_turn.parts:
                                        if part.inline_data:
                                            # Put response chunk into output_q
                                            # Gemini output is usually 24kHz PCM
                                            output_q.put(part.inline_data.data)
                        except Exception as e:
                            print(f"[Receive Error] {e}")
                            break
                        
                        if shutdown_event.is_set(): break
                
                await asyncio.gather(send_loop(), receive_loop())
                
        except Exception as e:
            if not shutdown_event.is_set():
                print(f"[Gemini] Connection dropped: {e}")
            await asyncio.sleep(2)

def start_gemini_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(gemini_worker())

threading.Thread(target=start_gemini_thread, daemon=True).start()

# --- Gradio Transceiver ---
def transceive(audio_chunk):
    """
    Receives (sr, data) from Gradio.
    Yields (sr, data) to Gradio.
    """
    if audio_chunk is None:
        return None

    sr, data = audio_chunk
    
    # 1. Process Input (User -> Gemini)
    # Convert numpy to bytes
    # Data is typically int16 or float32.
    if data.dtype == np.float32:
        # Convert float32 to int16
        data = (data * 32767).astype(np.int16)
    
    # Store in input_q
    if data.size > 0:
        # Mono conversion if stereo
        if len(data.shape) > 1 and data.shape[1] > 1:
            data = data[:, 0] # Take left channel
            
        input_q.put((sr, data.tobytes()))

    # 2. Process Output (Gemini -> User)
    # Check if we have audio to play back
    out_audio = b""
    try:
        # Fetch all available chunks to reduce latency
        while True:
            chunk = output_q.get_nowait()
            out_audio += chunk
    except queue.Empty:
        pass

    if out_audio:
        # Convert bytes back to numpy for Gradio
        # Gemini sends 24kHz usually.
        # Gradio output expects (sample_rate, numpy_array)
        out_sr = 24000
        out_data = np.frombuffer(out_audio, dtype=np.int16)
        return (out_sr, out_data)
    
    return None

# --- Gradio UI ---
def run_gradio():
    with gr.Blocks(title="Aira Real-time") as demo:
        gr.Markdown("## Aira (Gemini Live) - Real-time Streaming")
        
        with gr.Row():
            # Streaming Input
            mic = gr.Audio(sources=["microphone"], type="numpy", streaming=True, label="Mic Input")
            # Streaming Output
            spk = gr.Audio(label="Aira Output", streaming=True, autoplay=True)
            
        # Wire stream
        # mic.stream sends data to transceive, result goes to spk
        mic.stream(fn=transceive, inputs=[mic], outputs=[spk], stream_every=0.1)

    print("Launching Gradio Streaming...")
    demo.launch(share=True)

if __name__ == "__main__":
    run_gradio()
