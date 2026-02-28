/**
 * KidOS MVP - Session Store (Zustand)
 * ======================================
 * Global state for active session, engagement, and routing.
 */

import { create } from "zustand";

interface SessionState {
  // Identity
  childId: string;
  sessionId: string;

  // Session Data
  currentTopic: string;
  academicTier: string;
  engagementScore: number;
  mood: string;
  frustrationLevel: string;
  topicsCovered: string[];
  completionRate: number;

  // Routing (from Orchestrator)
  nextAction: string;
  agentRouted: string;
  promptModifiers: {
    tone: string;
    vocabulary_level: string;
    max_syllables: number;
  };

  // UI state
  isLessonStreaming: boolean;
  streamedContent: string;

  // Actions
  setChildId: (id: string) => void;
  setSessionId: (id: string) => void;
  setCurrentTopic: (topic: string) => void;
  setAcademicTier: (tier: string) => void;
  updateEngagement: (data: {
    engagement_score: number;
    mood: string;
    frustration_level: string;
    next_action: string;
    agent_routed: string;
    prompt_modifiers: {
      tone: string;
      vocabulary_level: string;
      max_syllables: number;
    };
  }) => void;
  addTopic: (topic: string) => void;
  setStreaming: (streaming: boolean) => void;
  appendContent: (token: string) => void;
  clearContent: () => void;
  clearSession: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  // Defaults
  childId: "child-default-001",
  sessionId: "",
  currentTopic: "",
  academicTier: "Level 1",
  engagementScore: 50,
  mood: "neutral",
  frustrationLevel: "low",
  topicsCovered: [],
  completionRate: 0,
  nextAction: "continue_lesson",
  agentRouted: "standard_teaching_agent",
  promptModifiers: {
    tone: "neutral",
    vocabulary_level: "standard",
    max_syllables: 3,
  },
  isLessonStreaming: false,
  streamedContent: "",

  // Actions
  setChildId: (id) => set({ childId: id }),
  setSessionId: (id) => set({ sessionId: id }),
  setCurrentTopic: (topic) =>
    set((s) => ({
      currentTopic: topic,
      topicsCovered: s.topicsCovered.includes(topic)
        ? s.topicsCovered
        : [...s.topicsCovered, topic],
    })),
  setAcademicTier: (tier) => set({ academicTier: tier }),

  updateEngagement: (data) =>
    set({
      engagementScore: data.engagement_score,
      mood: data.mood,
      frustrationLevel: data.frustration_level,
      nextAction: data.next_action,
      agentRouted: data.agent_routed,
      promptModifiers: data.prompt_modifiers,
    }),

  addTopic: (topic) =>
    set((s) => ({
      topicsCovered: s.topicsCovered.includes(topic)
        ? s.topicsCovered
        : [...s.topicsCovered, topic],
    })),

  setStreaming: (streaming) => set({ isLessonStreaming: streaming }),
  appendContent: (token) =>
    set((s) => ({ streamedContent: s.streamedContent + token })),
  clearContent: () => set({ streamedContent: "", isLessonStreaming: false }),

  clearSession: () =>
    set({
      sessionId: "",
      currentTopic: "",
      topicsCovered: [],
      completionRate: 0,
      engagementScore: 50,
      mood: "neutral",
      frustrationLevel: "low",
      streamedContent: "",
      isLessonStreaming: false,
    }),
}));
