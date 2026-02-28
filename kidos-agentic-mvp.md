# KidOS Agentic AI – MVP Implementation Plan

> **Project Type:** MOBILE (React Native) + BACKEND (FastAPI/Python)
> **Date:** 2026-02-28
> **Status:** Phase 2 – PLANNING (Approved)

---

## 1. Overview

**What:** Migrate KidOS from a Vite/React web app (Gemini-powered) to a **React Native** mobile app backed by a **local FastAPI server** with 4 specialized AI agents powered by **Ollama (Llama 3.2-3B)**.

**Why:** The current architecture uses a single cloud LLM for everything and hard timers for content switching. The new agentic system introduces real-time engagement monitoring, intelligent routing, adaptive teaching, and personalized recommendations — all running **100% locally** for child privacy.

---

## 2. Success Criteria

| #   | Metric                             | Target | How to Verify                                               |
| --- | ---------------------------------- | ------ | ----------------------------------------------------------- |
| 1   | App launches on Expo/RN            | ✅     | `npx expo start` renders Home screen                        |
| 2   | Backend starts locally             | ✅     | `http://localhost:8000/docs` loads FastAPI docs             |
| 3   | Observer Agent detects frustration | ✅     | Send high-latency telemetry → get `frustration_level: high` |
| 4   | Orchestrator routes correctly      | ✅     | Low engagement → routes to `encouragement_agent`            |
| 5   | Teaching Agent generates lesson    | ✅     | Streaming response with age-appropriate content             |
| 6   | Recommendation Agent works         | ✅     | Completed topics → relevant next suggestion                 |
| 7   | Full session lifecycle             | ✅     | Start → Learn → Telemetry → Switch → End → Recommend        |
| 8   | Ollama inference < 2s TTFT         | ✅     | Timed streaming response                                    |
| 9   | SQLite persistence across sessions | ✅     | Kill app, restart → profile loads                           |

---

## 3. IBLM Code Comparison & Decision

### Existing Code Analysis

| Source                                             | Strengths                                                                                                                                                                                                                                                                                                        | Weaknesses                                                                                                                                                                                                           | Verdict                                                         |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **`IBLM_v2_ProtoAGI_Cognitive_Brain.py`** (Patent) | ✅ 5-class architecture (CognitiveStateEngine, SimulationEngine, CognitiveGovernor, ProfileUpdater, IBLM_V2 Orchestrator). ✅ Models `engagement`, `emotional_stability`, `cognitive_load`, `curiosity_momentum`, `trust_level`. ✅ Predictive simulation before authorizing AI output. ✅ 3-layer safety check. | ❌ Designed for general-purpose cognitive governance, not children-specific. ❌ No telemetry input format (uses `InteractionSignal` with `duration_ms`, `success`, `retries`). ❌ No HTTP API / FastAPI integration. | **HYBRID: Reuse cognitive state math**                          |
| **`iblm_core.py`** (Patent)                        | ✅ Simple `CognitiveEngine.update()` + `get_policy()`. ✅ Clean state transitions.                                                                                                                                                                                                                               | ❌ Too simple for 4-agent system. ❌ Uses response_latency_ms (adult chat), not touch/scroll telemetry.                                                                                                              | **Reuse: `_clamp()`, state transition pattern**                 |
| **`iblm_proxy.py`** (Patent)                       | ✅ FastAPI server with `/chat` endpoint. ✅ Multi-provider fallback (Gemini → OpenAI → Ollama). ✅ Cognitive steering prompt generation.                                                                                                                                                                         | ❌ Not agent-based architecture. ❌ Single endpoint, not the 5-endpoint spec.                                                                                                                                        | **Reuse: Ollama client code, FastAPI structure**                |
| **`IBLMContext.tsx`** (Current Web)                | ✅ React context with IBLM metrics. ✅ Dormant session filter, STV decay, mastery tracking. ✅ Anti-echo chamber (3:1 rule).                                                                                                                                                                                     | ❌ All logic runs client-side. ❌ Uses browser `localStorage`.                                                                                                                                                       | **Port: ContentMode logic, mastery tracking to backend agents** |
| **`IBLM-main/` (Full Engine)**                     | ✅ 767-line `IBLM` class with observe/evolve/inject/correct/teach. ✅ 1477-line `UserKernel` with graph-vector hybrid storage. ✅ 782-line `InteractionObserver` with signal extraction.                                                                                                                         | ❌ Designed for adult developer workflows (code review, text analysis). ❌ Massive—over-engineered for MVP.                                                                                                          | **Reference only. Too complex for MVP.**                        |
| **Spec: Scratch Agents**                           | ✅ Simple rule-based logic for MVP. ✅ Exactly matches the 4-agent architecture. ✅ Child-specific telemetry (tap_latency, back_button, scroll_speed).                                                                                                                                                           | ❌ Needs to be built from scratch.                                                                                                                                                                                   | **Primary approach**                                            |

### ✅ DECISION: Hybrid Approach

**Build agents from scratch per the spec**, but:

1. **Reuse** `CognitiveStateEngine.update_state()` math from `IBLM_v2` for the Observer Agent's engagement calculation (it already models engagement, cognitive load, trust).
2. **Reuse** `iblm_proxy.py`'s Ollama client code and FastAPI structure.
3. **Port** `IBLMContext.tsx`'s mastery tracking, STV decay, and anti-echo chamber logic into the Recommendation Agent.
4. **Reference** `CognitiveGovernor.authorize()` for the Orchestrator's safety checks.

---

## 4. Tech Stack

### Backend (Python)

| Component     | Technology                   | Rationale                                                                        |
| ------------- | ---------------------------- | -------------------------------------------------------------------------------- |
| API Framework | **FastAPI 0.104+**           | Spec requirement. Already proven in `iblm_proxy.py`.                             |
| LLM Runtime   | **Ollama**                   | Spec requirement. Local-first privacy.                                           |
| Model         | **Llama 3.2-3B** (quantized) | Spec requirement. Fits in 4GB RAM.                                               |
| Vector Store  | **ChromaDB**                 | Better Python API than SQLite-VSS. Runs in-process (no Docker). MVP-sustainable. |
| Database      | **SQLite**                   | Profiles, sessions, interactions. Lightweight, file-based.                       |
| State         | **JSON file**                | Simpler than Redis for localhost MVP.                                            |

### Frontend (React Native)

| Component  | Technology                   | Rationale                                              |
| ---------- | ---------------------------- | ------------------------------------------------------ |
| Framework  | **Expo (React Native)**      | Cross-platform, fast setup, expo-go for quick testing. |
| State      | **Zustand**                  | Lightweight, simple API, spec-compatible.              |
| Telemetry  | **Custom Hooks**             | `useTelemetry.ts` for capturing touch, dwell, scroll.  |
| Streaming  | **Server-Sent Events (SSE)** | Spec requirement for `/generate` streaming.            |
| Navigation | **Expo Router**              | File-based routing, clean structure.                   |

---

## 5. File Structure

```
kidOS_mvp/
├── backend/
│   ├── main.py                          # FastAPI entry point
│   ├── config.py                        # Environment variables & constants
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── observer.py                  # Engagement tracking (reuses IBLM_v2 math)
│   │   ├── orchestrator.py              # Routing logic (reuses Governor safety)
│   │   ├── teaching_specialist.py       # Lesson generation
│   │   └── recommender.py              # Content suggestions (ports IBLMContext logic)
│   ├── models/
│   │   ├── __init__.py
│   │   └── ollama_client.py             # LLM interface (reuses iblm_proxy.py code)
│   ├── database/
│   │   ├── __init__.py
│   │   ├── sqlite_store.py              # SQLite for profiles + sessions
│   │   ├── vector_store.py              # ChromaDB for behavioral embeddings
│   │   └── schema.sql                   # DB schema
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── telemetry.py                 # Pydantic models
│   │   └── responses.py                 # API response models
│   └── utils/
│       ├── __init__.py
│       └── prompt_templates.py          # Dynamic prompts
├── frontend/
│   ├── app/                             # Expo Router pages
│   │   ├── _layout.tsx                  # Root layout
│   │   ├── index.tsx                    # Welcome/Home screen
│   │   ├── feed.tsx                     # Discovery feed
│   │   ├── learn.tsx                    # Active lesson screen
│   │   ├── games.tsx                    # Games hub
│   │   └── parent.tsx                   # Parent zone (PIN-gated)
│   ├── components/                      # Shared UI components
│   │   ├── LessonCard.tsx
│   │   ├── EngagementIndicator.tsx
│   │   └── NavigationBar.tsx
│   ├── hooks/
│   │   ├── useTelemetry.ts              # Touch/scroll/dwell capture
│   │   └── useSession.ts               # Session lifecycle
│   ├── services/
│   │   └── api.ts                       # Backend API calls + SSE
│   ├── stores/
│   │   └── sessionStore.ts              # Zustand state
│   ├── app.json                         # Expo config
│   └── package.json
├── tests/
│   ├── test_observer.py
│   ├── test_orchestrator.py
│   ├── test_recommender.py
│   └── test_api.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## 6. Task Breakdown

### Phase 1: Foundation (Backend Core) 🔴 HIGH PRIORITY

> **Agent:** `backend-specialist`
> **Skills:** `python-patterns`, `api-patterns`, `database-design`

#### Task 1.1: Project Scaffolding

- **INPUT:** Spec file structure + requirements
- **OUTPUT:** `kidOS_mvp/backend/` directory with `main.py`, `config.py`, `requirements.txt`, all `__init__.py` files
- **VERIFY:** `pip install -r requirements.txt` succeeds; `python main.py` starts FastAPI on port 8000
- **Priority:** P0
- **Dependencies:** None
- [ ] Complete

#### Task 1.2: Database Schema & SQLite Store

- **INPUT:** Schema from spec (5 tables: child_profiles, sessions, content_interactions, behavioral_embeddings, recommendations)
- **OUTPUT:** `database/schema.sql` + `database/sqlite_store.py` with CRUD operations
- **VERIFY:** Unit test creates DB, inserts profile, queries session history
- **Priority:** P0
- **Dependencies:** Task 1.1
- [ ] Complete

#### Task 1.3: ChromaDB Vector Store Setup

- **INPUT:** ChromaDB dependency + behavioral embedding requirements
- **OUTPUT:** `database/vector_store.py` with `store_embedding()`, `query_similar()`, `get_child_history()`
- **VERIFY:** Store 3 embeddings, query by similarity, get top-K results
- **Priority:** P0
- **Dependencies:** Task 1.1
- [ ] Complete

#### Task 1.4: Pydantic Schemas

- **INPUT:** API request/response specs from doc
- **OUTPUT:** `schemas/telemetry.py` + `schemas/responses.py` with all models
- **VERIFY:** Pydantic validation works for sample payloads; invalid data raises `ValidationError`
- **Priority:** P0
- **Dependencies:** Task 1.1
- [ ] Complete

#### Task 1.5: Ollama Client

- **INPUT:** `iblm_proxy.py` Ollama code + spec requirements
- **OUTPUT:** `models/ollama_client.py` with `generate()` (streaming), `generate_sync()`, `check_health()`, `list_models()`
- **VERIFY:** Health check returns model list; generate returns streamed tokens (or mock if Ollama offline)
- **Priority:** P0
- **Dependencies:** Task 1.1
- [ ] Complete

---

### Phase 2: Agent Implementation 🔴 HIGH PRIORITY

> **Agent:** `backend-specialist`
> **Skills:** `python-patterns`, `clean-code`

#### Task 2.1: Observer Agent

- **INPUT:** Spec Observer logic + `IBLM_v2` `CognitiveStateEngine.update_state()` math
- **OUTPUT:** `agents/observer.py` with `ObserverAgent.analyze()` returning `engagement_score`, `mood`, `frustration_level`, `recommended_action`
- **VERIFY:** `test_observer.py` — high latency + back buttons → frustration HIGH; low latency + low errors → engagement HIGH
- **Priority:** P0
- **Dependencies:** Task 1.4
- **Reuses from:** `IBLM_v2_ProtoAGI_Cognitive_Brain.py` → `CognitiveStateEngine.update_state()` engagement/cognitive_load formulas
- [ ] Complete

#### Task 2.2: Orchestrator Agent

- **INPUT:** Spec decision tree + `CognitiveGovernor.authorize()` safety pattern
- **OUTPUT:** `agents/orchestrator.py` with `OrchestratorAgent.decide()` returning `next_action`, `agent_to_route`, `prompt_modifiers`
- **VERIFY:** `test_orchestrator.py` — engagement < 40 → routes to encouragement; session > 10min + high engagement → routes to recommender
- **Priority:** P0
- **Dependencies:** Task 2.1
- **Reuses from:** `IBLM_v2` → `CognitiveGovernor.authorize()` risk threshold pattern
- [ ] Complete

#### Task 2.3: Teaching Specialist Agent

- **INPUT:** Spec prompt template + Ollama client
- **OUTPUT:** `agents/teaching_specialist.py` with `TeachingAgent.generate_lesson()` (streaming)
- **VERIFY:** Generates age-appropriate content; prompt includes modifiers from Orchestrator; streaming works
- **Priority:** P1
- **Dependencies:** Task 1.5, Task 2.2
- [ ] Complete

#### Task 2.4: Recommendation Agent

- **INPUT:** Spec recommendation logic + `IBLMContext.tsx` mastery/STV/anti-echo-chamber code
- **OUTPUT:** `agents/recommender.py` with `RecommenderAgent.suggest()` returning `recommended_topic`, `content_type`, `difficulty_level`, `reason`
- **VERIFY:** `test_recommender.py` — completed topic + high engagement → related harder topic; low engagement → same topic simplified
- **Priority:** P1
- **Dependencies:** Task 1.2, Task 1.3
- **Ports from:** `IBLMContext.tsx` → `decideNextContent()`, STV decay, anti-echo-chamber (3:1 rule), mastery tracking
- [ ] Complete

#### Task 2.5: Prompt Templates

- **INPUT:** Teaching prompt template from spec
- **OUTPUT:** `utils/prompt_templates.py` with `build_teaching_prompt()`, `build_recommendation_context()`
- **VERIFY:** Prompt includes age, academic tier, mood, vocabulary ceiling, syllable limit
- **Priority:** P1
- **Dependencies:** Task 2.2
- [ ] Complete

---

### Phase 3: API Endpoints 🔴 HIGH PRIORITY

> **Agent:** `backend-specialist`
> **Skills:** `api-patterns`, `python-patterns`

#### Task 3.1: POST /telemetry

- **INPUT:** Observer + Orchestrator agents
- **OUTPUT:** Endpoint wired up: telemetry → Observer → Orchestrator → response
- **VERIFY:** Postman: send telemetry JSON → get `engagement_score` + `next_action`
- **Priority:** P0
- **Dependencies:** Task 2.1, Task 2.2
- [ ] Complete

#### Task 3.2: POST /generate

- **INPUT:** Teaching Agent + Ollama client
- **OUTPUT:** SSE streaming endpoint: orchestrator decision → teaching prompt → streamed tokens
- **VERIFY:** `curl` or Postman: send topic → receive streaming tokens
- **Priority:** P0
- **Dependencies:** Task 2.3, Task 1.5
- [ ] Complete

#### Task 3.3: GET /recommend

- **INPUT:** Recommendation Agent + vector store
- **OUTPUT:** Endpoint returns personalized content suggestion
- **VERIFY:** Send child_id → get topic recommendation with reason
- **Priority:** P1
- **Dependencies:** Task 2.4
- [ ] Complete

#### Task 3.4: POST /session/start & /session/end

- **INPUT:** SQLite store + profile loading
- **OUTPUT:** Session lifecycle endpoints; creates/loads profile; saves progress on end
- **VERIFY:** Start session → get session_id; end session → profile_updated: true
- **Priority:** P1
- **Dependencies:** Task 1.2
- [ ] Complete

---

### Phase 4: Frontend (React Native) 🟡 MEDIUM PRIORITY

> **Agent:** `mobile-developer`
> **Skills:** `mobile-design`

#### Task 4.1: Expo Project Scaffolding

- **INPUT:** Expo + TypeScript + Expo Router
- **OUTPUT:** `kidOS_mvp/frontend/` with working Expo app, navigation, and basic screens
- **VERIFY:** `npx expo start` → app renders on simulator/Expo Go
- **Priority:** P0
- **Dependencies:** None (can run parallel to Phase 1)
- [ ] Complete

#### Task 4.2: API Service Layer

- **INPUT:** Backend API spec (5 endpoints)
- **OUTPUT:** `services/api.ts` with `sendTelemetry()`, `generateLesson()` (SSE), `getRecommendation()`, `startSession()`, `endSession()`
- **VERIFY:** TypeScript compiles; functions match API contract
- **Priority:** P0
- **Dependencies:** Task 4.1
- [ ] Complete

#### Task 4.3: Telemetry Hook

- **INPUT:** Spec telemetry fields (tap_latency, back_button, scroll_speed, time_on_task, error_rate)
- **OUTPUT:** `hooks/useTelemetry.ts` capturing touch events, scroll speed, time on screen; sends to `/telemetry` every 30s
- **VERIFY:** Console logs telemetry payload every 30s during interaction
- **Priority:** P0
- **Dependencies:** Task 4.2
- [ ] Complete

#### Task 4.4: Session Store (Zustand)

- **INPUT:** Session state requirements
- **OUTPUT:** `stores/sessionStore.ts` with `childId`, `sessionId`, `engagementScore`, `currentTopic`, `contentMode`
- **VERIFY:** State updates reactively; persists session info
- **Priority:** P1
- **Dependencies:** Task 4.1
- [ ] Complete

#### Task 4.5: Core Screens

- **INPUT:** Current web components (Feed, LearnTV, Games, ChatBuddy, ParentZone) + new agentic data flow
- **OUTPUT:** RN screens: Home/Feed, Active Lesson (streaming), Games Hub, Parent Zone
- **VERIFY:** Navigation works; lesson screen streams content from backend
- **Priority:** P1
- **Dependencies:** Task 4.2, Task 4.3, Task 4.4
- [ ] Complete

#### Task 4.6: Engagement Indicator UI

- **INPUT:** Observer Agent output (engagement_score, mood, frustration)
- **OUTPUT:** Visual indicator component showing child's engagement state (for parent/debug mode)
- **VERIFY:** UI updates in real-time as telemetry flows
- **Priority:** P2
- **Dependencies:** Task 4.3
- [ ] Complete

---

### Phase 5: Integration & Testing 🟡 MEDIUM PRIORITY

> **Agent:** `test-engineer`
> **Skills:** `testing-patterns`

#### Task 5.1: Unit Tests (Backend)

- **INPUT:** All 4 agents
- **OUTPUT:** `tests/test_observer.py`, `test_orchestrator.py`, `test_recommender.py`, `test_api.py`
- **VERIFY:** `pytest tests/` — all pass
- **Priority:** P0
- **Dependencies:** Phase 2 complete
- [ ] Complete

#### Task 5.2: Integration Test – Full Session Lifecycle

- **INPUT:** All endpoints + agents
- **OUTPUT:** Test: start_session → telemetry (3x) → generate → recommend → end_session
- **VERIFY:** Full flow runs end-to-end locally
- **Priority:** P0
- **Dependencies:** Phase 3 complete
- [ ] Complete

#### Task 5.3: Ollama Offline Fallback Test

- **INPUT:** Ollama client with mock mode
- **OUTPUT:** Test: when Ollama is offline, system returns mock responses gracefully
- **VERIFY:** No crashes; user-friendly fallback messages
- **Priority:** P1
- **Dependencies:** Task 1.5
- [ ] Complete

---

## 7. Implementation Order (Critical Path)

```
Phase 1 (Foundation)     Phase 2 (Agents)        Phase 3 (API)         Phase 4 (Frontend)
┌─────────────────┐     ┌────────────────┐      ┌──────────────┐      ┌──────────────┐
│ 1.1 Scaffolding  │────▶│ 2.1 Observer   │─────▶│ 3.1 /telemetry│     │ 4.1 Expo Init│
│ 1.2 SQLite       │     │ 2.2 Orchestrate│─────▶│ 3.2 /generate │     │ 4.2 API Layer│
│ 1.3 ChromaDB     │     │ 2.3 Teaching   │      │ 3.3 /recommend│     │ 4.3 Telemetry│
│ 1.4 Schemas      │     │ 2.4 Recommender│      │ 3.4 /session  │     │ 4.4 Zustand  │
│ 1.5 Ollama Client│     │ 2.5 Prompts    │      └──────────────┘     │ 4.5 Screens  │
└─────────────────┘     └────────────────┘                            └──────────────┘
       │                                                                    │
       │                    Phase 5 (Testing)                               │
       │                   ┌──────────────────┐                             │
       └──────────────────▶│ 5.1 Unit Tests   │◀────────────────────────────┘
                           │ 5.2 Integration  │
                           │ 5.3 Fallback     │
                           └──────────────────┘
```

> **Parallel Work:** Phase 4 (Frontend) Tasks 4.1–4.4 can run in parallel with Phase 1–3 (Backend).

---

## 8. MVP Warnings (from Spec)

- ❌ **DON'T:** Build complex ML models → ✅ **DO:** Rule-based logic first
- ❌ **DON'T:** Make all agents fully autonomous → ✅ **DO:** Orchestrator stays in control
- ❌ **DON'T:** Store everything in cloud → ✅ **DO:** PII local, sync only learning progress
- ❌ **DON'T:** Over-engineer recommendations → ✅ **DO:** if-this-then-that rules
- ❌ **DON'T:** Build all 4 agents at once → ✅ **DO:** Observer + Orchestrator first (Tasks 2.1, 2.2), then Teaching + Recommender (Tasks 2.3, 2.4)

---

## 9. Risk Registry

| Risk                                | Likelihood | Impact | Mitigation                                                                 |
| ----------------------------------- | ---------- | ------ | -------------------------------------------------------------------------- |
| Ollama not installed on dev machine | High       | Medium | Mock mode in `ollama_client.py`; push to friend's machine                  |
| Llama 3.2-3B too slow on CPU        | Medium     | High   | Use quantized model (Q4_K_M); fallback to gemma:2b                         |
| React Native telemetry accuracy     | Medium     | Medium | Start with simple tap + time tracking; enhance later                       |
| ChromaDB embedding quality          | Low        | Low    | Use simple text embeddings for MVP; upgrade to sentence-transformers later |

---

## Phase X: Verification Checklist

- [ ] `pip install -r requirements.txt` → No errors
- [ ] `python backend/main.py` → FastAPI starts on :8000
- [ ] `npx expo start` → RN app loads
- [ ] `pytest tests/` → All unit tests pass
- [ ] Full session lifecycle test passes
- [ ] Ollama offline fallback works gracefully
- [ ] SQLite DB persists across restarts
- [ ] Streaming lesson generation works end-to-end
