# KidOS Agentic AI – MVP

> **Edge-Native, Agentic AI learning system for children (ages 5-12)**

Privacy-first, local-only adaptive learning powered by 4 specialized AI agents and Ollama.

## Quick Start

### Backend (Python)

```bash
cd kidOS_mvp
pip install -r requirements.txt
cp .env.example .env
python -m backend.main
# → http://localhost:8000/docs
```

### Frontend (React Native)

```bash
cd kidOS_mvp/frontend
npm install
npx expo start
```

### Ollama (Local LLM)

```bash
# Install from https://ollama.com
ollama pull llama3.2:3b
ollama serve
```

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    KIDOS AGENTIC SYSTEM                        │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │   Observer    │────▶│ Orchestrator │────▶│  Specialist  │   │
│  │    Agent      │     │    Agent     │     │    Agents    │   │
│  └──────────────┘     └──────────────┘     └──────────────┘   │
│         │                    │                    │            │
│         ▼                    ▼                    ▼            │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │  Engagement   │     │   Routing    │     │  Teaching /  │   │
│  │  Tracker      │     │   Logic     │     │  Recommender │   │
│  └──────────────┘     └──────────────┘     └──────────────┘   │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           SQLite + ChromaDB (Child Profile)             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## API Endpoints

> [!IMPORTANT]
> When testing on a physical mobile device or Android emulator, replace `localhost` in `kidOS_mvp/frontend/services/api.ts` with your computer's local network IP (e.g., `192.168.1.x`).

| Method | Endpoint                | Purpose                                           |
| ------ | ----------------------- | ------------------------------------------------- |
| POST   | `/api/v1/telemetry`     | Send interaction data → get engagement assessment |
| POST   | `/api/v1/generate`      | Generate lesson (SSE streaming)                   |
| POST   | `/api/v1/recommend`     | Get next content recommendation                   |
| POST   | `/api/v1/session/start` | Initialize learning session                       |
| POST   | `/api/v1/session/end`   | Close session & save progress                     |

## Tech Stack

- **Backend:** FastAPI, Python 3.10+, Ollama, ChromaDB, SQLite
- **Frontend:** React Native (Expo), Zustand, TypeScript
- **LLM:** Llama 3.2-3B (local via Ollama)

## Tests

```bash
cd kidOS_mvp
python -m pytest tests/ -v
```
