"""
KidOS MVP - Response Schemas
==============================
Pydantic models for API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class PromptModifiers(BaseModel):
    """Modifiers applied to teaching prompts by the Orchestrator."""
    tone: str = Field(default="neutral", description="encouraging, neutral, calm")
    vocabulary_level: str = Field(default="standard", description="simplified, standard, advanced")
    max_syllables: int = Field(default=3, ge=1, le=5)


class TelemetryResponse(BaseModel):
    """Response from POST /telemetry."""
    engagement_score: int = Field(..., ge=0, le=100)
    mood: str
    frustration_level: str
    next_action: str
    agent_routed: str = Field(default="standard_teaching_agent")
    prompt_modifiers: PromptModifiers = Field(default_factory=PromptModifiers)


class GenerateToken(BaseModel):
    """Single token in the SSE stream from POST /generate."""
    token: str
    complete: bool = False


class RecommendResponse(BaseModel):
    """Response from GET /recommend."""
    recommended_topic: str
    content_type: str
    difficulty_level: int = Field(ge=1, le=3)
    reason: str


class SessionStartResponse(BaseModel):
    """Response from POST /session/start."""
    session_id: str
    initial_topic: str
    academic_tier: str
    profile_loaded: bool


class SessionEndResponse(BaseModel):
    """Response from POST /session/end."""
    profile_updated: bool
    next_recommendation: str = ""
    streak_days: int = 0
