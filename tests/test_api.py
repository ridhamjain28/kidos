"""
KidOS MVP - API Integration Tests
====================================
Tests the full FastAPI endpoints with mock data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_root():
    """Health check endpoint."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "KidOS Agentic AI"


def test_session_start():
    """Start a session and get session_id."""
    resp = client.post("/api/v1/session/start", json={
        "child_id": "test-child-001",
        "preferred_topic": "gravity"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["profile_loaded"] is True
    assert data["initial_topic"] == "gravity"


def test_telemetry():
    """Send telemetry and get engagement assessment."""
    # First start a session
    start = client.post("/api/v1/session/start", json={
        "child_id": "test-child-002"
    }).json()

    resp = client.post("/api/v1/telemetry", json={
        "child_id": "test-child-002",
        "session_id": start["session_id"],
        "tap_latency_ms": 600,
        "back_button_count": 5,
        "scroll_speed": "fast",
        "time_on_task_sec": 120,
        "error_rate": 0.5
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "engagement_score" in data
    assert "mood" in data
    assert "next_action" in data
    assert data["frustration_level"] == "high"


def test_recommend():
    """Get content recommendation."""
    # Ensure profile exists first
    client.post("/api/v1/session/start", json={
        "child_id": "test-child-003"
    })

    resp = client.post("/api/v1/recommend", json={
        "child_id": "test-child-003",
        "current_topic": "gravity"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "recommended_topic" in data
    assert "content_type" in data
    assert "reason" in data


def test_session_end():
    """End a session and get next recommendation."""
    start = client.post("/api/v1/session/start", json={
        "child_id": "test-child-004"
    }).json()

    resp = client.post("/api/v1/session/end", json={
        "session_id": start["session_id"],
        "final_engagement_score": 75,
        "topics_covered": ["gravity", "planets"],
        "completion_rate": 0.8
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile_updated"] is True
    assert "next_recommendation" in data


def test_full_session_lifecycle():
    """Integration: Start → Telemetry → Recommend → End."""
    # 1. Start
    start = client.post("/api/v1/session/start", json={
        "child_id": "test-child-lifecycle",
        "preferred_topic": "animals"
    }).json()
    session_id = start["session_id"]
    assert start["profile_loaded"]

    # 2. Telemetry (3 rounds)
    for i in range(3):
        tel = client.post("/api/v1/telemetry", json={
            "child_id": "test-child-lifecycle",
            "session_id": session_id,
            "tap_latency_ms": 200 + i * 100,
            "back_button_count": i,
            "scroll_speed": "normal",
            "time_on_task_sec": 30 * (i + 1),
            "error_rate": 0.1 * i
        }).json()
        assert "engagement_score" in tel

    # 3. Recommend
    rec = client.post("/api/v1/recommend", json={
        "child_id": "test-child-lifecycle",
        "current_topic": "animals"
    }).json()
    assert "recommended_topic" in rec

    # 4. End
    end = client.post("/api/v1/session/end", json={
        "session_id": session_id,
        "final_engagement_score": 70,
        "topics_covered": ["animals"],
        "completion_rate": 0.7
    }).json()
    assert end["profile_updated"]


if __name__ == "__main__":
    test_root()
    test_session_start()
    test_telemetry()
    test_recommend()
    test_session_end()
    test_full_session_lifecycle()
    print("✅ All API tests passed!")
