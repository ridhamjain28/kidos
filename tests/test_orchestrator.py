"""
KidOS MVP - Orchestrator Agent Tests
=======================================
High priority: Verify correct agent routing based on engagement + session state.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.agents.orchestrator import OrchestratorAgent


def test_low_engagement_routes_to_encouragement():
    """Engagement < 40 → encouragement agent."""
    agent = OrchestratorAgent()
    result = agent.decide(
        observer_output={
            "engagement_score": 30,
            "mood": "frustrated",
            "frustration_level": "high",
            "_cognitive_load": 0.3,
            "_emotional_stability": 0.5,
        },
        session_time_sec=120,
        academic_tier="Level 2",
    )
    assert result["agent_to_route"] == "encouragement_agent"
    assert result["next_action"] == "simplify_content"
    assert result["prompt_modifiers"]["tone"] == "encouraging"


def test_level1_routes_to_simplified():
    """Level 1 academic tier → simplified teaching agent."""
    agent = OrchestratorAgent()
    result = agent.decide(
        observer_output={
            "engagement_score": 60,
            "mood": "neutral",
            "frustration_level": "medium",
            "_cognitive_load": 0.2,
            "_emotional_stability": 0.6,
        },
        session_time_sec=120,
        academic_tier="Level 1",
    )
    assert result["agent_to_route"] == "simplified_teaching_agent"
    assert result["prompt_modifiers"]["vocabulary_level"] == "simplified"


def test_long_session_high_engagement_routes_to_recommender():
    """Session > 10 min AND engagement > 70 → recommender agent."""
    agent = OrchestratorAgent()
    result = agent.decide(
        observer_output={
            "engagement_score": 80,
            "mood": "happy",
            "frustration_level": "low",
            "_cognitive_load": 0.1,
            "_emotional_stability": 0.8,
        },
        session_time_sec=700,  # > 600s = 10 min
        academic_tier="Level 2",
    )
    assert result["agent_to_route"] == "recommender_agent"
    assert result["next_action"] == "suggest_video"


def test_default_routes_to_standard_teaching():
    """Default case → standard teaching agent."""
    agent = OrchestratorAgent()
    result = agent.decide(
        observer_output={
            "engagement_score": 60,
            "mood": "neutral",
            "frustration_level": "medium",
            "_cognitive_load": 0.2,
            "_emotional_stability": 0.6,
        },
        session_time_sec=300,
        academic_tier="Level 2",
    )
    assert result["agent_to_route"] == "standard_teaching_agent"
    assert result["next_action"] == "continue_lesson"


def test_high_risk_triggers_safety():
    """High cognitive risk → safety fallback (from IBLM_v2 Governor)."""
    agent = OrchestratorAgent()
    result = agent.decide(
        observer_output={
            "engagement_score": 55,
            "mood": "neutral",
            "frustration_level": "medium",
            "_cognitive_load": 0.8,
            "_emotional_stability": 0.2,
        },
        session_time_sec=120,
        academic_tier="Level 2",
    )
    assert result["agent_to_route"] == "encouragement_agent"
    assert result["next_action"] == "calm_and_simplify"
    assert result["prompt_modifiers"]["tone"] == "calm"


if __name__ == "__main__":
    test_low_engagement_routes_to_encouragement()
    test_level1_routes_to_simplified()
    test_long_session_high_engagement_routes_to_recommender()
    test_default_routes_to_standard_teaching()
    test_high_risk_triggers_safety()
    print("✅ All Orchestrator Agent tests passed!")
