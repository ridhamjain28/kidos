"""
KidOS MVP - Ollama Client
===========================
LLM interface for local inference via Ollama.
Supports streaming and sync generation with automatic fallback.
Adapted from IBLM proxy's multi-provider pattern.
"""

import httpx
import json
from typing import AsyncGenerator, Optional, List, Dict, Any

from backend.config import OLLAMA_HOST, OLLAMA_MODEL


class OllamaClient:
    """Async client for Ollama local LLM inference."""

    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.host = host.rstrip("/")
        self.model = model
        self._available_models: List[str] = []

    async def check_health(self) -> Dict[str, Any]:
        """Check if Ollama is running and which models are available."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.host}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    self._available_models = [m["name"] for m in data.get("models", [])]
                    model_available = any(self.model in m for m in self._available_models)
                    return {
                        "status": "online",
                        "models": self._available_models,
                        "target_model": self.model,
                        "target_available": model_available,
                    }
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        return {
            "status": "offline",
            "models": [],
            "target_model": self.model,
            "target_available": False,
        }

    def _resolve_model(self) -> str:
        """Find the best available model matching our target."""
        if not self._available_models:
            return self.model
        for m in self._available_models:
            if self.model in m:
                return m
        # Fallback to first available model
        return self._available_models[0] if self._available_models else self.model

    async def generate_stream(
        self, prompt: str, system: str = "", temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama. Yields individual text chunks."""
        model = self._resolve_model()
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST", f"{self.host}/api/generate", json=payload
                ) as response:
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        token = chunk.get("response", "")
                        if token:
                            yield token
                        if chunk.get("done", False):
                            return
        except (httpx.ConnectError, httpx.TimeoutException):
            yield "[Ollama offline] Install Ollama and run: ollama pull " + self.model

    async def generate_sync(
        self, prompt: str, system: str = "", temperature: float = 0.7
    ) -> str:
        """Generate a complete response (non-streaming)."""
        model = self._resolve_model()
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{self.host}/api/generate", json=payload)
                if resp.status_code == 200:
                    return resp.json().get("response", "")
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        return f"[Ollama offline] Mock response for: {prompt[:100]}..."

    async def list_models(self) -> List[str]:
        """List all available models."""
        health = await self.check_health()
        return health["models"]


# Singleton instance
ollama_client = OllamaClient()
