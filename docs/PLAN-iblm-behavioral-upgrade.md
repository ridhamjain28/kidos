# PLAN: IBLM Behavioral Upgrade (KidOS MVP)

## 📌 1. Strategic Objective
Transition the existing IBLM from "Engagement-based personalization" to a "Growth-aware adaptive learning engine" for the upcoming 25-day pitch.

## 🏗️ 2. Architecture Overview
- **State Separation**: Refactor `IBLMContext` to maintain two independent state buckets: `STV` (Curiosity/Session) and `LMV` (Mastery/Persistence).
- **Signal Filter**: Intercept `startInteraction` and `endInteraction` calls with an "Intent Filter" that rejects noise.
- **Scheduler**: Wrap the existing recommendation engine with a "3:1 Growth Guard" that forces a difficulty jump every 4 items.

## 📊 3. Data Model (Local-First)
### A. Short-Term Context Vector (STV)
- **Storage**: `sessionStorage` (auto-resets) + `localStorage` for 7-day decay.
- **Decay Formula**: `Weight = InitialWeight * (0.5 ^ (DaysPassed))`.
- **Reset**: 100% flush after 7 days of inactivity.

### B. Long-Term Mastery Vector (LMV)
- **Storage**: `localStorage['iblm_mastery']`.
- **Structure**: `{ "topic_id": { "level": 1, "score": 85, "attempts": 12 } }`.
- **Sync**: Batch update to SQLite (via `IBLM-main` Python logic if connected) every 5 interactions.

### C. Content Difficulty (Tier 1-3)
- **Level 1 (Comfort)**: Matches current LMV.
- **Level 2 (Stretch)**: LMV + 1.
- **Level 3 (Cognitive Leap)**: LMV + 2 (rarely served in MVP).

## 🚀 4. Implementation Phases

### Phase 1: Noise Control (Frontend Hooks)
1. **Idle Monitor**: Use a redundant timer in `App.tsx` or `IBLMContext`.
   - `lastActivity` timestamp updated on `mousemove`, `touchstart`, `click`.
   - If `Date.now() - lastActivity > 30s` → `isDormant = true`.
2. **Signal Gate**: Modify `endInteraction` to check `isDormant` and `duration`.
   - Reject signals if `duration < 3s` or `isDormant == true`.

### Phase 2: Dual-State Core (Context Refactor)
1. Split `metrics` in `IBLMContext.tsx` into `sessionMetrics` (STV) and `masteryMetrics` (LMV).
2. Implement **Recency Weighing** for STV updates.
3. Add `updateMastery(topic, quizScore)` function.

### Phase 3: Growth Injection (Ranking Guard)
1. Update `decideNextContent` to track a session counter (`itemsServedCount`).
2. If `itemsServedCount % 4 === 0`, return `ContentRecommendation` with `difficulty: Level + 1`.

### Phase 4: Feedback Loop (Micro-Quizzes)
1. Create a `QuizOverlay` component in `CreativeStudio`.
2. Trigger it automatically when a "Challenge" content piece (Level 2) is completed.
3. Hook quiz results directly into `updateMastery`.

## ✅ 5. Verification Checklist
- [ ] **Stress Test**: Leave app open for 60s; verify no background points are added.
- [ ] **Decay Test**: Mock system time +24h; verify STV weights dropped by 50%.
- [ ] **Growth Test**: Scroll through Feed; verify every 4th item is a "Stretch" topic.
- [ ] **Pitch Stability**: Ensure local fallbacks work if Gemini API is disconnected.

---
*Created by @project-planner*
