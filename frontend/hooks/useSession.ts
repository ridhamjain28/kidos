/**
 * KidOS MVP - Session Hook
 * ==========================
 * Manages session lifecycle: start, track, end.
 */

import { useCallback } from "react";
import { startSession, endSession } from "../services/api";
import { useSessionStore } from "../stores/sessionStore";

export function useSession() {
  const store = useSessionStore();

  const begin = useCallback(
    async (preferredTopic?: string) => {
      try {
        const resp = await startSession({
          child_id: store.childId,
          preferred_topic: preferredTopic || "",
        });
        store.setSessionId(resp.session_id);
        store.setCurrentTopic(resp.initial_topic);
        store.setAcademicTier(resp.academic_tier);
        return resp;
      } catch (err) {
        console.error("[Session] Start failed:", err);
        return null;
      }
    },
    [store]
  );

  const finish = useCallback(async () => {
    if (!store.sessionId) return null;

    try {
      const resp = await endSession({
        session_id: store.sessionId,
        final_engagement_score: store.engagementScore,
        topics_covered: store.topicsCovered,
        completion_rate: store.completionRate,
      });
      store.clearSession();
      return resp;
    } catch (err) {
      console.error("[Session] End failed:", err);
      return null;
    }
  }, [store]);

  return { begin, finish };
}
