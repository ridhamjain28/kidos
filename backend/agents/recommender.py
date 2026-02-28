"""
KidOS MVP - Recommendation Agent 🎬
======================================
Suggests next content based on learning history and engagement.
Ports mastery tracking, STV decay, and anti-echo-chamber from IBLMContext.tsx.

Spec logic (MVP if-this-then-that):
  if child_completed("gravity_basics") AND engagement > 70:
      recommend("gravity_experiment_video"), recommend("planets_quiz_level2")
  elif engagement < 40 on last_topic:
      recommend("same_topic_simplified")
"""

from typing import Dict, Any, List, Optional

from backend.database.sqlite_store import SQLiteStore
from backend.database.vector_store import VectorStore


# Content progression map (MVP: hard-coded topic graph)
TOPIC_GRAPH: Dict[str, Dict[str, Any]] = {
    "gravity": {
        "next": ["planets", "forces"],
        "related_video": "gravity_experiment_video",
        "difficulty": 1,
    },
    "planets": {
        "next": ["solar_system", "stars"],
        "related_video": "planets_tour_video",
        "difficulty": 2,
    },
    "solar_system": {
        "next": ["galaxies", "astronauts"],
        "related_video": "solar_system_video",
        "difficulty": 2,
    },
    "animals": {
        "next": ["habitats", "food_chains"],
        "related_video": "animal_safari_video",
        "difficulty": 1,
    },
    "habitats": {
        "next": ["ecosystems", "weather"],
        "related_video": "habitat_explorer_video",
        "difficulty": 2,
    },
    "numbers": {
        "next": ["addition", "shapes"],
        "related_video": "counting_fun_video",
        "difficulty": 1,
    },
    "addition": {
        "next": ["subtraction", "multiplication"],
        "related_video": "math_adventure_video",
        "difficulty": 2,
    },
    "colors": {
        "next": ["painting", "light"],
        "related_video": "rainbow_science_video",
        "difficulty": 1,
    },
}

# Default topics for new children
DEFAULT_TOPICS = ["animals", "colors", "numbers", "planets", "gravity"]


class RecommenderAgent:
    """Suggests personalized next content based on history and engagement."""

    def __init__(self, db: SQLiteStore, vector_store: VectorStore):
        self.db = db
        self.vector_store = vector_store
        self._items_served: Dict[str, int] = {}  # child_id → count (anti-echo-chamber)

    def suggest(
        self,
        child_id: str,
        current_topic: str = "",
        engagement_score: int = 50,
    ) -> Dict[str, Any]:
        """
        Suggest the next content for a child.

        Returns:
            {
                "recommended_topic": str,
                "content_type": "lesson" | "video" | "quiz",
                "difficulty_level": 1-3,
                "reason": str
            }
        """
        completed = self.db.get_completed_topics(child_id)
        topic_scores = self.db.get_topic_engagement(child_id)
        top_interests = self.vector_store.get_top_interests(child_id)

        # Track items served for anti-echo-chamber (ported from IBLMContext.tsx)
        count = self._items_served.get(child_id, 0) + 1
        self._items_served[child_id] = count

        # ─── Spec Rule: Low engagement → simplify ───
        if engagement_score < 40 and current_topic:
            return {
                "recommended_topic": current_topic,
                "content_type": "lesson",
                "difficulty_level": 1,
                "reason": "Low engagement detected. Simplifying current topic.",
            }

        # ─── Spec Rule: Completed topic + high engagement → advance ───
        if current_topic in completed and engagement_score > 70:
            graph_entry = TOPIC_GRAPH.get(current_topic, {})
            next_topics = graph_entry.get("next", [])
            if next_topics:
                # Pick first unfinished next topic
                for nt in next_topics:
                    if nt not in completed:
                        return {
                            "recommended_topic": nt,
                            "content_type": "video" if count % 3 == 0 else "lesson",
                            "difficulty_level": min(3, graph_entry.get("difficulty", 1) + 1),
                            "reason": f"High engagement on {current_topic}. Advancing to related topic.",
                        }

        # ─── Anti-Echo Chamber: Every 4th item is a challenge (from IBLMContext.tsx) ───
        if count % 4 == 0:
            challenge_topic = self._find_challenge_topic(completed, top_interests)
            if challenge_topic:
                return {
                    "recommended_topic": challenge_topic,
                    "content_type": "quiz",
                    "difficulty_level": 2,
                    "reason": "Growth injection: structured challenge on a new topic.",
                }

        # ─── Default: Interest-based recommendation ───
        if top_interests:
            best = top_interests[0]
            graph_entry = TOPIC_GRAPH.get(best["topic"], {})
            next_topics = graph_entry.get("next", [])
            for nt in next_topics:
                if nt not in completed:
                    return {
                        "recommended_topic": nt,
                        "content_type": "lesson",
                        "difficulty_level": graph_entry.get("difficulty", 1),
                        "reason": f"Based on strong interest in {best['topic']}.",
                    }

        # ─── Fallback: Suggest from default topics ───
        for dt in DEFAULT_TOPICS:
            if dt not in completed:
                return {
                    "recommended_topic": dt,
                    "content_type": "lesson",
                    "difficulty_level": 1,
                    "reason": "Starting with a new beginner topic.",
                }

        return {
            "recommended_topic": DEFAULT_TOPICS[0],
            "content_type": "lesson",
            "difficulty_level": 1,
            "reason": "All topics explored. Revisiting for mastery.",
        }

    def _find_challenge_topic(
        self, completed: List[str], interests: List[Dict]
    ) -> Optional[str]:
        """Find a topic the child hasn't explored yet for growth injection."""
        familiar_topics = set(completed)
        interest_topics = {i["topic"] for i in interests}
        all_known = familiar_topics | interest_topics

        for topic in TOPIC_GRAPH:
            if topic not in all_known:
                return topic
        return None
