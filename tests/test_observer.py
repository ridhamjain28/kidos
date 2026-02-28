"""
KidOS MVP - Observer Agent Tests
==================================
High priority: Verify frustration detection and engagement scoring.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Direct import to avoid pulling in chromadb via agents/__init__.py
from backend.agents.observer import ObserverAgent


def test_high_frustration():
    """High tap latency + many back buttons → frustration HIGH, engagement 35."""
    agent = ObserverAgent()
    result = agent.analyze(
        session_id="test-session-1",
        tap_latency_ms=600,
        back_button_count=5,
        scroll_speed="fast",
        time_on_task_sec=120,
        error_rate=0.5,
    )
    assert result["frustration_level"] == "high"
    assert result["engagement_score"] <= 40
    assert result["mood"] == "frustrated"


def test_high_engagement():
    """Low tap latency + low error rate → engagement HIGH."""
    agent = ObserverAgent()
    result = agent.analyze(
        session_id="test-session-2",
        tap_latency_ms=150,
        back_button_count=0,
        scroll_speed="normal",
        time_on_task_sec=60,
        error_rate=0.1,
    )
    assert result["frustration_level"] == "low"
    assert result["engagement_score"] >= 80
    assert result["mood"] == "happy"


def test_medium_engagement():
    """Average signals → medium engagement."""
    agent = ObserverAgent()
    result = agent.analyze(
        session_id="test-session-3",
        tap_latency_ms=350,
        back_button_count=1,
        scroll_speed="normal",
        time_on_task_sec=90,
        error_rate=0.3,
    )
    assert result["frustration_level"] == "medium"
    assert 50 <= result["engagement_score"] <= 75
    assert result["mood"] == "neutral"


def test_time_fatigue():
    """Long session > 10min degrades engagement."""
    agent = ObserverAgent()
    result = agent.analyze(
        session_id="test-session-4",
        tap_latency_ms=300,
        back_button_count=1,
        scroll_speed="normal",
        time_on_task_sec=700,  # > 600s = 10+ min
        error_rate=0.25,
    )
    assert result["engagement_score"] < 65  # Reduced from medium base


def test_fast_scroll_penalty():
    """Fast scrolling reduces engagement."""
    agent = ObserverAgent()
    result = agent.analyze(
        session_id="test-session-5",
        tap_latency_ms=300,
        back_button_count=1,
        scroll_speed="fast",
        time_on_task_sec=60,
        error_rate=0.25,
    )
    # Should be lower than normal scroll with same params
    result_normal = agent.analyze(
        session_id="test-session-6",
        tap_latency_ms=300,
        back_button_count=1,
        scroll_speed="normal",
        time_on_task_sec=60,
        error_rate=0.25,
    )
    assert result["engagement_score"] < result_normal["engagement_score"]


def test_session_state_tracking():
    """Verify session state is maintained across calls."""
    agent = ObserverAgent()
    # First call
    agent.analyze("test-track", 600, 5, "fast", 120, 0.5)
    # Second call to same session
    result = agent.analyze("test-track", 150, 0, "normal", 180, 0.1)
    # State should carry over (emotional_stability affected by previous interaction)
    assert "_emotional_stability" in result
    assert "_cognitive_load" in result


def test_clear_session():
    """Clearing session removes state."""
    agent = ObserverAgent()
    agent.analyze("test-clear", 300, 1, "normal", 60, 0.3)
    agent.clear_session("test-clear")
    # After clear, should start fresh
    result = agent.analyze("test-clear", 150, 0, "normal", 60, 0.1)
    assert result["frustration_level"] == "low"


if __name__ == "__main__":
    test_high_frustration()
    test_high_engagement()
    test_medium_engagement()
    test_time_fatigue()
    test_fast_scroll_penalty()
    test_session_state_tracking()
    test_clear_session()
    print("✅ All Observer Agent tests passed!")
