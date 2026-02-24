import os
# Load env variables first
from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import numpy as np
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
import uuid
import datetime
from google import genai
import sys
from modules.cosmos_db import cosmos_service
from modules.memory import memory_service
from modules.seoul_info_module import build_seoul_info_packet, build_speech_summary
from modules.news_agent import NewsAgent
from modules.intent_router import IntentRouter
from modules.seoul_live_service import SeoulLiveService
from modules.vision_service import VisionService
from modules.news_context_service import NewsContextService
from modules.timer_service import TimerService
from modules.proactive_service import ProactiveService
from modules.ws_orchestrator_service import WsOrchestratorService
from modules.morning_briefing_module import MorningBriefingModule
from modules.tmap_service import TmapService
from modules.live_seoul_summary_service import LiveSeoulSummaryService
from modules.context_runtime_service import ContextRuntimeService
from modules.audio_stt_utils import create_push_stream
from modules.audio_stt_utils import create_recognizer as create_azure_recognizer
from modules.http_api_routes import create_api_router
from modules.briefing_runtime_service import BriefingRuntimeService
from modules import conversation_text_utils
from modules import runtime_env as runtime_env_utils
from modules import route_text_utils
from modules.fast_intent_router import fast_route_intent as fast_route_intent_core
from modules.transit_runtime_service import TransitRuntimeService
from modules.lumirami import LumiRamiManager

from contextlib import asynccontextmanager

# --- OAuth Setup ---
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')

oauth = OAuth()
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/gmail.readonly',
            'prompt': 'consent'
        }
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("[Server] Starting up... (Lifespan Event)")
    yield
    # Shutdown logic
    print("[Server] Shutting down... (Lifespan Event)")

app = FastAPI(lifespan=lifespan)

# Custom Session Middleware to bypass WebSockets
class WebSocketFriendlySessionMiddleware:
    def __init__(self, app, secret_key: str):
        self.app = app
        self.session_middleware = SessionMiddleware(app, secret_key=secret_key)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            # Bypass SessionMiddleware for websockets completely
            await self.app(scope, receive, send)
            return
        await self.session_middleware(scope, receive, send)

app.add_middleware(WebSocketFriendlySessionMiddleware, secret_key=SECRET_KEY)


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*", 
        "http://localhost:5173", 
        "https://icy-ground-0066bb800.6.azurestaticapps.net"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-native-audio-preview-12-2025"
GEMINI_DIRECT_AUDIO_INPUT = os.getenv("GEMINI_DIRECT_AUDIO_INPUT", "true").strip().lower() in {"1", "true", "yes", "on"}
ORCHESTRATION_SINGLE_PATH = os.getenv("ORCHESTRATION_SINGLE_PATH", "true").strip().lower() in {"1", "true", "yes", "on"}
EFFECTIVE_GEMINI_DIRECT_AUDIO_INPUT = GEMINI_DIRECT_AUDIO_INPUT and (not ORCHESTRATION_SINGLE_PATH)
CAMERA_FRAME_MIN_INTERVAL_SEC = float(os.getenv("CAMERA_FRAME_MIN_INTERVAL_SEC", "1.0"))
VISION_SNAPSHOT_TTL_SEC = float(os.getenv("VISION_SNAPSHOT_TTL_SEC", "120"))
ENV_CACHE_TTL_SEC = float(os.getenv("ENV_CACHE_TTL_SEC", "300"))

# Azure Speech Config
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
SEOUL_API_KEY = os.getenv("SEOUL_API_KEY")
ODSAY_API_KEY = os.getenv("ODSAY_API_KEY")
TMAP_APP_KEY = os.getenv("TMAP_APP_KEY")
HOME_LAT = os.getenv("HOME_LAT")
HOME_LNG = os.getenv("HOME_LNG")
COMMUTE_DEFAULT_DESTINATION = os.getenv("COMMUTE_DEFAULT_DESTINATION", "광화문")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
INTENT_ROUTER_MODEL = os.getenv("INTENT_ROUTER_MODEL") or AZURE_OPENAI_DEPLOYMENT_NAME or "gpt-4o-mini"
ENABLE_TRANSIT_FILLER = os.getenv("ENABLE_TRANSIT_FILLER", "false").strip().lower() in {"1", "true", "yes", "on"}
STT_SEGMENTATION_SILENCE_TIMEOUT_MS = os.getenv("STT_SEGMENTATION_SILENCE_TIMEOUT_MS", "800")
AI_STT_SEGMENTATION_SILENCE_TIMEOUT_MS = os.getenv("AI_STT_SEGMENTATION_SILENCE_TIMEOUT_MS", "900")
AI_FLUSH_SILENCE_AFTER_SEC = float(os.getenv("AI_FLUSH_SILENCE_AFTER_SEC", "1.2"))
AI_FLUSH_SILENCE_SEC = float(os.getenv("AI_FLUSH_SILENCE_SEC", "0.15"))
AI_FLUSH_MIN_INTERVAL_SEC = float(os.getenv("AI_FLUSH_MIN_INTERVAL_SEC", "1.5"))
print(f"[Config] ENABLE_TRANSIT_FILLER={ENABLE_TRANSIT_FILLER}")
print(f"[Config] GEMINI_DIRECT_AUDIO_INPUT={GEMINI_DIRECT_AUDIO_INPUT}")
print(f"[Config] ORCHESTRATION_SINGLE_PATH={ORCHESTRATION_SINGLE_PATH}")
print(f"[Config] EFFECTIVE_GEMINI_DIRECT_AUDIO_INPUT={EFFECTIVE_GEMINI_DIRECT_AUDIO_INPUT}")

RUNTIME_ENV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".env",
)

BRIEFING_PRE_AD_COPY = (
    "오늘의 브리핑을 시작하기 전, Aira가 전하는 꿀정보! "
    "효과음: 키보드 엔터, 탁! "
    "복잡한 B2B 솔루션 도입, 아직도 헤매시나요? "
    "마이크로소프트 애저 마켓플레이스에선 클릭 한 번에 배포 끝! "
    "남은 클라우드 예산으로 결제 혜택까지 알뜰하게 챙기세요. "
    "비즈니스의 정답, 애저!"
)

try:
    NEWS_AGENT = NewsAgent()
except Exception as e:
    NEWS_AGENT = None
    print(f"[News] NewsAgent init failed: {e}")

try:
    MORNING_BRIEFING = MorningBriefingModule(news_agent=NEWS_AGENT, log=print)
except Exception as e:
    MORNING_BRIEFING = None
    print(f"[MorningBriefing] init failed: {e}")

TMAP_SERVICE = TmapService(TMAP_APP_KEY, log=print)
TRANSIT_RUNTIME = TransitRuntimeService(
    odsay_api_key=ODSAY_API_KEY,
    seoul_api_key=SEOUL_API_KEY,
    tmap_app_key=TMAP_APP_KEY,
    tmap_service=TMAP_SERVICE,
    log=print,
)
CONTEXT_RUNTIME = ContextRuntimeService(
    odsay_api_key=ODSAY_API_KEY,
    tmap_service=TMAP_SERVICE,
    env_cache_ttl_sec=ENV_CACHE_TTL_SEC,
    haversine_meters=TRANSIT_RUNTIME.haversine_meters,
    home_lat=HOME_LAT,
    home_lng=HOME_LNG,
    log=print,
)

news_context_service = NewsContextService(news_agent=NEWS_AGENT, log=print)
ws_orchestrator = WsOrchestratorService()

_to_float = CONTEXT_RUNTIME.to_float
_resolve_home_coords = CONTEXT_RUNTIME.resolve_home_coords
_extract_destination_from_text = route_text_utils.extract_destination_from_text


intent_router = IntentRouter(
    api_key=AZURE_OPENAI_API_KEY,
    endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION,
    model=INTENT_ROUTER_MODEL,
    destination_extractor=_extract_destination_from_text,
)


_extract_news_topic_from_text = news_context_service.extract_topic
_get_news_headlines = news_context_service.get_headlines
_get_news_items = news_context_service.get_items
_is_news_detail_query = news_context_service.is_detail_query
_is_news_followup_query = news_context_service.is_followup_query
_select_news_item_by_text = news_context_service.select_item_by_text
_build_news_detail_summary = news_context_service.build_detail_summary

_search_restaurants_nearby = CONTEXT_RUNTIME.search_restaurants_nearby

_is_vision_related_query = conversation_text_utils.is_vision_related_query
_is_vision_followup_utterance = conversation_text_utils.is_vision_followup_utterance
_is_congestion_query = route_text_utils.is_congestion_query
_is_schedule_query = route_text_utils.is_schedule_query
_is_arrival_eta_query = route_text_utils.is_arrival_eta_query
_normalize_place_name = route_text_utils.normalize_place_name
_is_home_update_utterance = conversation_text_utils.is_home_update_utterance
_resolve_destination_coords_from_name = CONTEXT_RUNTIME.resolve_destination_coords_from_name

_to_int = TRANSIT_RUNTIME.to_int
_round_eta_minutes = TRANSIT_RUNTIME.round_eta_minutes
_parse_eta_minutes_from_message = TRANSIT_RUNTIME.parse_eta_minutes_from_message
_format_eta_phrase = TRANSIT_RUNTIME.format_eta_phrase
_haversine_meters = TRANSIT_RUNTIME.haversine_meters
_estimate_walk_minutes = TRANSIT_RUNTIME.estimate_walk_minutes
_pick_station_from_odsay_response = TRANSIT_RUNTIME.pick_station_from_odsay_response
_get_nearby_station = TRANSIT_RUNTIME.get_nearby_station
_get_nearby_bus_stop = TRANSIT_RUNTIME.get_nearby_bus_stop
_weekday_to_tmap_dow = TRANSIT_RUNTIME.weekday_to_tmap_dow
_normalize_route_name_for_tmap = TRANSIT_RUNTIME.normalize_route_name_for_tmap
_extract_tmap_congestion_rows = TRANSIT_RUNTIME.extract_tmap_congestion_rows
_get_tmap_subway_car_congestion = TRANSIT_RUNTIME.get_tmap_subway_car_congestion
_get_odsay_path = TRANSIT_RUNTIME.get_odsay_path
_parse_odsay_strategy = TRANSIT_RUNTIME.parse_odsay_strategy
_parse_tmap_strategy = TRANSIT_RUNTIME.parse_tmap_strategy
_strategy_needs_odsay_backfill = TRANSIT_RUNTIME.strategy_needs_odsay_backfill
_merge_strategy_with_fallback = TRANSIT_RUNTIME.merge_strategy_with_fallback

_extract_schedule_search_dttm = route_text_utils.extract_schedule_search_dttm
_get_weather_only = CONTEXT_RUNTIME.get_weather_only
_get_air_only = CONTEXT_RUNTIME.get_air_only
_get_weather_and_air = CONTEXT_RUNTIME.get_weather_and_air
_is_env_cache_fresh = CONTEXT_RUNTIME.is_env_cache_fresh


LIVE_SEOUL_SUMMARY_SERVICE = LiveSeoulSummaryService(
    get_nearby_station=_get_nearby_station,
    get_nearby_bus_stop=_get_nearby_bus_stop,
    estimate_walk_minutes=_estimate_walk_minutes,
    resolve_destination_coords_from_name=_resolve_destination_coords_from_name,
    resolve_home_coords=_resolve_home_coords,
    is_schedule_query=_is_schedule_query,
    is_arrival_eta_query=_is_arrival_eta_query,
    extract_schedule_search_dttm=_extract_schedule_search_dttm,
    get_transit_route=TMAP_SERVICE.get_transit_route,
    parse_tmap_strategy=_parse_tmap_strategy,
    strategy_needs_odsay_backfill=_strategy_needs_odsay_backfill,
    get_odsay_path=_get_odsay_path,
    parse_odsay_strategy=_parse_odsay_strategy,
    merge_strategy_with_fallback=_merge_strategy_with_fallback,
    get_weather_and_air=_get_weather_and_air,
    get_tmap_subway_car_congestion=_get_tmap_subway_car_congestion,
    format_eta_phrase=_format_eta_phrase,
    get_subway_arrival=TRANSIT_RUNTIME.get_subway_arrival,
    extract_arrival_minutes=TRANSIT_RUNTIME.extract_arrival_minutes,
)

_build_live_seoul_summary = LIVE_SEOUL_SUMMARY_SERVICE.build_summary


seoul_live_service = SeoulLiveService(
    default_destination=COMMUTE_DEFAULT_DESTINATION,
    normalize_place_name=_normalize_place_name,
    build_live_summary=_build_live_seoul_summary,
    get_weather_only=_get_weather_only,
    get_air_only=_get_air_only,
    get_weather_and_air=_get_weather_and_air,
    is_env_cache_fresh=_is_env_cache_fresh,
    extract_news_topic=_extract_news_topic_from_text,
    get_news_headlines=_get_news_headlines,
    get_news_items=_get_news_items,
    search_restaurants=_search_restaurants_nearby,
)

_execute_tools_for_intent = seoul_live_service.execute_tools_for_intent
_fast_route_intent = lambda text, active_timer=False: fast_route_intent_core(
    text=text,
    active_timer=active_timer,
    destination_extractor=_extract_destination_from_text,
    arrival_eta_query_checker=_is_arrival_eta_query,
)

# --- Helper: Azure STT Setup ---
def create_recognizer(audio_config, language="en-US", silence_timeout_ms: str | None = None):
    return create_azure_recognizer(
        audio_config=audio_config,
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION,
        language=language,
        silence_timeout_ms=silence_timeout_ms,
    )

# --- WebSocket Endpoint ---
@app.websocket("/ws")
async def audio_websocket(ws: WebSocket):
    await ws.accept()
    
    # 1. Auth & Identification
    # Note: Frontend uses '?token=email@gmail.com'
    user_id = ws.query_params.get("token")
    current_lat = _to_float(ws.query_params.get("lat"))
    current_lng = _to_float(ws.query_params.get("lng"))
    client_state = {"lat": current_lat, "lng": current_lng, "last_log_lat": current_lat, "last_log_lng": current_lng}
    if not user_id or "@" not in user_id:
        print("[Server] Missing or invalid token.")
        await ws.close(code=1008, reason="Invalid Login Token")
        return
        
    print(f"[Server] Client connected: {user_id}")
    if current_lat is None or current_lng is None:
        print("[SeoulInfo] Missing lat/lng in websocket query. Live ODSAY routing will be unavailable.")
    else:
        print(f"[SeoulInfo] Client location lat={current_lat}, lng={current_lng}")
    if not API_KEY or not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        print("[Error] Missing API Keys.")
        await ws.close(code=1008, reason="API Keys missing")
        return

    # 2. Load Memory (Context)
    past_memories = await asyncio.to_thread(cosmos_service.get_all_memories, user_id)
    lumi_mem_str = ""
    rami_mem_str = ""
    
    if past_memories:
        print(f"[Memory] Loaded {len(past_memories)} past conversation summaries.")
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

    # 2.5 Load Personal Assistant Context (Calendar & Gmail)
    try:
        from modules.personal_assistant_service import PersonalAssistantService
        pa_service = await asyncio.to_thread(PersonalAssistantService, user_id)
        pa_context = await asyncio.to_thread(pa_service.get_context_summary)
        
        if pa_context:
            print("[Server] Successfully loaded Calendar/Gmail context.")
            pa_injection = f"\n\n[Live Personal Assistant Data (Current Context)]\n{pa_context}"
            lumi_mem_str += pa_injection
            rami_mem_str += pa_injection
    except Exception as e:
        print(f"[Server] Failed to load Personal Assistant data: {e}")

    user_profile = await asyncio.to_thread(cosmos_service.get_user_profile, user_id)
    saved_home_destination = None
    if isinstance(user_profile, dict):
        saved_home_destination = str(user_profile.get("home_destination") or "").strip() or None
    if saved_home_destination:
        print(f"[Profile] Loaded home destination for {user_id}: {saved_home_destination}")

    destination_state = {
        "name": saved_home_destination or COMMUTE_DEFAULT_DESTINATION,
        "asked_once": False,
    }
    env_cache = {"weather": {}, "air": {}, "lat": current_lat, "lng": current_lng, "ts": 0.0}
    news_state = {"topic": "", "items": [], "selected": None, "ts": 0.0}

    # Initialize Azure STT (User: 16kHz, AI: 24kHz)
    user_push_stream, user_audio_config = create_push_stream(16000)
    user_recognizer = create_recognizer(
        user_audio_config,
        "ko-KR",
        silence_timeout_ms=str(STT_SEGMENTATION_SILENCE_TIMEOUT_MS),
    )

    lumi_push_stream, lumi_audio_config = create_push_stream(24000)
    lumi_recognizer = create_recognizer(
        lumi_audio_config,
        "ko-KR",
        silence_timeout_ms=str(AI_STT_SEGMENTATION_SILENCE_TIMEOUT_MS),
    )
    
    rami_push_stream, rami_audio_config = create_push_stream(24000)
    rami_recognizer = create_recognizer(
        rami_audio_config,
        "ko-KR",
        silence_timeout_ms=str(AI_STT_SEGMENTATION_SILENCE_TIMEOUT_MS),
    )

    # Capture the main event loop
    loop = asyncio.get_running_loop()

    async def send_audio_to_client(audio_bytes: bytes, speaker_name: str):
        try:
            await ws.send_bytes(audio_bytes)
            if speaker_name == "lumi":
                await asyncio.to_thread(lumi_push_stream.write, audio_bytes)
                lumi_state["last_ai_write_time"] = time.monotonic()
                lumi_state["flushed"] = False
            elif speaker_name == "rami":
                await asyncio.to_thread(rami_push_stream.write, audio_bytes)
                rami_state["last_ai_write_time"] = time.monotonic()
                rami_state["flushed"] = False
        except Exception as e:
            print(f"[Server] Error sending audio for {speaker_name}: {e}")

    async def flush_ai_stt(speaker_name: str):
        try:
            silence = bytes(24000 * 2 * 1) 
            if speaker_name == "lumi":
                await asyncio.to_thread(lumi_push_stream.write, silence)
            elif speaker_name == "rami":
                await asyncio.to_thread(rami_push_stream.write, silence)
        except Exception as e:
            pass

    lumi_rami_manager = LumiRamiManager(ws_send_func=send_audio_to_client, flush_stt_func=flush_ai_stt)

    # Track state for Smart Flushing
    lumi_state = {"last_ai_write_time": 0.0, "flushed": True}
    rami_state = {"last_ai_write_time": 0.0, "flushed": True}
    vision_service = VisionService(
        min_interval_sec=CAMERA_FRAME_MIN_INTERVAL_SEC,
        snapshot_ttl_sec=VISION_SNAPSHOT_TTL_SEC,
        log=print,
    )
    dynamic_contexts = []
    dynamic_context_lock = asyncio.Lock()
    session_ref = {"obj": None}
    
    import uuid
    from datetime import datetime
    session_messages = []
    global_seq = 0
    conversation_id = f"c_{uuid.uuid4().hex[:8]}"
    session_start_time = datetime.utcnow().isoformat() + "Z"

    route_dedupe = {"text": "", "ts": 0.0}
    timer_set_dedupe = {"key": "", "ts": 0.0}
    context_turn_dedupe = {"key": "", "ts": 0.0}
    transcript_ui_dedupe = {"key": "", "ts": 0.0}
    user_activity = {"last_user_ts": time.monotonic()}
    speech_window_state = {"last_recognizing_ts": 0.0, "utterance_start_ts": 0.0}
    default_transport_mode = "public"
    if MORNING_BRIEFING is not None:
        try:
            default_transport_mode = MORNING_BRIEFING.get_default_transport_mode()
        except Exception:
            default_transport_mode = "public"
    briefing_state = {
        "wake_sent_date": "",
        "test_wake_sent": False,
        "leave_home_sent_date": "",
        "leave_office_sent_date": "",
        "last_leave_home_check_ts": 0.0,
        "last_leave_office_check_ts": 0.0,
        "awaiting_transport_choice": False,
        "selected_transport": default_transport_mode,
        "transport_choice_date": "",
    }
    transit_turn_gate = {"until": 0.0}
    speech_capture_gate = {"until": 0.0}
    response_guard = {
        "active": False,
        "context_sent": False,
        "suppressed_audio_seen": False,
        "block_direct_audio": False,
        "block_direct_audio_until": 0.0,
        "post_context_audio_hold_until": 0.0,
        "active_since": 0.0,
        "context_sent_at": 0.0,
        "pending_intent": None,
        "pending_context_summary": "",
        "pending_action_instruction": "",
        "pending_user_text": "",
        "retry_issued": False,
        "forced_intent_turn": None,
    }

    async def _inject_live_context_now(context_text: str, complete_turn: bool = False):
        if not getattr(lumi_rami_manager, "running", False):
            async with dynamic_context_lock:
                dynamic_contexts.append(context_text)
            return
        payload = "[LIVE_CONTEXT_UPDATE]\n" + context_text + "\nUse this for current answer."
        queue_key = "text" if complete_turn else "context"
        for name, q in lumi_rami_manager.queues.items():
            await q.put((queue_key, payload))

    proactive_service = ProactiveService(
        response_guard=response_guard,
        transit_turn_gate=transit_turn_gate,
        inject_live_context_now=_inject_live_context_now,
        log=print,
    )

    def _reset_response_gate(reason: str = ""):
        proactive_service.reset_response_gate(reason)

    async def _request_spoken_response_with_context(
        intent_tag: str,
        context_summary: str,
        action_instruction: str,
        tone: str = "neutral",
        style: str = "",
        complete_turn: bool = True,
    ):
        try:
            await proactive_service.request_spoken_response_with_context(
                intent_tag=intent_tag,
                context_summary=context_summary,
                action_instruction=action_instruction,
                tone=tone,
                style=style,
                complete_turn=complete_turn,
            )
            response_guard["context_sent"] = True
            response_guard["context_sent_at"] = time.monotonic()
        except Exception as e:
            print(f"[Guard] context request failed: {e}")
            _reset_response_gate("context request failed")

    def _submit_coroutine(coro, label: str):
        if not loop.is_running():
            return None
        fut = asyncio.run_coroutine_threadsafe(coro, loop)
        def _done_callback(f):
            try:
                _ = f.result()
            except Exception as ex:
                print(f"[Async:{label}] failed: {ex}")
        fut.add_done_callback(_done_callback)
        return fut

    def _queue_transcript_event(role: str, text: str):
        clean_text = str(text or "").strip()
        if not clean_text:
            return
        role_norm = str(role or "").strip().lower()
        if role_norm not in ("user", "lumi", "rami"):
            role_norm = "ai"
        normalized_text = re.sub(r"\s+", " ", clean_text)
        key = f"{role_norm}:{normalized_text}"
        now_ts = time.monotonic()
        if (
            key
            and key == str(transcript_ui_dedupe.get("key") or "")
            and (now_ts - float(transcript_ui_dedupe.get("ts") or 0.0)) < 1.2
        ):
            return
        transcript_ui_dedupe["key"] = key
        transcript_ui_dedupe["ts"] = now_ts

        # Build message object for memory saving
        nonlocal global_seq
        created_at_str = datetime.utcnow().isoformat() + "Z"
        
        msg_obj = {
            "message_id": f"msg_{conversation_id}_{(global_seq):03d}",
            "conversation_id": conversation_id,
            "seq": global_seq,
            "speaker_type": "user" if role_norm == "user" else "ai",
            "ai_persona": role_norm if (role_norm in ("lumi", "rami")) else None,
            "text": clean_text,
            "created_at": created_at_str
        }
        global_seq += 1
        session_messages.append(msg_obj)

        payload = json.dumps({"type": "transcript", "role": role_norm, "text": clean_text})
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(ws.send_text(payload), loop)
        else:
            print(f"[Error] Main loop is closed. Cannot send STT: {clean_text}")

    async def _send_user_text_turn(user_text: str):
        if not getattr(lumi_rami_manager, "running", False):
            return
        payload = [{"role": "user", "parts": [{"text": str(user_text or "")}]}]
        for name, q in lumi_rami_manager.queues.items():
            await q.put(("turns", payload))

    async def _send_user_text_with_snapshot_turn(user_text: str, snapshot_bytes: bytes):
        if not getattr(lumi_rami_manager, "running", False):
            return
            
        import base64 as _b64
        frame_tag = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%H:%M:%S")
        
        # We append inline base64 string directly into prompt Turn instead of unreliable realtime_input.
        b64_str = _b64.b64encode(snapshot_bytes).decode("utf-8")
        parts = [
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": b64_str
                }
            },
            {
                "text": (
                    "[VISION TURN]\n"
                    f"Frame time: {frame_tag} KST.\n"
                    "Prioritize the camera frame that was just uploaded.\n"
                    "Only use memory if it does not conflict with the frame."
                )
            },
            {"text": f"사용자: {str(user_text or '')}"}
        ]
        
        payload = [{"role": "user", "parts": parts}]
        for name, q in lumi_rami_manager.queues.items():
            await q.put(("turns", payload))

    async def _inject_guarded_context_turn(context_text: str):
        try:
            await _inject_live_context_now(context_text, complete_turn=True)
            response_guard["context_sent"] = True
            response_guard["context_sent_at"] = time.monotonic()
        except Exception as e:
            print(f"[Guard] guarded context inject failed: {e}")
            _reset_response_gate("guarded context inject failed")

    async def _send_proactive_announcement(
        summary_text: str,
        tone: str = "neutral",
        style: str = "",
        add_followup_hint: bool = True,
        max_chars: int = 220,
        max_sentences: int = 5,
        split_by_sentence: bool = False,
        chunk_max_sentences: int = 1,
        chunk_max_chars: int = 180,
    ):
        await proactive_service.send_proactive_announcement(
            summary_text=summary_text,
            tone=tone,
            style=style,
            add_followup_hint=add_followup_hint,
            max_chars=max_chars,
            max_sentences=max_sentences,
            split_by_sentence=False,
            chunk_max_sentences=chunk_max_sentences,
            chunk_max_chars=chunk_max_chars,
        )

    async def _on_timer_fired(delay_sec: int):
        if delay_sec >= 60:
            amount = max(1, delay_sec // 60)
            unit = "분"
        else:
            amount = delay_sec
            unit = "초"
        await _send_proactive_announcement(
            f"요청하신 {amount}{unit}이 지났어요. 다시 이야기할까요?",
            tone="neutral",
            add_followup_hint=False,
        )

    timer_service = TimerService(
        on_fire=_on_timer_fired,
        log=print,
    )

    briefing_runtime = BriefingRuntimeService(
        morning_briefing=MORNING_BRIEFING,
        send_proactive_announcement=_send_proactive_announcement,
        runtime_env_bool=runtime_env_utils.runtime_env_bool,
        runtime_env_path=RUNTIME_ENV_PATH,
        briefing_pre_ad_copy=BRIEFING_PRE_AD_COPY,
        log=print,
    )

    async def _inject_initial_location_context():
        if client_state.get("lat") is None or client_state.get("lng") is None:
            return
        try:
            await _inject_live_context_now(
                "[INTENT:location_context] Current location coordinates are already known from device. "
                "Do not ask user's current location.",
                complete_turn=False,
            )
        except Exception as e:
            print(f"[SeoulInfo] initial location context injection failed: {e}")

    async def _save_home_destination(new_home_destination: str):
        dest = str(new_home_destination or "").strip()
        if not dest:
            return
        try:
            await asyncio.to_thread(
                cosmos_service.upsert_user_profile,
                user_id,
                {"home_destination": dest},
            )
        except Exception as e:
            print(f"[Profile] Failed to save home destination: {e}")

    async def _preload_env_cache(force: bool = False):
        lat = client_state.get("lat")
        lng = client_state.get("lng")
        if lat is None or lng is None:
            return
        fresh = _is_env_cache_fresh(env_cache, lat, lng)
        if fresh and not force:
            return
        try:
            weather, air = await asyncio.to_thread(_get_weather_and_air, lat, lng)
            env_cache["weather"] = weather or {}
            env_cache["air"] = air or {}
            env_cache["lat"] = lat
            env_cache["lng"] = lng
            env_cache["ts"] = time.monotonic()
            print(
                f"[SeoulInfo] Env cache refreshed: "
                f"weather={bool(env_cache['weather'])}, air={bool(env_cache['air'])}"
            )
        except Exception as e:
            print(f"[SeoulInfo] Env cache refresh failed: {e}")

    # STT Event Handlers
    def on_recognized(args, role):
        if args.result.text:
            text = args.result.text
            print(f"[STT] {role}: {text}")
            _queue_transcript_event(role, text)

            if role == "user":
                try:
                    user_activity["last_user_ts"] = time.monotonic()
                    speech_capture_gate["until"] = max(
                        float(speech_capture_gate.get("until") or 0.0),
                        time.monotonic() + 1.0,
                    )

                    normalized_user_text = re.sub(r"[\s\W_]+", "", str(text or ""))
                    now_ts = time.monotonic()
                    utterance_start_ts = float(speech_window_state.get("utterance_start_ts") or 0.0)
                    if utterance_start_ts <= 0:
                        utterance_start_ts = max(0.0, now_ts - 2.0)

                    camera_on = bool(vision_service.camera_state.get("enabled", False))
                    explicit_vision = _is_vision_related_query(text)
                    inferred_vision = camera_on and _is_vision_followup_utterance(text)
                    is_vision_query = explicit_vision or inferred_vision
                    snapshot_bytes = (
                        vision_service.get_snapshot_for_speech_window(
                            utterance_start_ts=utterance_start_ts,
                            utterance_end_ts=now_ts,
                            pre_roll_sec=2.0,
                            max_age_sec=12.0,
                        )
                        if camera_on
                        else None
                    )
                    speech_window_state["utterance_start_ts"] = 0.0
                    if is_vision_query and snapshot_bytes and loop.is_running():
                        _submit_coroutine(
                            _send_user_text_with_snapshot_turn(text, snapshot_bytes),
                            label="vision_turn_with_snapshot",
                        )
                        return
                    # Azure STT can emit near-duplicate finalized chunks; skip fast duplicates.
                    if (
                        normalized_user_text
                        and normalized_user_text == route_dedupe.get("text")
                        and (now_ts - float(route_dedupe.get("ts") or 0.0)) < 1.5
                    ):
                        print(f"[IntentRouter] skip duplicate user turn: {text}")
                        return
                    route_dedupe["text"] = normalized_user_text
                    route_dedupe["ts"] = now_ts

                    transport_pick = briefing_runtime.apply_transport_choice(briefing_state, text)
                    if transport_pick.get("handled"):
                        if loop.is_running():
                            _submit_coroutine(
                                _send_proactive_announcement(
                                    summary_text=str(transport_pick.get("ack_text") or ""),
                                    tone="neutral",
                                    add_followup_hint=False,
                                    max_chars=80,
                                    max_sentences=2,
                                ),
                                label="transport_choice_ack",
                            )
                        if bool(transport_pick.get("should_short_circuit")):
                            return

                    route = _fast_route_intent(text, active_timer=timer_service.has_active())
                    if not route:
                        route = intent_router.route(text, active_timer=timer_service.has_active())
                    intent = route.get("intent") if isinstance(route, dict) else "commute_overview"
                    routed_dest = route.get("destination") if isinstance(route, dict) else None
                    routed_home_update = bool(route.get("home_update")) if isinstance(route, dict) else False
                    routed_timer_seconds = route.get("timer_seconds") if isinstance(route, dict) else None
                    route_source = route.get("source") if isinstance(route, dict) else "fallback"
                    print(
                        f"[IntentRouter] source={route_source}, intent={intent}, "
                        f"destination={routed_dest}, home_update={routed_home_update}, "
                        f"timer_seconds={routed_timer_seconds}"
                    )
                    if intent == "timer_cancel" and (not timer_service.has_active()):
                        # Timer cancel intent is only meaningful while a timer is active.
                        intent = "general"
                    if intent == "timer_cancel" and timer_service.has_active():
                        canceled = timer_service.cancel_all()
                        # Force a single controlled response turn; suppress direct audio turn.
                        response_guard["active"] = True
                        response_guard["context_sent"] = False
                        response_guard["suppressed_audio_seen"] = False
                        response_guard["block_direct_audio"] = True
                        response_guard["active_since"] = time.monotonic()
                        response_guard["context_sent_at"] = 0.0
                        response_guard["block_direct_audio_until"] = max(
                            float(response_guard.get("block_direct_audio_until") or 0.0),
                            time.monotonic() + 4.0,
                        )
                        _submit_coroutine(
                            _inject_guarded_context_turn(
                                f"[INTENT:timer_canceled] Canceled {canceled} active timer(s). "
                                "Acknowledge cancellation briefly in Korean, then answer the user's current request directly."
                            ),
                            label="timer_cancel",
                        )
                        # Let the same user utterance proceed naturally after cancel notice.
                        # Do not run live-tool routing for this branch.
                        return
                    if intent == "timer" and loop.is_running():
                        timer_sec = None
                        try:
                            timer_sec = int(routed_timer_seconds) if routed_timer_seconds is not None else None
                        except Exception:
                            timer_sec = None
                        if timer_sec is not None and 5 <= timer_sec <= 21600:
                            # Prevent duplicate "timer set" responses from near-duplicate STT finalization.
                            timer_key = f"{timer_sec}:{normalized_user_text}"
                            now_timer_ts = time.monotonic()
                            if (
                                timer_key
                                and timer_key == str(timer_set_dedupe.get("key") or "")
                                and (now_timer_ts - float(timer_set_dedupe.get("ts") or 0.0)) < 2.5
                            ):
                                print(f"[Timer] duplicate timer_set skipped: {timer_sec}s")
                                return
                            timer_set_dedupe["key"] = timer_key
                            timer_set_dedupe["ts"] = now_timer_ts

                            # Force a single controlled timer-set response.
                            response_guard["active"] = True
                            response_guard["context_sent"] = False
                            response_guard["suppressed_audio_seen"] = False
                            response_guard["block_direct_audio"] = True
                            response_guard["active_since"] = time.monotonic()
                            response_guard["context_sent_at"] = 0.0
                            response_guard["retry_issued"] = False
                            response_guard["block_direct_audio_until"] = max(
                                float(response_guard.get("block_direct_audio_until") or 0.0),
                                time.monotonic() + 4.0,
                            )
                            transit_turn_gate["until"] = max(
                                float(transit_turn_gate.get("until") or 0.0),
                                time.monotonic() + 1.1,
                            )
                            _submit_coroutine(
                                _inject_guarded_context_turn(
                                    (
                                        f"[INTENT:timer_set] Timer seconds={timer_sec}. "
                                        "Confirm timer set in one short Korean sentence. "
                                        "Do not repeat the same timer confirmation."
                                    )
                                ),
                                label="timer_set",
                            )
                            asyncio.run_coroutine_threadsafe(
                                timer_service.register(timer_sec),
                                loop,
                            )
                            print(f"[Timer] timer_set accepted: {timer_sec}s")
                        else:
                            print("[Timer] timer_set rejected: invalid timer_seconds")
                        return

                    # News detail/follow-up inference from recently fetched news items.
                    has_recent_news = (
                        bool(news_state.get("items"))
                        and (now_ts - float(news_state.get("ts") or 0.0)) < 900
                    )
                    if has_recent_news and intent in {"general", "news"}:
                        wants_detail = _is_news_detail_query(text)
                        wants_followup = _is_news_followup_query(text)
                        if wants_detail or wants_followup:
                            matched_item = _select_news_item_by_text(
                                text=text,
                                items=(news_state.get("items") or []),
                            )
                            if matched_item is None and wants_followup:
                                matched_item = news_state.get("selected")
                            # Detail request without explicit match:
                            # keep conversation in current news context instead of re-fetching generic news.
                            if matched_item is None and wants_detail:
                                matched_item = news_state.get("selected") or ((news_state.get("items") or [None])[0])
                            if matched_item is not None:
                                news_state["selected"] = matched_item
                                intent = "news_detail" if wants_detail else "news_followup"

                    # LLM-first: only use regex destination extraction when fallback routing is active.
                    if route_source == "llm":
                        dest = routed_dest
                    else:
                        dest = routed_dest or _extract_destination_from_text(text)
                    # If destination is explicitly mentioned with route-like wording, prefer route intent.
                    if dest and intent == "general" and any(k in text for k in ["길", "경로", "가는"]):
                        intent = "commute_overview"
                    if dest:
                        next_dest = str(dest).strip()
                        if next_dest and next_dest != destination_state.get("name"):
                            destination_state["name"] = next_dest
                        destination_state["asked_once"] = False

                    # Persist home destination only when classifier says this is a home update utterance.
                    if routed_home_update or (route_source != "llm" and _is_home_update_utterance(text)):
                        home_candidate = str(dest or "").strip()
                        # Fallback: If LLM missed the destination but flagged home_update=True, try regex extraction
                        if not home_candidate:
                            home_candidate = str(_extract_destination_from_text(text) or "").strip()
                            
                        if home_candidate:
                            destination_state["name"] = home_candidate
                            destination_state["asked_once"] = False
                            if loop.is_running():
                                _submit_coroutine(
                                    _save_home_destination(home_candidate),
                                    label="save_home",
                                )
                            print(f"[Profile] Home destination updated in-session: {home_candidate}")

                    live_summary = None
                    routing_intents = ws_orchestrator.ROUTING_INTENTS
                    should_inject_live = intent in routing_intents

                    if should_inject_live:
                        # Always gate response until live context is injected to prevent pre-context utterances.
                        ws_orchestrator.arm_live_response_gate(
                            response_guard=response_guard,
                            transit_turn_gate=transit_turn_gate,
                            intent=intent,
                        )
                        response_guard["active_since"] = time.monotonic()
                        response_guard["context_sent_at"] = 0.0
                        response_guard["retry_issued"] = False
                        if client_state.get("lat") is not None and client_state.get("lng") is not None and loop.is_running():
                            asyncio.run_coroutine_threadsafe(
                                _inject_live_context_now(
                                    "[INTENT:location_guard] Device location is already known and valid for this turn. "
                                    "Do not ask user location.",
                                    complete_turn=False,
                                ),
                                loop,
                            )

                        # For transit queries that require live API fetch, speak a short filler first.
                        # This reduces awkward silence while ODSAY/Seoul APIs are being fetched.
                        if (
                            (not EFFECTIVE_GEMINI_DIRECT_AUDIO_INPUT)
                            and ENABLE_TRANSIT_FILLER
                            and intent in {"subway_route", "bus_route", "commute_overview"}
                            and loop.is_running()
                        ):
                            filler_text = (
                                "[INTENT:loading] The user requested live transit guidance. "
                                "First, say one short Korean filler sentence naturally "
                                "(e.g., '음, 잠시만요. 지금 확인해볼게요.'). "
                                "Do not provide route details yet. "
                                "Do not ask for user location."
                            )
                            asyncio.run_coroutine_threadsafe(
                                _inject_live_context_now(filler_text, complete_turn=True),
                                loop,
                            )
                        transit_intents = ws_orchestrator.TRANSIT_INTENTS
                        context_destination = destination_state["name"] if intent in transit_intents else None
                        if intent in {"news_detail", "news_followup"}:
                            picked = news_state.get("selected")
                            if picked is None and news_state.get("items"):
                                picked = _select_news_item_by_text(text=text, items=(news_state.get("items") or []))
                            if picked is None and news_state.get("items"):
                                picked = (news_state.get("items") or [None])[0]
                            if picked is not None:
                                news_state["selected"] = picked
                            detail_summary = _build_news_detail_summary(picked) if picked else "먼저 최신 뉴스를 불러온 뒤에, 관심 있는 키워드를 말해주시면 자세히 설명해드릴게요."
                            live_data = {
                                "speechSummary": detail_summary,
                                "news": {
                                    "topic": news_state.get("topic") or "",
                                    "headlines": [str(i.get("title") or "").strip() for i in (news_state.get("items") or []) if isinstance(i, dict)],
                                    "items": news_state.get("items") or [],
                                    "selected": picked,
                                },
                            }
                        else:
                            live_data = _execute_tools_for_intent(
                                intent=intent or "commute_overview",
                                lat=client_state.get("lat"),
                                lng=client_state.get("lng"),
                                destination_name=context_destination,
                                env_cache=env_cache,
                                user_text=text,
                            )
                        live_summary = live_data.get("speechSummary") if isinstance(live_data, dict) else None
                        # Strict fail-closed behavior for API-backed intents:
                        # if data is unavailable, do not provide alternative guidance.
                        api_backed_intents = {"subway_route", "bus_route", "commute_overview", "weather", "air_quality", "restaurant", "news"}
                        if intent in api_backed_intents:
                            if not isinstance(live_data, dict):
                                live_summary = "현재 요청하신 정보를 받을 수 없습니다."
                            elif not str(live_data.get("speechSummary") or "").strip():
                                live_summary = "현재 요청하신 정보를 받을 수 없습니다."

                        # If user asked congestion specifically, do not fallback to route guidance.
                        if intent in {"subway_route", "commute_overview"} and _is_congestion_query(text):
                            cong = live_data.get("subwayCongestion") if isinstance(live_data, dict) else None
                            least_car = str(cong.get("leastCar") or "").strip() if isinstance(cong, dict) else ""
                            if not least_car:
                                live_summary = "현재 지하철 혼잡도 정보를 받을 수 없습니다."
                        if intent == "news":
                            news_meta = live_data.get("news") if isinstance(live_data, dict) else None
                            if isinstance(news_meta, dict):
                                news_state["topic"] = str(news_meta.get("topic") or "").strip()
                                items = news_meta.get("items") or []
                                if isinstance(items, list):
                                    news_state["items"] = [i for i in items if isinstance(i, dict)]
                                else:
                                    news_state["items"] = []
                                news_state["selected"] = None
                                news_state["ts"] = time.monotonic()
                        print(
                            f"[SeoulInfo] live context built: intent={intent}, destination={context_destination}, "
                            f"summary_ok={bool(live_summary)}"
                        )

                        guidance = []
                        if client_state.get("lat") is not None and client_state.get("lng") is not None:
                            guidance.append("Location is known; do not ask user's current location.")
                        if intent in transit_intents and destination_state.get("name"):
                            guidance.append(
                                f"Use destination '{destination_state['name']}' for this turn and ignore older destination context."
                            )
                        if (
                            not destination_state.get("name")
                            and intent in transit_intents
                        ):
                            if not destination_state.get("asked_once", False):
                                guidance.append("Ask destination exactly once in one short question.")
                                destination_state["asked_once"] = True
                            else:
                                guidance.append("Destination still missing; do not repeat destination question.")

                        if not live_summary:
                            live_summary = "현재 요청하신 정보를 받을 수 없습니다."

                        context_priority_intents = ws_orchestrator.CONTEXT_PRIORITY_INTENTS
                        context_summary = ws_orchestrator.merge_context_summary(
                            live_summary=live_summary,
                            guidance=guidance,
                        )
                        action_instruction = ws_orchestrator.build_action_instruction(intent)

                        if intent in context_priority_intents:
                            # Keep gate a little longer while response turn is being finalized.
                            ws_orchestrator.extend_post_context_gate(transit_turn_gate)

                        if loop.is_running():
                            # Suppress near-duplicate context turns generated by STT split finalization.
                            normalized_summary = re.sub(r"\s+", " ", str(context_summary or "")).strip()[:220]
                            dedupe_key = f"{intent}|{normalized_summary}"
                            now_ctx_ts = time.monotonic()
                            if (
                                dedupe_key
                                and dedupe_key == str(context_turn_dedupe.get("key") or "")
                                and (now_ctx_ts - float(context_turn_dedupe.get("ts") or 0.0)) < 8.0
                            ):
                                print(f"[Guard] duplicate context turn skipped: intent={intent}")
                                return
                            context_turn_dedupe["key"] = dedupe_key
                            context_turn_dedupe["ts"] = now_ctx_ts
                            response_guard["pending_intent"] = (intent or "commute_overview")
                            response_guard["pending_context_summary"] = context_summary
                            response_guard["pending_action_instruction"] = action_instruction
                            response_guard["pending_user_text"] = str(text or "").strip()
                            _submit_coroutine(
                                _request_spoken_response_with_context(
                                    intent_tag=(intent or "commute_overview"),
                                    context_summary=context_summary,
                                    action_instruction=action_instruction,
                                    tone="neutral",
                                    complete_turn=(intent in context_priority_intents),
                                ),
                                label=f"context_turn:{intent}",
                            )
                    else:
                        # Text-only path for non-routing/general turns when direct audio is disabled.
                        if (not EFFECTIVE_GEMINI_DIRECT_AUDIO_INPUT) and loop.is_running():
                            asyncio.run_coroutine_threadsafe(_send_user_text_turn(text), loop)
                except Exception as e:
                    print(f"[SeoulInfo] dynamic context build failed: {e}")
            
    def on_recognizing(args, role):
        if role != "user":
            return
        text = str(getattr(args.result, "text", "") or "").strip()
        if not text:
            return
        now_ts = time.monotonic()
        user_activity["last_user_ts"] = now_ts
        last_ts = float(speech_window_state.get("last_recognizing_ts") or 0.0)
        if (now_ts - last_ts) > 0.9:
            speech_window_state["utterance_start_ts"] = now_ts
        speech_window_state["last_recognizing_ts"] = now_ts
        # Gate early model audio while user speech is being finalized by STT.
        speech_capture_gate["until"] = max(float(speech_capture_gate.get("until") or 0.0), now_ts + 1.2)
        # Also hard-block direct audio briefly to avoid stale pre-context model turns.
        response_guard["block_direct_audio"] = True
        response_guard["block_direct_audio_until"] = max(
            float(response_guard.get("block_direct_audio_until") or 0.0),
            now_ts + 1.5,
        )

    def dual_on_recognized(args, role):
        if args.result.text:
            text = args.result.text
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(lumi_rami_manager.handle_stt_result(text, role), loop)
            on_recognized(args, role)

    user_recognizer.recognized.connect(lambda evt: dual_on_recognized(evt, "user"))
    lumi_recognizer.recognized.connect(lambda evt: dual_on_recognized(evt, "lumi"))
    rami_recognizer.recognized.connect(lambda evt: dual_on_recognized(evt, "rami"))
    user_recognizer.recognizing.connect(lambda evt: on_recognizing(evt, "user"))

    user_recognizer.start_continuous_recognition()
    lumi_recognizer.start_continuous_recognition()
    rami_recognizer.start_continuous_recognition()

    try:
        await lumi_rami_manager.start(lumi_memory=lumi_mem_str, rami_memory=rami_mem_str)
        await _preload_env_cache(force=True)
        await _inject_initial_location_context()
        
        async def receive_from_client():
            try:
                while True:
                    msg = await ws.receive()
                    msg_type = msg.get("type")
                    if msg_type == "websocket.disconnect":
                        print("[Server] WebSocket Disconnected (Receive Loop)")
                        return
                    if msg_type != "websocket.receive":
                        continue

                    text_data = msg.get("text")
                    if text_data:
                        try:
                            payload = json.loads(text_data)
                            if isinstance(payload, dict) and payload.get("type") == "location_update":
                                new_lat = _to_float(payload.get("lat"))
                                new_lng = _to_float(payload.get("lng"))
                                if new_lat is not None and new_lng is not None:
                                    client_state["lat"] = new_lat
                                    client_state["lng"] = new_lng
                                    prev_lat = _to_float(client_state.get("last_log_lat"))
                                    prev_lng = _to_float(client_state.get("last_log_lng"))
                                    moved_m = None
                                    if prev_lat is not None and prev_lng is not None:
                                        moved_m = _haversine_meters(prev_lat, prev_lng, new_lat, new_lng)
                                    if moved_m is None or moved_m >= 25:
                                        print(f"[SeoulInfo] Location updated lat={new_lat}, lng={new_lng}")
                                        client_state["last_log_lat"] = new_lat
                                        client_state["last_log_lng"] = new_lng
                                    if moved_m is None or moved_m >= 80:
                                        asyncio.create_task(_preload_env_cache(force=False))
                                    asyncio.create_task(
                                        briefing_runtime.maybe_send_leaving_home_alert(
                                            briefing_state=briefing_state,
                                            current_gps={"lat": new_lat, "lng": new_lng},
                                        )
                                    )
                                    asyncio.create_task(
                                        briefing_runtime.maybe_send_evening_local_alert(
                                            briefing_state=briefing_state,
                                            current_gps={"lat": new_lat, "lng": new_lng},
                                            moved_m=moved_m,
                                        )
                                    )
                            elif isinstance(payload, dict) and payload.get("type") == "camera_state":
                                await vision_service.set_camera_enabled(
                                    enabled=bool(payload.get("enabled")),
                                    inject_live_context_now=_inject_live_context_now,
                                )
                            elif isinstance(payload, dict) and payload.get("type") == "camera_frame_base64":
                                await vision_service.handle_camera_frame_payload(
                                    payload=payload,
                                    push_image_now=lumi_rami_manager.push_image if hasattr(lumi_rami_manager, "push_image") else None,
                                    inject_live_context_now=_inject_live_context_now,
                                )
                            elif isinstance(payload, dict) and payload.get("type") == "camera_snapshot_base64":
                                await vision_service.handle_camera_snapshot_payload(
                                    payload=payload,
                                    push_image_now=lumi_rami_manager.push_image if hasattr(lumi_rami_manager, "push_image") else None,
                                    inject_live_context_now=_inject_live_context_now,
                                )
                            elif isinstance(payload, dict) and payload.get("type") == "multimodal_input":
                                input_text = payload.get("text", "")
                                input_image = payload.get("image_b64")
                                
                                msg_disp = input_text
                                if input_image:
                                    msg_disp = "[Photo Attached] " + msg_disp
                                _queue_transcript_event("user", msg_disp)
                                print(f"[Multimodal] USER: {msg_disp}")
                                
                                if input_image:
                                    try:
                                        import base64
                                        b64_str = input_image.split(",")[-1] if "," in input_image else input_image
                                        img_bytes = base64.b64decode(b64_str)
                                        if loop.is_running():
                                            _submit_coroutine(lumi_rami_manager.handle_multimodal_input(input_text, image_bytes=img_bytes), label="multimodal_img")
                                    except Exception as e:
                                        print(f"[Multimodal] Error parsing image: {e}")
                                else:
                                    if loop.is_running() and input_text:
                                        _submit_coroutine(lumi_rami_manager.handle_multimodal_input(input_text), label="multimodal_txt")

                        except Exception:
                            pass
                        continue

                    data = msg.get("bytes")
                    if not data:
                        continue

                    if (
                        (not response_guard.get("active"))
                        and response_guard.get("block_direct_audio")
                        and time.monotonic() >= float(response_guard.get("block_direct_audio_until") or 0.0)
                    ):
                        response_guard["block_direct_audio"] = False

                    injected_context = None
                    async with dynamic_context_lock:
                        if dynamic_contexts:
                            injected_context = dynamic_contexts.pop()
                            dynamic_contexts.clear()
                    if injected_context:
                        try:
                            payload = "[LIVE_CONTEXT_UPDATE]\n" + injected_context + "\nUse this for current answer."
                            for name, q in lumi_rami_manager.queues.items():
                                await q.put(("text", payload))
                            transit_turn_gate["until"] = min(
                                float(transit_turn_gate.get("until") or 0.0),
                                time.monotonic() + 0.15,
                            )
                        except Exception as e:
                            print(f"[SeoulInfo] context injection failed: {e}")
                            
                    if (
                        EFFECTIVE_GEMINI_DIRECT_AUDIO_INPUT
                        and (not response_guard.get("active"))
                        and (not response_guard.get("block_direct_audio"))
                        and time.monotonic() >= float(response_guard.get("block_direct_audio_until") or 0.0)
                        and time.monotonic() >= float(response_guard.get("post_context_audio_hold_until") or 0.0)
                        and time.monotonic() >= float(transit_turn_gate.get("until") or 0.0)
                    ):
                        await lumi_rami_manager.push_audio(data)
                        
                    await asyncio.to_thread(user_push_stream.write, data)
            except WebSocketDisconnect:
                print("[Server] WebSocket Disconnected (Receive Loop)")
                return
            except Exception as e:
                print(f"[Server] Error processing input: {e}")

        # Run tasks
        async def smart_flush_injector():
            silence_chunk = b"\x00" * int(max(1, AI_FLUSH_SILENCE_SEC) * 48000)
            try:
                while True:
                    await asyncio.sleep(0.1)
                    now_mono = time.monotonic()
                    
                    if (now_mono - lumi_state["last_ai_write_time"] > AI_FLUSH_SILENCE_AFTER_SEC) and not lumi_state["flushed"]:
                        await asyncio.to_thread(lumi_push_stream.write, silence_chunk)
                        lumi_state["flushed"] = True
                        
                    if (now_mono - rami_state["last_ai_write_time"] > AI_FLUSH_SILENCE_AFTER_SEC) and not rami_state["flushed"]:
                        await asyncio.to_thread(rami_push_stream.write, silence_chunk)
                        rami_state["flushed"] = True
            except asyncio.CancelledError:
                pass

        tasks = [
            asyncio.create_task(receive_from_client()),
            asyncio.create_task(smart_flush_injector()),
        ]
        if MORNING_BRIEFING is not None:
            tasks.append(asyncio.create_task(briefing_runtime.scheduler_loop(briefing_state)))
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending: task.cancel()

    except Exception as e:
        print(f"[Server] Session Error or Disconnect: {e}")
    finally:
        # Cleanup
        session_ref["obj"] = None
        print("[Server] Cleaning up resources...")
        await timer_service.shutdown()
        await lumi_rami_manager.stop()
        try:
            await asyncio.wait_for(asyncio.to_thread(user_recognizer.stop_continuous_recognition), timeout=2.0)
            await asyncio.wait_for(asyncio.to_thread(lumi_recognizer.stop_continuous_recognition), timeout=2.0)
            await asyncio.wait_for(asyncio.to_thread(rami_recognizer.stop_continuous_recognition), timeout=2.0)
        except Exception as e:
            print(f"[Server] Cleanup Warning: {e}")
        try: await ws.close() 
        except: pass
        print("[Server] Connection closed")

        # 3. Save Memory (Unified Unified Schema)
        if session_messages and len(session_messages) > 2: # Don't save overly short sessions
            print("[Memory] Analyzing unified memory graph and turns...")
            
            # Blocking I/O -> Async Thread
            session_end_time = datetime.utcnow().isoformat() + "Z"
            conversation_data = await asyncio.to_thread(
                memory_service.analyze_unified_memory,
                conversation_id,
                user_id,
                session_start_time,
                session_end_time,
                session_messages
            )
            
            if conversation_data:
                await asyncio.to_thread(cosmos_service.save_memory, user_id, conversation_data)
                print(f"[Memory] Unified Session Graph saved for {user_id} ({conversation_id})")
            else:
                print("[Memory] Skipped saving: unified memory analysis failed.")

app.include_router(
    create_api_router(
        build_live_seoul_summary=_build_live_seoul_summary,
        to_float=_to_float,
        morning_briefing=MORNING_BRIEFING,
        build_seoul_info_packet=build_seoul_info_packet,
        build_speech_summary=build_speech_summary,
    )
)

@app.get("/api/memory")
async def get_memory_history(token: str):
    """
    Fetch all conversation memories from Cosmos DB for a specific user.
    'token' acts as the user_id (e.g. user's email address).
    Returns a unified array of conversation graph and message objects.
    """
    if not token:
        return {"ok": False, "error": "Missing token"}
    items = await asyncio.to_thread(cosmos_service.get_all_memories, token)
    return {"ok": True, "data": items}

# --- OAuth Routes for Frontend ---

@app.get('/login')
async def login(request: Request, redirect_target: str = "http://localhost:5173"):
    # Save target URL to session
    request.session['redirect_target'] = redirect_target
    # Reconstruct the redirect URI based on actual incoming headers (ngrok/azure support)
    forwarded_proto = request.headers.get("x-forwarded-proto", "http")
    host = request.headers.get("host", request.url.hostname)
    if request.url.port and request.url.port not in (80, 443) and ":" not in host:
         host = f"{host}:{request.url.port}"
         
    redirect_uri = f"{forwarded_proto}://{host}/auth"
        
    return await oauth.google.authorize_redirect(request, redirect_uri, access_type='offline')

@app.get('/auth')
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        if not user_info:
             user_info = await oauth.google.userinfo(token=token)

        # Save/Update User in Cosmos DB (Users Container)
        if cosmos_service.users_container:
            user_data = {
                "id": str(uuid.uuid4()),
                "email": user_info['email'],
                "name": user_info.get('name'),
                "picture": user_info.get('picture'),
                "last_login": datetime.datetime.utcnow().isoformat(),
                "google_token": token
            }
            
            try:
                # Query by email to preserve ID
                query = "SELECT * FROM c WHERE c.email = @email"
                params = [{"name": "@email", "value": user_info['email']}]
                items = list(cosmos_service.users_container.query_items(
                    query=query, parameters=params, enable_cross_partition_query=True
                ))
                if items:
                    user_data['id'] = items[0]['id']
                cosmos_service.users_container.upsert_item(user_data)
                print(f"[Auth] User {user_info['email']} saved/updated.")
            except Exception as e:
                print(f"[Auth] DB Save Error: {e}")
        else:
            print("[Auth] Missing users_container in Cosmos DB.")
        
        # Session Setting
        request.session['user'] = user_info
        token_str = user_info['email']
        request.session['token'] = token_str
        
        # [Auto-Login Logic]
        target_url = request.session.pop('redirect_target', 'http://localhost:5173')
        # If the target URL already has a query string, append with &, otherwise ?
        sep = "&" if "?" in target_url else "?"
        final_redirect = f"{target_url}{sep}token={token_str}"
        
        return RedirectResponse(url=final_redirect)

    except Exception as e:
        return HTMLResponse(f"<h1>Auth Error</h1><p>{e}</p>")

@app.get('/logout')
async def logout(request: Request, redirect_target: str = "http://localhost:5173"):
    request.session.pop('user', None)
    request.session.pop('token', None)
    return RedirectResponse(url=redirect_target)

@app.get("/api/memory")
async def get_user_memory(token: str = None):
    """
    Serve the unified memory JSON data to the React History MVP Graph.
    Expected frontend query: /api/memory?token=xxx@gmail.com
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing user token")
    
    # In a real app we would verify the token. Here we use it as email/userid.
    user_email = token.strip()
    try:
        memories = await asyncio.to_thread(cosmos_service.get_all_memories, user_email)
        return {"data": memories}
        
    except Exception as e:
        print(f"[API] Error fetching memory for {user_email}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
