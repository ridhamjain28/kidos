"""
KidOS MVP - FastAPI Entry Point
==================================
5 API endpoints as specified in the Agentic Architecture doc.
Runs on localhost:8000 for local-first privacy.
"""

import json
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from backend.config import BACKEND_PORT, DEBUG
from backend.schemas import (
    TelemetryRequest,
    TelemetryResponse,
    GenerateRequest,
    GenerateToken,
    RecommendRequest,
    RecommendResponse,
    SessionStartRequest,
    SessionStartResponse,
    SessionEndRequest,
    SessionEndResponse,
    PromptModifiers,
)
from backend.agents.observer import ObserverAgent
from backend.agents.orchestrator import OrchestratorAgent
from backend.agents.teaching_specialist import TeachingSpecialistAgent
from backend.agents.recommender import RecommenderAgent
from backend.database.sqlite_store import SQLiteStore
from backend.database.vector_store import VectorStore
from backend.models.ollama_client import ollama_client


# ─── Global Instances ───
db = SQLiteStore()
vector_store = VectorStore()
observer = ObserverAgent()
orchestrator = OrchestratorAgent()
teacher = TeachingSpecialistAgent()
recommender = RecommenderAgent(db=db, vector_store=vector_store)

# Session tracking (in-memory for MVP)
active_sessions: dict = {}  # session_id → {child_id, start_time, topics, ...}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: check Ollama health."""
    health = await ollama_client.check_health()
    status = health["status"]
    model = health["target_model"]
    available = health["target_available"]
    print(f"\n🧠 KidOS Agentic MVP Starting...")
    print(f"   Ollama: {status}")
    print(f"   Model: {model} ({'✅ available' if available else '❌ not found'})")
    if status == "offline":
        print(f"   ⚠️  Ollama offline. Teaching Agent will use mock responses.")
        print(f"   💡 Install: https://ollama.com → then run: ollama pull {model}")
    print(f"   Database: {db.db_path}")
    print(f"   API Docs: http://localhost:{BACKEND_PORT}/docs\n")
    yield
    print("\n🛑 KidOS shutting down...\n")


app = FastAPI(
    title="KidOS Agentic AI",
    description="Edge-native agentic learning system for children (5-12)",
    version="0.1.0-mvp",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ───

@app.get("/")
async def root():
    health = await ollama_client.check_health()
    return {
        "service": "KidOS Agentic AI",
        "version": "0.1.0-mvp",
        "ollama": health["status"],
        "model": health["target_model"],
    }


# ─── 1. POST /api/v1/telemetry ───

@app.post("/api/v1/telemetry", response_model=TelemetryResponse)
async def telemetry(req: TelemetryRequest):
    """Send user interaction data → get engagement assessment + routing decision."""

    # Step 1: Observer analyzes telemetry
    observation = observer.analyze(
        session_id=req.session_id,
        tap_latency_ms=req.tap_latency_ms,
        back_button_count=req.back_button_count,
        scroll_speed=req.scroll_speed.value,
        time_on_task_sec=req.time_on_task_sec,
        error_rate=req.error_rate,
    )

    # Step 2: Orchestrator decides next action
    session_info = active_sessions.get(req.session_id, {})
    session_time = session_info.get("elapsed_sec", req.time_on_task_sec)
    academic_tier = session_info.get("academic_tier", "Level 1")

    routing = orchestrator.decide(
        observer_output=observation,
        session_time_sec=session_time,
        academic_tier=academic_tier,
    )

    # Step 3: Log interaction to vector store
    vector_store.store_behavior(
        child_id=req.child_id,
        behavior_type="telemetry",
        description=f"engagement:{observation['engagement_score']} mood:{observation['mood']} frustration:{observation['frustration_level']}",
        metadata={"engagement_score": observation["engagement_score"]},
    )

    return TelemetryResponse(
        engagement_score=observation["engagement_score"],
        mood=observation["mood"],
        frustration_level=observation["frustration_level"],
        next_action=routing["next_action"],
        agent_routed=routing["agent_to_route"],
        prompt_modifiers=PromptModifiers(**routing["prompt_modifiers"]),
    )


# ─── 2. POST /api/v1/generate ───

@app.post("/api/v1/generate")
async def generate(req: GenerateRequest):
    """Generate lesson content (SSE streaming)."""

    profile = db.get_or_create_profile(req.child_id)
    age = profile.get("age", 7)

    async def event_stream():
        async for token in teacher.generate_lesson(
            topic=req.topic,
            age=age,
            academic_tier=req.academic_tier,
            mood=req.mood.value,
            prompt_modifiers=req.prompt_modifiers,
        ):
            yield {
                "event": "token",
                "data": json.dumps({"token": token, "complete": False}),
            }
        yield {
            "event": "token",
            "data": json.dumps({"token": "", "complete": True}),
        }

    return EventSourceResponse(event_stream())


# ─── 3. POST /api/v1/recommend ───

@app.post("/api/v1/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest):
    """Get next content recommendation."""

    # Get latest engagement score from vector store
    behaviors = vector_store.query_behaviors(req.child_id, "engagement", top_k=1)
    last_engagement = 50
    if behaviors:
        last_engagement = behaviors[0].get("metadata", {}).get("engagement_score", 50)

    result = recommender.suggest(
        child_id=req.child_id,
        current_topic=req.current_topic,
        engagement_score=last_engagement,
    )

    # Cache recommendation
    db.cache_recommendation(
        child_id=req.child_id,
        topic=result["recommended_topic"],
        content_type=result["content_type"],
        confidence=0.7,
    )

    return RecommendResponse(**result)


# ─── 4. POST /api/v1/session/start ───

@app.post("/api/v1/session/start", response_model=SessionStartResponse)
async def session_start(req: SessionStartRequest):
    """Initialize a learning session."""

    profile = db.get_or_create_profile(req.child_id)
    session_id = db.create_session(req.child_id)

    # Determine initial topic
    initial_topic = req.preferred_topic
    if not initial_topic:
        suggestion = recommender.suggest(child_id=req.child_id)
        initial_topic = suggestion["recommended_topic"]

    # Track active session
    active_sessions[session_id] = {
        "child_id": req.child_id,
        "academic_tier": profile.get("academic_tier", "Level 1"),
        "elapsed_sec": 0,
        "topics": [initial_topic],
    }

    return SessionStartResponse(
        session_id=session_id,
        initial_topic=initial_topic,
        academic_tier=profile.get("academic_tier", "Level 1"),
        profile_loaded=True,
    )


# ─── 5. POST /api/v1/session/end ───

@app.post("/api/v1/session/end", response_model=SessionEndResponse)
async def session_end(req: SessionEndRequest):
    """Close session, save progress, and get next recommendation."""

    # Persist session data
    db.end_session(
        session_id=req.session_id,
        engagement_score=req.final_engagement_score,
        topics=req.topics_covered,
        completion_rate=req.completion_rate,
    )

    # Log topic interactions
    session_info = active_sessions.pop(req.session_id, {})
    child_id = session_info.get("child_id", "")
    for topic in req.topics_covered:
        db.log_interaction(
            session_id=req.session_id,
            topic=topic,
            content_type="lesson",
            engagement_score=req.final_engagement_score,
            completed=req.completion_rate > 0.5,
        )
        vector_store.store_topic_interest(child_id, topic, req.final_engagement_score)

    # Clean up observer state
    observer.clear_session(req.session_id)

    # Get next recommendation
    suggestion = recommender.suggest(
        child_id=child_id,
        engagement_score=req.final_engagement_score,
    )

    streak = db.get_streak_days(child_id) if child_id else 0

    return SessionEndResponse(
        profile_updated=True,
        next_recommendation=suggestion["recommended_topic"],
        streak_days=streak,
    )


# ─── Backend __init__ ───

# Create backend/__init__.py marker
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=BACKEND_PORT, reload=DEBUG)
