"""
KidOS MVP - Orchestrator Agent 🎯
====================================
Decides which specialist agent handles the current situation.
Reuses CognitiveGovernor safety pattern from IBLM_v2.

Spec decision tree:
  if engagement_score < 40:
      route_to = "encouragement_agent", action = "simplify_content"
  elif academic_tier == "Level 1":
      route_to = "simplified_teaching_agent", action = "continue_lesson"
  elif session_time > 10_min AND engagement > 70:
      route_to = "recommender_agent", action = "suggest_video"
  else:
      route_to = "standard_teaching_agent", action = "continue_lesson"
"""

from typing import Dict, Any, Optional

from backend.config import ENGAGEMENT_LOW_THRESHOLD, ENGAGEMENT_HIGH_THRESHOLD, SESSION_SWITCH_MINUTES


# Risk threshold adapted from IBLM_v2 CognitiveGovernor
RISK_THRESHOLD = 0.45


class OrchestratorAgent:
    """Routes requests to the appropriate specialist agent based on engagement state."""

    def decide(
        self,
        observer_output: Dict[str, Any],
        session_time_sec: int = 0,
        learning_objective: str = "",
        academic_tier: str = "Level 1",
    ) -> Dict[str, Any]:
        """
        Decide which agent should handle the current situation.

        Args:
            observer_output: Output from ObserverAgent.analyze()
            session_time_sec: Current session duration in seconds
            learning_objective: Current learning goal
            academic_tier: Child's academic level

        Returns:
            {
                "next_action": str,
                "agent_to_route": str,
                "prompt_modifiers": {
                    "tone": str,
                    "vocabulary_level": str,
                    "max_syllables": int
                }
            }
        """
        engagement = observer_output["engagement_score"]
        frustration = observer_output["frustration_level"]
        mood = observer_output["mood"]
        cognitive_load = observer_output.get("_cognitive_load", 0.3)

        # ─── IBLM_v2 Safety Check (CognitiveGovernor pattern) ───
        risk_score = cognitive_load * 0.6 + (1 - observer_output.get("_emotional_stability", 0.5)) * 0.4
        if risk_score > RISK_THRESHOLD:
            return self._route_to_safety(mood)

        # ─── Spec Decision Tree ───
        session_minutes = session_time_sec / 60

        if engagement < ENGAGEMENT_LOW_THRESHOLD:
            return {
                "next_action": "simplify_content",
                "agent_to_route": "encouragement_agent",
                "prompt_modifiers": {
                    "tone": "encouraging",
                    "vocabulary_level": "simplified",
                    "max_syllables": 2,
                },
            }

        if academic_tier == "Level 1":
            return {
                "next_action": "continue_lesson",
                "agent_to_route": "simplified_teaching_agent",
                "prompt_modifiers": {
                    "tone": "playful",
                    "vocabulary_level": "simplified",
                    "max_syllables": 2,
                },
            }

        if session_minutes > SESSION_SWITCH_MINUTES and engagement > ENGAGEMENT_HIGH_THRESHOLD:
            return {
                "next_action": "suggest_video",
                "agent_to_route": "recommender_agent",
                "prompt_modifiers": {
                    "tone": "enthusiastic",
                    "vocabulary_level": "standard",
                    "max_syllables": 3,
                },
            }

        # Default: continue with standard teaching
        tone = "encouraging" if frustration == "medium" else "neutral"
        vocab = "standard" if academic_tier != "Level 1" else "simplified"

        return {
            "next_action": "continue_lesson",
            "agent_to_route": "standard_teaching_agent",
            "prompt_modifiers": {
                "tone": tone,
                "vocabulary_level": vocab,
                "max_syllables": 3,
            },
        }

    def _route_to_safety(self, mood: str) -> Dict[str, Any]:
        """Safety fallback when cognitive risk is too high (from IBLM_v2 Governor)."""
        return {
            "next_action": "calm_and_simplify",
            "agent_to_route": "encouragement_agent",
            "prompt_modifiers": {
                "tone": "calm",
                "vocabulary_level": "simplified",
                "max_syllables": 2,
            },
        }
