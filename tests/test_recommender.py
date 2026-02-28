"""
KidOS MVP - Recommender Agent Tests
=======================================
Tests recommendation logic, anti-echo-chamber, and topic progression.
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Use temp database paths for tests
os.environ["DATABASE_PATH"] = os.path.join(tempfile.gettempdir(), "kidos_test_rec.db")
os.environ["CHROMA_PATH"] = os.path.join(tempfile.gettempdir(), "kidos_test_chroma")

from backend.database.sqlite_store import SQLiteStore
from backend.database.vector_store import VectorStore
from backend.agents.recommender import RecommenderAgent


def _make_agent():
    db = SQLiteStore(os.environ["DATABASE_PATH"])
    vs = VectorStore(os.environ["CHROMA_PATH"])
    return RecommenderAgent(db=db, vector_store=vs), db, vs


def test_low_engagement_simplifies():
    """Engagement < 40 → recommend same topic simplified."""
    agent, db, vs = _make_agent()
    db.get_or_create_profile("kid-rec-1")

    result = agent.suggest(
        child_id="kid-rec-1",
        current_topic="gravity",
        engagement_score=30,
    )
    assert result["recommended_topic"] == "gravity"
    assert result["difficulty_level"] == 1
    assert "simplif" in result["reason"].lower()


def test_high_engagement_advances():
    """Completed topic + high engagement → advance to next topic."""
    agent, db, vs = _make_agent()
    db.get_or_create_profile("kid-rec-2")
    session_id = db.create_session("kid-rec-2")
    db.log_interaction(session_id, "gravity", "lesson", 85, True)

    result = agent.suggest(
        child_id="kid-rec-2",
        current_topic="gravity",
        engagement_score=80,
    )
    assert result["recommended_topic"] in ["planets", "forces"]
    assert result["difficulty_level"] >= 2
    assert "advancing" in result["reason"].lower() or "high engagement" in result["reason"].lower()


def test_new_child_gets_default():
    """Brand new child → gets a beginner default topic."""
    agent, db, vs = _make_agent()
    db.get_or_create_profile("kid-rec-3")

    result = agent.suggest(
        child_id="kid-rec-3",
        current_topic="",
        engagement_score=50,
    )
    assert result["recommended_topic"] in ["animals", "colors", "numbers", "planets", "gravity"]
    assert result["difficulty_level"] == 1


def test_anti_echo_chamber():
    """Every 4th suggestion should be a challenge topic."""
    agent, db, vs = _make_agent()
    db.get_or_create_profile("kid-rec-4")

    results = []
    for i in range(4):
        r = agent.suggest(
            child_id="kid-rec-4",
            current_topic="",
            engagement_score=60,
        )
        results.append(r)

    # 4th item should be a challenge/quiz
    assert results[3]["content_type"] == "quiz"
    assert "growth" in results[3]["reason"].lower() or "challenge" in results[3]["reason"].lower()


if __name__ == "__main__":
    test_low_engagement_simplifies()
    test_high_engagement_advances()
    test_new_child_gets_default()
    test_anti_echo_chamber()
    print("All Recommender Agent tests passed!")
