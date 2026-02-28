"""
KidOS MVP - Teaching Specialist Agent 📚
==========================================
Generates age-appropriate, adaptive lessons using Ollama.
Uses dynamic prompt templates compiled from Orchestrator modifiers.
"""

from typing import AsyncGenerator, Dict, Any

from backend.models.ollama_client import ollama_client
from backend.utils.prompt_templates import build_teaching_prompt


class TeachingSpecialistAgent:
    """Generates personalized lesson content via local LLM."""

    async def generate_lesson(
        self,
        topic: str,
        age: int = 7,
        academic_tier: str = "Level 1",
        mood: str = "neutral",
        prompt_modifiers: Dict[str, Any] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a personalized lesson for the child.

        Args:
            topic: Lesson topic (e.g. "gravity", "planets")
            age: Child's age
            academic_tier: Level 1, 2, or 3
            mood: Current mood state from Observer
            prompt_modifiers: Tone/vocabulary overrides from Orchestrator

        Yields:
            Individual text tokens for streaming to the frontend.
        """
        modifiers = prompt_modifiers or {}
        prompt = build_teaching_prompt(
            topic=topic,
            age=age,
            academic_tier=academic_tier,
            mood=mood,
            tone=modifiers.get("tone", "neutral"),
            vocabulary_level=modifiers.get("vocabulary_level", "standard"),
            max_syllables=modifiers.get("max_syllables", 3),
        )

        system = (
            "You are a friendly, expert teacher for children. "
            "You make learning fun and engaging. "
            "Never use scary, violent, or inappropriate content. "
            "Always be encouraging and positive."
        )

        async for token in ollama_client.generate_stream(
            prompt=prompt, system=system, temperature=0.7
        ):
            yield token

    async def generate_encouragement(self, topic: str, age: int = 7) -> str:
        """Generate a short encouragement message (non-streaming)."""
        prompt = (
            f"Generate a short (2-3 sentences), encouraging message for a {age}-year-old "
            f"who is learning about {topic}. Be warm, fun, and use simple words. "
            f"Include an emoji or two."
        )
        return await ollama_client.generate_sync(prompt=prompt, temperature=0.8)
