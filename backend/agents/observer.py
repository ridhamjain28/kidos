"""
KidOS MVP - Observer Agent 📊
===============================
Monitors child engagement and frustration in real-time.
Reuses engagement/cognitive_load math from IBLM_v2 CognitiveStateEngine.

Spec logic:
  if avg_tap_latency > 500ms AND back_button > 3x/min:
      frustration_level = "high", engagement_score = 35
  elif avg_tap_latency < 200ms AND error_rate < 0.2:
      frustration_level = "low", engagement_score = 85
  else:
      frustration_level = "medium", engagement_score = 65
"""

from dataclasses import dataclass
from typing import Dict, Any

from backend.config import (
    TAP_LATENCY_HIGH_MS,
    TAP_LATENCY_LOW_MS,
    BACK_BUTTON_FRUSTRATION_THRESHOLD,
    ERROR_RATE_LOW,
)


def _clamp(value: float, min_v: float = 0.0, max_v: float = 1.0) -> float:
    return max(min_v, min(value, max_v))


@dataclass
class EngagementState:
    """Internal cognitive/engagement state for a child session.
    Adapted from IBLM_v2 MentalState."""
    engagement: float = 0.5
    cognitive_load: float = 0.2
    emotional_stability: float = 0.5
    trust_level: float = 0.8


class ObserverAgent:
    """Monitors child engagement and frustration from telemetry signals."""

    def __init__(self):
        self._session_states: Dict[str, EngagementState] = {}

    def _get_state(self, session_id: str) -> EngagementState:
        if session_id not in self._session_states:
            self._session_states[session_id] = EngagementState()
        return self._session_states[session_id]

    def analyze(
        self,
        session_id: str,
        tap_latency_ms: int,
        back_button_count: int,
        scroll_speed: str,
        time_on_task_sec: int,
        error_rate: float,
    ) -> Dict[str, Any]:
        """
        Analyze telemetry and return engagement assessment.

        Returns:
            {
                "engagement_score": 0-100,
                "mood": "happy" | "neutral" | "frustrated" | "tired",
                "frustration_level": "low" | "medium" | "high",
                "recommended_action": "continue" | "simplify" | "switch_activity" | "encourage"
            }
        """
        state = self._get_state(session_id)

        # ─── Spec Rule: Frustration Detection ───
        if tap_latency_ms > TAP_LATENCY_HIGH_MS and back_button_count > BACK_BUTTON_FRUSTRATION_THRESHOLD:
            frustration_level = "high"
            engagement_score = 35
            mood = "frustrated"
            recommended_action = "simplify"
        elif tap_latency_ms < TAP_LATENCY_LOW_MS and error_rate < ERROR_RATE_LOW:
            frustration_level = "low"
            engagement_score = 85
            mood = "happy"
            recommended_action = "continue"
        else:
            frustration_level = "medium"
            engagement_score = 65
            mood = "neutral"
            recommended_action = "continue"

        # ─── IBLM_v2 Refinement: Cognitive State Update ───
        # Reused from CognitiveStateEngine.update_state()
        cognitive_load = _clamp(error_rate * 0.5 + (back_button_count * 0.1))
        emotional_stability = _clamp(
            state.emotional_stability
            - cognitive_load
            + (0.1 if error_rate < 0.3 else -0.1)
        )

        # Scroll speed penalty
        if scroll_speed == "fast":
            engagement_score = max(20, engagement_score - 15)
            if frustration_level != "high":
                mood = "tired" if time_on_task_sec > 300 else mood

        # Time fatigue (sessions > 10 min)
        if time_on_task_sec > 600:
            engagement_score = max(20, engagement_score - 10)
            if mood == "neutral":
                mood = "tired"

        # Refine action based on combined signals
        if engagement_score < 40:
            recommended_action = "switch_activity"
        elif engagement_score < 50 and frustration_level == "medium":
            recommended_action = "encourage"

        # Update internal state for next call
        state.engagement = engagement_score / 100.0
        state.cognitive_load = cognitive_load
        state.emotional_stability = emotional_stability

        return {
            "engagement_score": engagement_score,
            "mood": mood,
            "frustration_level": frustration_level,
            "recommended_action": recommended_action,
            # Internal state (for Orchestrator)
            "_cognitive_load": round(cognitive_load, 3),
            "_emotional_stability": round(emotional_stability, 3),
        }

    def clear_session(self, session_id: str):
        """Remove session state when session ends."""
        self._session_states.pop(session_id, None)
