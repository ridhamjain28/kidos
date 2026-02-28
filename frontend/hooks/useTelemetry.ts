/**
 * KidOS MVP - Telemetry Hook
 * ============================
 * Captures touch interactions, scroll speed, dwell time,
 * and sends to /telemetry every 30 seconds.
 */

import { useEffect, useRef, useCallback } from "react";
import { sendTelemetry, TelemetryResponse } from "../services/api";
import { useSessionStore } from "../stores/sessionStore";

const TELEMETRY_INTERVAL_MS = 30_000;

interface TelemetryMetrics {
  tapLatencies: number[];
  backButtonCount: number;
  scrollSpeed: "slow" | "normal" | "fast";
  taskStartTime: number;
  errorCount: number;
  totalAttempts: number;
}

export function useTelemetry(onUpdate?: (data: TelemetryResponse) => void) {
  const metricsRef = useRef<TelemetryMetrics>({
    tapLatencies: [],
    backButtonCount: 0,
    scrollSpeed: "normal",
    taskStartTime: Date.now(),
    errorCount: 0,
    totalAttempts: 0,
  });

  const { childId, sessionId } = useSessionStore();
  const lastTapTime = useRef<number>(0);

  /** Record a tap event (captures latency between taps) */
  const recordTap = useCallback(() => {
    const now = Date.now();
    if (lastTapTime.current > 0) {
      const latency = now - lastTapTime.current;
      metricsRef.current.tapLatencies.push(latency);
      // Keep only last 20 latencies
      if (metricsRef.current.tapLatencies.length > 20) {
        metricsRef.current.tapLatencies.shift();
      }
    }
    lastTapTime.current = now;
  }, []);

  /** Record a back button press */
  const recordBackPress = useCallback(() => {
    metricsRef.current.backButtonCount++;
  }, []);

  /** Record scroll speed observation */
  const recordScroll = useCallback(
    (speed: "slow" | "normal" | "fast") => {
      metricsRef.current.scrollSpeed = speed;
    },
    []
  );

  /** Record an error (wrong answer, failed interaction) */
  const recordError = useCallback(() => {
    metricsRef.current.errorCount++;
    metricsRef.current.totalAttempts++;
  }, []);

  /** Record a success */
  const recordSuccess = useCallback(() => {
    metricsRef.current.totalAttempts++;
  }, []);

  /** Reset metrics for a new task */
  const resetForNewTask = useCallback(() => {
    metricsRef.current = {
      tapLatencies: [],
      backButtonCount: 0,
      scrollSpeed: "normal",
      taskStartTime: Date.now(),
      errorCount: 0,
      totalAttempts: 0,
    };
    lastTapTime.current = 0;
  }, []);

  // Auto-send telemetry every 30 seconds
  useEffect(() => {
    if (!childId || !sessionId) return;

    const interval = setInterval(async () => {
      const m = metricsRef.current;

      // Calculate averages
      const avgLatency =
        m.tapLatencies.length > 0
          ? Math.round(
              m.tapLatencies.reduce((a, b) => a + b, 0) /
                m.tapLatencies.length
            )
          : 300; // default

      const errorRate =
        m.totalAttempts > 0 ? m.errorCount / m.totalAttempts : 0;

      const timeOnTask = Math.round((Date.now() - m.taskStartTime) / 1000);

      try {
        const response = await sendTelemetry({
          child_id: childId,
          session_id: sessionId,
          tap_latency_ms: avgLatency,
          back_button_count: m.backButtonCount,
          scroll_speed: m.scrollSpeed,
          time_on_task_sec: timeOnTask,
          error_rate: Math.round(errorRate * 100) / 100,
        });

        // Reset per-interval counters
        m.backButtonCount = 0;

        if (onUpdate) {
          onUpdate(response);
        }
      } catch (err) {
        console.warn("[Telemetry] Failed to send:", err);
      }
    }, TELEMETRY_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [childId, sessionId, onUpdate]);

  return {
    recordTap,
    recordBackPress,
    recordScroll,
    recordError,
    recordSuccess,
    resetForNewTask,
  };
}
