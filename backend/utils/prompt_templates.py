"""
KidOS MVP - Dynamic Prompt Templates
=======================================
Builds age-appropriate prompts compiled from Orchestrator modifiers.
From spec's Teaching Specialist prompt template.
"""


def build_teaching_prompt(
    topic: str,
    age: int = 7,
    academic_tier: str = "Level 1",
    mood: str = "neutral",
    tone: str = "neutral",
    vocabulary_level: str = "standard",
    max_syllables: int = 3,
) -> str:
    """Build a dynamic teaching prompt with all modifiers injected."""

    # Vocabulary ceiling mapping
    vocab_ceilings = {
        "simplified": "kindergarten (very simple words only)",
        "standard": "grade 3 (common everyday words)",
        "advanced": "grade 5 (some complex words allowed)",
    }
    vocabulary_ceiling = vocab_ceilings.get(vocabulary_level, vocab_ceilings["standard"])

    # Mood-specific additions
    mood_instructions = ""
    if mood == "frustrated":
        mood_instructions = (
            "- The child seems frustrated. Be extra patient and encouraging.\n"
            "- Start with something they already know to rebuild confidence.\n"
            "- Use lots of praise and positive reinforcement.\n"
        )
    elif mood == "tired":
        mood_instructions = (
            "- The child seems tired. Keep it very short and fun.\n"
            "- Use stories or fun facts instead of direct teaching.\n"
            "- Suggest taking a break if appropriate.\n"
        )
    elif mood == "happy":
        mood_instructions = (
            "- The child is engaged and happy! Challenge them a little.\n"
            "- Ask a fun question to keep their curiosity going.\n"
        )

    prompt = f"""You are teaching a {age}-year-old at {academic_tier} level.
Current mood: {mood}
Topic: {topic}

Rules:
- Max syllables per word: {max_syllables}
- Tone: {tone}
- Never use words above {vocabulary_ceiling}
- Keep sentences short (max 15 words per sentence)
- Use analogies a child would understand (toys, animals, food)
- Include 1-2 fun facts or "Did you know?" moments
{mood_instructions}
Now teach about {topic} in a way that's fun and easy to understand.
Start with a hook that grabs attention (a question, a surprising fact, or a tiny story).
"""
    return prompt


def build_recommendation_context(
    child_id: str,
    completed_topics: list,
    engagement_scores: dict,
    current_mood: str = "neutral",
) -> str:
    """Build context string for recommendation reasoning (optional LLM-based recommendations)."""

    completed_str = ", ".join(completed_topics) if completed_topics else "none yet"
    scores_str = ", ".join(
        f"{t}: {s:.0f}%" for t, s in engagement_scores.items()
    ) if engagement_scores else "no data"

    return f"""Child {child_id} learning profile:
- Completed topics: {completed_str}
- Engagement scores: {scores_str}
- Current mood: {current_mood}

Based on this profile, suggest the next topic and content type.
Prioritize topics adjacent to high-engagement areas.
If engagement was low on last topic, suggest simplifying.
Every 4th suggestion should be a new/challenging topic for growth.
"""
