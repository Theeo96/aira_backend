"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Camera, CameraOff, Mic, MicOff, Monitor, MonitorOff } from "lucide-react";

type TranscriptMessage = {
  role: "user" | "ai" | "lumi" | "rami";
  text: string;
};

export default function Home() {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [isScreenOn, setIsScreenOn] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [status, setStatus] = useState("Disconnected");
  const [transcripts, setTranscripts] = useState<TranscriptMessage[]>([]);

  // Auth State
  const [userToken, setUserToken] = useState<string | null>(null);
  const [loginInput, setLoginInput] = useState("");

  // Multimodal Input State
  const [textInput, setTextInput] = useState("");
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const websocketRef = useRef<WebSocket | null>(null);
  const locationTimerRef = useRef<number | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const nextStartTimeRef = useRef<number>(0);
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const cameraVideoRef = useRef<HTMLVideoElement | null>(null);
  const cameraCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const cameraStreamRef = useRef<MediaStream | null>(null);
  const screenStreamRef = useRef<MediaStream | null>(null);
  const aiSpeakingRef = useRef<boolean>(false);
  const aiSpeakingTimerRef = useRef<number | null>(null);
  const visionHeartbeatTimerRef = useRef<number | null>(null);

  // Initialize Audio Context & Cleanup
  useEffect(() => {
    // Check localStorage for token
    const savedToken = localStorage.getItem("google_user_token");
    if (savedToken) setUserToken(savedToken);

    return () => {
      clearLocationTimer();
      stopCameraProcessing();
      stopScreenProcessing();
      if (visionHeartbeatTimerRef.current) {
        window.clearInterval(visionHeartbeatTimerRef.current);
        visionHeartbeatTimerRef.current = null;
      }
      if (aiSpeakingTimerRef.current) {
        window.clearTimeout(aiSpeakingTimerRef.current);
        aiSpeakingTimerRef.current = null;
      }
      if (websocketRef.current) websocketRef.current.close();
      stopAudioProcessing();
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcripts]);

  // Auto-Login Check (URL Query Param)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const tokenFromUrl = params.get("token");
      if (tokenFromUrl) {
        setUserToken(tokenFromUrl);
        localStorage.setItem("google_user_token", tokenFromUrl);
        const newUrl = window.location.protocol + "//" + window.location.host + window.location.pathname;
        window.history.replaceState({ path: newUrl }, "", newUrl);
      }
    }
  }, []);

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
    stopCameraProcessing();
    stopScreenProcessing();
    setUserToken(null);
    localStorage.removeItem("google_user_token");
    if (websocketRef.current) websocketRef.current.close();
    setIsConnected(false);
    setTranscripts([]);
  };

  const openGoogleLogin = () => {
    const target = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
    const loginUrl = `https://8ai-th-loginback-atcyfgfcgbfxcvhx.koreacentral-01.azurewebsites.net/login?redirect_target=${encodeURIComponent(target)}`;
    window.location.href = loginUrl;
  };

  const markAiSpeaking = () => {
    aiSpeakingRef.current = true;
    if (aiSpeakingTimerRef.current) {
      window.clearTimeout(aiSpeakingTimerRef.current);
      aiSpeakingTimerRef.current = null;
    }
    aiSpeakingTimerRef.current = window.setTimeout(() => {
      aiSpeakingRef.current = false;
      aiSpeakingTimerRef.current = null;
    }, 900);
  };

  const resampleTo16k = (input: Float32Array, inputRate: number): Float32Array => {
    const targetRate = 16000;
    if (!input || input.length === 0) return new Float32Array(0);
    if (!inputRate || inputRate <= 0 || inputRate === targetRate) return input;
    const ratio = inputRate / targetRate;
    const outputLength = Math.max(1, Math.floor(input.length / ratio));
    const output = new Float32Array(outputLength);
    for (let i = 0; i < outputLength; i++) {
      const srcIndex = i * ratio;
      const idx = Math.floor(srcIndex);
      const next = Math.min(idx + 1, input.length - 1);
      const frac = srcIndex - idx;
      output[i] = input[idx] * (1 - frac) + input[next] * frac;
    }
    return output;
  };

  const clearLocationTimer = () => {
    if (locationTimerRef.current) {
      window.clearInterval(locationTimerRef.current);
      locationTimerRef.current = null;
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      setSelectedImage(event.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleSendMultimodal = () => {
    if (!textInput.trim() && !selectedImage) return;
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.send(
        JSON.stringify({
          type: "multimodal_input",
          text: textInput,
          image_b64: selectedImage,
        })
      );
      // We don't locally push text to transcript here because server will echo it back, 
      // but if we want instant feedback we can. Let's let server echo it.
      setTextInput("");
      setSelectedImage(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } else {
      alert("Aira에 먼저 연결해주세요 (Connect 버튼 클릭).");
    }
  };

  const sendLocationUpdate = useCallback(async (ws?: WebSocket | null) => {
    const socket = ws || websocketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        if (!navigator.geolocation) {
          reject(new Error("Geolocation not supported"));
          return;
        }
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 10000,
        });
      });
      socket.send(
        JSON.stringify({
          type: "location_update",
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        })
      );
    } catch (e) {
      console.warn("Location update failed:", e);
    }
  }, []);

  const connectWebSocket = useCallback(async () => {
    if (!userToken) return;
    if (isConnecting) return;
    setIsConnecting(true);
    setStatus("Connecting...");
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    let latParam = "";
    let lngParam = "";
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        if (!navigator.geolocation) {
          reject(new Error("Geolocation not supported"));
          return;
        }
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 30000,
        });
      });
      latParam = `&lat=${encodeURIComponent(position.coords.latitude)}`;
      lngParam = `&lng=${encodeURIComponent(position.coords.longitude)}`;
    } catch (e) {
      console.warn("Geolocation unavailable:", e);
      setStatus("Location permission required. Use localhost and allow location.");
      setIsConnecting(false);
      return;
    }

    const wsUrl = `${protocol}//${host}/ws/audio?user_id=${encodeURIComponent(userToken)}${latParam}${lngParam}`;

    const ws = new WebSocket(wsUrl);
    websocketRef.current = ws;

    ws.onopen = () => {
      if (websocketRef.current !== ws) return;
      setIsConnected(true);
      setIsConnecting(false);
      setStatus("Connected to Aira");
      console.log("WebSocket Connected");
      sendLocationUpdate(ws);
      clearLocationTimer();
      locationTimerRef.current = window.setInterval(() => {
        sendLocationUpdate(ws);
      }, 60000);
    };

    ws.onclose = () => {
      if (websocketRef.current !== ws) return;
      websocketRef.current = null;
      clearLocationTimer();
      stopCameraProcessing();
      stopScreenProcessing();
      stopAudioProcessing();
      setIsConnected(false);
      setIsConnecting(false);
      setStatus("Disconnected");
    };

    ws.onerror = () => {
      if (websocketRef.current !== ws) return;
      websocketRef.current = null;
      clearLocationTimer();
      stopCameraProcessing();
      stopScreenProcessing();
      stopAudioProcessing();
      setIsConnected(false);
      setIsConnecting(false);
      setStatus("WebSocket Error");
    };

    ws.onmessage = async (event) => {
      if (websocketRef.current !== ws) return;
      if (event.data instanceof Blob) {
        // Audio Data
        const arrayBuffer = await event.data.arrayBuffer();
        markAiSpeaking();
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
  }, [userToken, isConnecting, sendLocationUpdate]);

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
  const micStreamRef = useRef<MediaStream | null>(null);

  const stopCameraProcessing = () => {
    if (visionHeartbeatTimerRef.current) {
      window.clearInterval(visionHeartbeatTimerRef.current);
      visionHeartbeatTimerRef.current = null;
    }
    if (cameraStreamRef.current) {
      cameraStreamRef.current.getTracks().forEach((t) => t.stop());
      cameraStreamRef.current = null;
    }
    if (cameraVideoRef.current) {
      cameraVideoRef.current.srcObject = null;
    }
    setIsCameraOn(false);
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({ type: "camera_state", enabled: false }));
    }
  };

  const stopScreenProcessing = () => {
    if (visionHeartbeatTimerRef.current) {
      window.clearInterval(visionHeartbeatTimerRef.current);
      visionHeartbeatTimerRef.current = null;
    }
    if (screenStreamRef.current) {
      screenStreamRef.current.getTracks().forEach((t) => t.stop());
      screenStreamRef.current = null;
    }
    setIsScreenOn(false);
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({ type: "camera_state", enabled: false }));
    }
  };

  const sendVisionSnapshot = async () => {
    const ws = websocketRef.current;
    const v = cameraVideoRef.current;
    const c = cameraCanvasRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN || !v || !c) return;
    const ctx = c.getContext("2d");
    if (!ctx) return;

    // For browser screen-share, use track frame capture first to avoid stale first-frame issues.
    let captured = false;
    if (isScreenOn && screenStreamRef.current) {
      try {
        const [track] = screenStreamRef.current.getVideoTracks();
        if (track && "ImageCapture" in window) {
          const imageCapture = new (window as any).ImageCapture(track);
          const bitmap = await imageCapture.grabFrame();
          c.width = 640;
          c.height = Math.max(360, Math.floor((640 * bitmap.height) / bitmap.width));
          ctx.drawImage(bitmap, 0, 0, c.width, c.height);
          captured = true;
        }
      } catch (e) {
        console.warn("ImageCapture failed, fallback to video frame:", e);
      }
    }

    if (!captured) {
      if (v.videoWidth === 0 || v.videoHeight === 0) return;
      c.width = 640;
      c.height = Math.max(360, Math.floor((640 * v.videoHeight) / v.videoWidth));
      ctx.drawImage(v, 0, 0, c.width, c.height);
    }

    const dataUrl = c.toDataURL("image/jpeg", 0.55);
    const b64 = dataUrl.split(",")[1] || "";
    if (!b64) return;
    ws.send(
      JSON.stringify({
        type: "camera_snapshot_base64",
        mime_type: "image/jpeg",
        data: b64,
      })
    );
    return true;
  };

  const sendVisionSnapshotWithRetry = async (attempt = 0) => {
    const ok = await sendVisionSnapshot();
    if (ok) return;
    if (attempt >= 20) return;
    window.setTimeout(() => {
      void sendVisionSnapshotWithRetry(attempt + 1);
    }, 250);
  };

  const startVisionHeartbeat = () => {
    if (visionHeartbeatTimerRef.current) {
      window.clearInterval(visionHeartbeatTimerRef.current);
      visionHeartbeatTimerRef.current = null;
    }
    visionHeartbeatTimerRef.current = window.setInterval(() => {
      void sendVisionSnapshotWithRetry();
    }, 1200);
  };

  const startCameraProcessing = async () => {
    if (!websocketRef.current || websocketRef.current.readyState !== WebSocket.OPEN) {
      setStatus("Connect first");
      return;
    }
    if (isCameraOn) return;
    try {
      if (isScreenOn) stopScreenProcessing();
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment",
          width: { ideal: 960 },
          height: { ideal: 540 },
        },
        audio: false,
      });
      cameraStreamRef.current = stream;
      const video = cameraVideoRef.current;
      if (video) {
        video.srcObject = stream;
        await video.play();
      }

      websocketRef.current.send(JSON.stringify({ type: "camera_state", enabled: true }));
      setIsCameraOn(true);
      setIsScreenOn(false);
      void sendVisionSnapshotWithRetry();
      startVisionHeartbeat();
    } catch (e) {
      console.error(e);
      setStatus("Camera Error");
      stopCameraProcessing();
    }
  };

  const startScreenProcessing = async () => {
    if (!websocketRef.current || websocketRef.current.readyState !== WebSocket.OPEN) {
      setStatus("Connect first");
      return;
    }
    if (isScreenOn) return;
    try {
      if (isCameraOn) stopCameraProcessing();
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: { frameRate: 8 },
        audio: false,
      });
      screenStreamRef.current = stream;
      const video = cameraVideoRef.current;
      if (video) {
        video.srcObject = stream;
        await video.play();
      }

      websocketRef.current.send(JSON.stringify({ type: "camera_state", enabled: true }));
      setIsScreenOn(true);
      setIsCameraOn(false);
      void sendVisionSnapshotWithRetry();
      startVisionHeartbeat();

      const [track] = stream.getVideoTracks();
      if (track) {
        track.onended = () => {
          stopScreenProcessing();
        };
      }
    } catch (e) {
      console.error(e);
      setStatus("Screen Share Error");
      stopScreenProcessing();
    }
  };

  const startAudioProcessing = async () => {
    if (!websocketRef.current || websocketRef.current.readyState !== WebSocket.OPEN) {
      setStatus("Connect first");
      return;
    }
    if (isRecording) return;
    try {
      // Defensive cleanup for restart stability (Stop -> Start race cases).
      processorRef.current?.disconnect();
      if (processorRef.current) processorRef.current.onaudioprocess = null as any;
      processorRef.current = null;
      sourceRef.current?.disconnect();
      sourceRef.current = null;
      if (micStreamRef.current) {
        micStreamRef.current.getTracks().forEach((t) => t.stop());
        micStreamRef.current = null;
      }
      if (inputContextRef.current) {
        try {
          await inputContextRef.current.close();
        } catch { }
        inputContextRef.current = null;
      }

      await sendLocationUpdate(websocketRef.current);
      if (!aiSpeakingRef.current) {
        void sendVisionSnapshotWithRetry();
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true }
      });
      micStreamRef.current = stream;
      inputContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      const ctx = inputContextRef.current;
      if (ctx.state === "suspended") {
        await ctx.resume();
      }
      sourceRef.current = ctx.createMediaStreamSource(stream);
      processorRef.current = ctx.createScriptProcessor(2048, 1, 1);

      processorRef.current.onaudioprocess = (e) => {
        if (!websocketRef.current || websocketRef.current.readyState !== WebSocket.OPEN) return;
        const inputData = e.inputBuffer.getChannelData(0);
        const resampled = resampleTo16k(inputData, ctx.sampleRate);
        const pcmData = new Int16Array(resampled.length);
        for (let i = 0; i < resampled.length; i++) {
          const s = Math.max(-1, Math.min(1, resampled[i]));
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        try {
          websocketRef.current.send(pcmData.buffer);
        } catch (err) {
          console.warn("Audio send failed:", err);
        }
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
    if (processorRef.current) processorRef.current.onaudioprocess = null as any;
    processorRef.current?.disconnect();
    processorRef.current = null;
    sourceRef.current?.disconnect();
    sourceRef.current = null;
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((t) => t.stop());
      micStreamRef.current = null;
    }
    inputContextRef.current?.close();
    inputContextRef.current = null;
    setIsRecording(false);
    if (isConnected) setStatus("Idle");
  };

  const toggleCamera = () => {
    if (isCameraOn) {
      stopCameraProcessing();
      return;
    }
    startCameraProcessing();
  };

  const toggleScreenShare = () => {
    if (isScreenOn) {
      stopScreenProcessing();
      return;
    }
    startScreenProcessing();
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
      {/* Header & Status */}
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm flex flex-col gap-4">
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

      {/* Mic + Camera */}
      <div className="flex-1 flex flex-col items-center justify-center gap-8 w-full max-w-6xl">
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
            <button
              onClick={connectWebSocket}
              disabled={isConnecting}
              className={`w-full py-3 rounded-lg transition font-bold ${isConnecting ? "bg-gray-600 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"}`}
            >
              {isConnecting ? "Connecting..." : "Connect"}
            </button>
          ) : (
            <button onClick={isRecording ? stopAudioProcessing : startAudioProcessing}
              className={`w-full py-4 rounded-lg text-lg font-bold transition ${isRecording ? "bg-red-600 hover:bg-red-700" : "bg-green-600 hover:bg-green-700"}`}>
              {isRecording ? "Stop Speaking" : "Start Speaking"}
            </button>
          )}
        </div>
        <div className="w-full">
          <button
            onClick={toggleCamera}
            disabled={!isConnected}
            className={`w-full py-3 rounded-lg text-base font-bold transition ${!isConnected
              ? "bg-gray-700 cursor-not-allowed"
              : isCameraOn
                ? "bg-yellow-600 hover:bg-yellow-700"
                : "bg-indigo-600 hover:bg-indigo-700"
              }`}
          >
            <span className="inline-flex items-center gap-2 justify-center">
              {isCameraOn ? <CameraOff size={18} /> : <Camera size={18} />}
              {isCameraOn ? "Turn Camera Off" : "Turn Camera On"}
            </span>
          </button>
        </div>
        <div className="w-full">
          <button
            onClick={toggleScreenShare}
            disabled={!isConnected}
            className={`w-full py-3 rounded-lg text-base font-bold transition ${!isConnected
              ? "bg-gray-700 cursor-not-allowed"
              : isScreenOn
                ? "bg-rose-600 hover:bg-rose-700"
                : "bg-cyan-600 hover:bg-cyan-700"
              }`}
          >
            <span className="inline-flex items-center gap-2 justify-center">
              {isScreenOn ? <MonitorOff size={18} /> : <Monitor size={18} />}
              {isScreenOn ? "Stop Screen Share" : "Start Screen Share"}
            </span>
          </button>
        </div>
        <div className="w-full bg-gray-900/80 border border-gray-700 rounded-lg p-3">
          <div className="mb-2 text-xs text-gray-400">
            Camera: {isCameraOn ? "ON (continuous stream)" : "OFF"} | Screen: {isScreenOn ? "ON (continuous stream)" : "OFF"}
          </div>
          <video
            ref={cameraVideoRef}
            autoPlay
            playsInline
            muted
            className="w-full rounded-md bg-black aspect-video min-h-[320px] md:min-h-[420px] max-h-[70vh] object-cover"
          />
          <canvas ref={cameraCanvasRef} className="hidden" />
        </div>
      </div>

      {/* Chat Transcript Area */}
      <div className="w-full max-w-5xl mt-8 h-80 bg-gray-900 border border-gray-800 rounded-xl p-4 overflow-y-auto flex flex-col gap-3 shadow-inner">
        {transcripts.length === 0 && <p className="text-gray-600 text-center text-sm py-10">대화 내용이 여기에 표시됩니다...</p>}
        {transcripts.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm border ${msg.role === "user"
              ? "bg-blue-600 text-white border-blue-600 rounded-br-none"
              : msg.role === "lumi"
                ? "bg-blue-100 text-blue-900 border-blue-200 rounded-bl-none shadow-sm"
                : msg.role === "rami"
                  ? "bg-orange-100 text-orange-900 border-orange-200 rounded-bl-none shadow-sm"
                  : "bg-gray-700 text-gray-200 border-gray-600 rounded-bl-none"
              }`}>
              <p className="font-bold text-[10px] opacity-70 mb-1 uppercase">{msg.role}</p>
              {msg.text}
            </div>
          </div>
        ))}
        <div ref={chatBottomRef} />
      </div>

      {/* Multimodal Input Area */}
      <div className="w-full max-w-5xl mt-4 bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col gap-3">
        {selectedImage && (
          <div className="relative w-fit">
            <img src={selectedImage} alt="preview" className="h-24 rounded-md object-cover border border-gray-700" />
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute -top-2 -right-2 bg-red-600 rounded-full w-6 h-6 flex items-center justify-center text-xs text-white"
            >
              x
            </button>
          </div>
        )}
        <div className="flex gap-2">
          <input
            type="file"
            accept="image/*"
            className="hidden"
            ref={fileInputRef}
            onChange={handleImageSelect}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition font-bold"
          >
            📷 사진 첨부
          </button>
          <input
            type="text"
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
            placeholder="텍스트 메시지 입력..."
            value={textInput}
            onChange={e => setTextInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') handleSendMultimodal();
            }}
          />
          <button
            onClick={handleSendMultimodal}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-bold transition"
          >
            전송
          </button>
        </div>
      </div>
    </main>
  );
}