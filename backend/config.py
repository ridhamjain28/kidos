"""
KidOS MVP - Configuration
=========================
Central configuration loaded from environment variables with sane defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# Server
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "kidos.db"))
CHROMA_PATH = os.getenv("CHROMA_PATH", str(DATA_DIR / "chroma"))

# Agent Thresholds (from spec)
ENGAGEMENT_LOW_THRESHOLD = 40
ENGAGEMENT_HIGH_THRESHOLD = 70
SESSION_SWITCH_MINUTES = 10
TELEMETRY_INTERVAL_SEC = 30

# Teaching Defaults
DEFAULT_AGE_RANGE = (5, 12)
DEFAULT_SYLLABLE_LIMIT = 3
DEFAULT_VOCABULARY_CEILING = "grade_3"

# Observer Thresholds (from spec)
TAP_LATENCY_HIGH_MS = 500
TAP_LATENCY_LOW_MS = 200
BACK_BUTTON_FRUSTRATION_THRESHOLD = 3
ERROR_RATE_LOW = 0.2
