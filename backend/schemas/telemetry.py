"""
KidOS MVP - Telemetry Schemas
==============================
Pydantic models for API request/response validation.
Matches the spec's API contract exactly.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ScrollSpeed(str, Enum):
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


class Mood(str, Enum):
    HAPPY = "happy"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    TIRED = "tired"


class FrustrationLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ContentType(str, Enum):
    LESSON = "lesson"
    VIDEO = "video"
    QUIZ = "quiz"
    GAME = "game"


# ─── Request Models ───


class TelemetryRequest(BaseModel):
    """POST /telemetry - User interaction data from the app."""
    child_id: str = Field(..., description="UUID of the child")
    session_id: str = Field(..., description="UUID of the active session")
    tap_latency_ms: int = Field(default=300, ge=0, description="Average tap response time in ms")
    back_button_count: int = Field(default=0, ge=0, description="Back button presses per minute")
    scroll_speed: ScrollSpeed = Field(default=ScrollSpeed.NORMAL)
    time_on_task_sec: int = Field(default=0, ge=0, description="Seconds spent on current task")
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Fraction of failed attempts")


class GenerateRequest(BaseModel):
    """POST /generate - Request lesson content generation."""
    child_id: str
    topic: str = Field(..., min_length=1, description="Lesson topic")
    academic_tier: str = Field(default="Level 1", description="Level 1, 2, or 3")
    mood: Mood = Field(default=Mood.NEUTRAL)
    prompt_modifiers: dict = Field(default_factory=dict)


class RecommendRequest(BaseModel):
    """GET /recommend - Request next content recommendation."""
    child_id: str
    current_topic: str = Field(default="", description="Topic just completed")


class SessionStartRequest(BaseModel):
    """POST /session/start - Initialize a learning session."""
    child_id: str
    preferred_topic: str = Field(default="")


class SessionEndRequest(BaseModel):
    """POST /session/end - Close session and save progress."""
    session_id: str
    final_engagement_score: int = Field(default=50, ge=0, le=100)
    topics_covered: List[str] = Field(default_factory=list)
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
