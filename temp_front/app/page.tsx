"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Mic, MicOff } from "lucide-react";

type TranscriptMessage = {
  role: "user" | "ai";
  text: string;
};

export default function Home() {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState("Disconnected");
  const [transcripts, setTranscripts] = useState<TranscriptMessage[]>([]);

  // Auth State
  const [userToken, setUserToken] = useState<string | null>(null);
  const [loginInput, setLoginInput] = useState("");

  const websocketRef = useRef<WebSocket | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const nextStartTimeRef = useRef<number>(0);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Initialize Audio Context & Cleanup
  useEffect(() => {
    // Check localStorage for token
    const savedToken = localStorage.getItem("google_user_token");
    if (savedToken) setUserToken(savedToken);

    return () => {
      if (websocketRef.current) websocketRef.current.close();
      stopAudioProcessing();
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcripts]);

  const handleLogin = () => {
    const token = loginInput.trim();
    if (token.includes("@") && token.includes(".")) {
      setUserToken(token);
      localStorage.setItem("google_user_token", token);
    } else {
      alert("Please enter a valid email address/token.");
    }
  };

  const handleLogout = () => {
    setUserToken(null);
    localStorage.removeItem("google_user_token");
    if (websocketRef.current) websocketRef.current.close();
    setIsConnected(false);
    setTranscripts([]);
  };

  const openGoogleLogin = () => {
    window.open("https://8ai-th-loginback-atcyfgfcgbfxcvhx.koreacentral-01.azurewebsites.net/login", "_blank");
  };

  const connectWebSocket = useCallback(() => {
    if (!userToken) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    // Pass user_id query param
    const wsUrl = `${protocol}//${host}/ws/audio?user_id=${encodeURIComponent(userToken)}`;

    const ws = new WebSocket(wsUrl);
    websocketRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setStatus("Connected to Aira");
      console.log("WebSocket Connected");
    };

    ws.onclose = () => {
      setIsConnected(false);
      setStatus("Disconnected");
    };

    ws.onmessage = async (event) => {
      if (event.data instanceof Blob) {
        // Audio Data
        const arrayBuffer = await event.data.arrayBuffer();
        playAudioChunk(arrayBuffer);
      } else {
        // Text Data (JSON Transcript)
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "transcript") {
            setTranscripts(prev => [...prev, { role: msg.role, text: msg.text }]);
          }
        } catch (e) {
          console.error("Msg Parse Error", e);
        }
      }
    };
  }, [userToken]);

  const playAudioChunk = useCallback((arrayBuffer: ArrayBuffer) => {
    if (!playbackContextRef.current) {
      playbackContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
      nextStartTimeRef.current = playbackContextRef.current.currentTime;
    }
    const ctx = playbackContextRef.current;

    const dataView = new DataView(arrayBuffer);
    const float32Data = new Float32Array(arrayBuffer.byteLength / 2);
    for (let i = 0; i < float32Data.length; i++) {
      const pcm = dataView.getInt16(i * 2, true);
      float32Data[i] = pcm / 32768.0;
    }

    const buffer = ctx.createBuffer(1, float32Data.length, 24000);
    buffer.getChannelData(0).set(float32Data);

    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);

    const scheduleTime = Math.max(ctx.currentTime + 0.05, nextStartTimeRef.current);
    source.start(scheduleTime);
    nextStartTimeRef.current = scheduleTime + buffer.duration;
  }, []);

  // --- Recording Logic ---
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const inputContextRef = useRef<AudioContext | null>(null);

  const startAudioProcessing = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true }
      });
      inputContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      const ctx = inputContextRef.current;
      sourceRef.current = ctx.createMediaStreamSource(stream);
      processorRef.current = ctx.createScriptProcessor(4096, 1, 1);

      processorRef.current.onaudioprocess = (e) => {
        if (!websocketRef.current || websocketRef.current.readyState !== WebSocket.OPEN) return;
        const inputData = e.inputBuffer.getChannelData(0);
        const pcmData = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        websocketRef.current.send(pcmData.buffer);
      };

      sourceRef.current.connect(processorRef.current);
      processorRef.current.connect(ctx.destination);
      setIsRecording(true);
      setStatus("Listening...");
    } catch (err) {
      console.error(err);
      setStatus("Microphone Error");
    }
  };

  const stopAudioProcessing = () => {
    processorRef.current?.disconnect();
    sourceRef.current?.disconnect();
    inputContextRef.current?.close();
    setIsRecording(false);
    setStatus("Idle");
  };

  if (!userToken) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-black text-white gap-6">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mb-8">
          Aira Login
        </h1>

        <div className="flex flex-col gap-4 w-full max-w-md bg-gray-900 p-8 rounded-2xl border border-gray-800">
          <button
            onClick={openGoogleLogin}
            className="w-full py-3 rounded-lg bg-white text-black font-bold hover:bg-gray-200 transition flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" /><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" /><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" /><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" /></svg>
            Google Login
          </button>

          <div className="text-center text-gray-500 text-sm my-2">-- OR --</div>

          <input
            type="email"
            placeholder="Paste your Token (Email) here"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-blue-500"
            value={loginInput}
            onChange={(e) => setLoginInput(e.target.value)}
          />

          <button
            onClick={handleLogin}
            className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-700 transition font-bold text-white"
          >
            Enter Aira
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-8 bg-black text-white">
      {/* Header & Status - Wider (max-w-4xl) */}
      <div className="z-10 w-full max-w-4xl items-center justify-between font-mono text-sm flex flex-col gap-4">
        <div className="w-full flex justify-between items-center">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Aira Real-time
          </h1>
          <button onClick={handleLogout} className="text-xs text-gray-500 hover:text-white underline">
            Logout ({userToken})
          </button>
        </div>

        <div className={`text-sm ${isConnected ? "text-green-400" : "text-red-400"}`}>
          {status}
        </div>
      </div>

      {/* Mic Control - Wider (max-w-4xl) */}
      <div className="flex-1 flex flex-col items-center justify-center gap-8 w-full max-w-4xl">
        <div className={`relative w-48 h-48 rounded-full flex items-center justify-center transition-all duration-300 ${isRecording ? "bg-red-900/20 shadow-[0_0_50px_rgba(220,38,38,0.5)]" : "bg-gray-800"}`}>
          {isRecording && (
            <div className="absolute inset-0 rounded-full border-4 border-red-500 opacity-20 animate-ping"></div>
          )}
          <div className={`text-6xl ${isRecording ? "text-red-500" : isConnected ? "text-blue-400" : "text-gray-500"}`}>
            {isRecording ? <Mic /> : <MicOff />}
          </div>
        </div>

        <div className="w-full">
          {!isConnected ? (
            <button onClick={connectWebSocket} className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-700 transition font-bold">
              Connect
            </button>
          ) : (
            <button onClick={isRecording ? stopAudioProcessing : startAudioProcessing}
              className={`w-full py-4 rounded-lg text-lg font-bold transition ${isRecording ? "bg-red-600 hover:bg-red-700" : "bg-green-600 hover:bg-green-700"}`}>
              {isRecording ? "Stop Speaking" : "Start Speaking"}
            </button>
          )}
        </div>
      </div>

      {/* Chat Transcript Area - Wider (max-w-4xl) & Taller (h-80) */}
      <div className="w-full max-w-4xl mt-8 h-80 bg-gray-900 border border-gray-800 rounded-xl p-4 overflow-y-auto flex flex-col gap-3 shadow-inner">
        {transcripts.length === 0 && <p className="text-gray-600 text-center text-sm py-10">대화 내용이 여기에 표시됩니다...</p>}
        {transcripts.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${msg.role === "user"
              ? "bg-blue-600 text-white rounded-br-none"
              : "bg-gray-700 text-gray-200 rounded-bl-none"
              }`}>
              <p className="font-bold text-[10px] opacity-50 mb-1 uppercase">{msg.role}</p>
              {msg.text}
            </div>
          </div>
        ))}
        <div ref={chatBottomRef} />
      </div>
    </main>
  );
}
