/**
 * KidOS MVP - API Service
 * ========================
 * Client for all 5 backend endpoints.
 * Supports SSE streaming for /generate.
 */

const BASE_URL = "http://localhost:8000/api/v1";

// ─── Types ───

export interface TelemetryPayload {
  child_id: string;
  session_id: string;
  tap_latency_ms: number;
  back_button_count: number;
  scroll_speed: "slow" | "normal" | "fast";
  time_on_task_sec: number;
  error_rate: number;
}

export interface TelemetryResponse {
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
}

export interface GeneratePayload {
  child_id: string;
  topic: string;
  academic_tier?: string;
  mood?: string;
  prompt_modifiers?: Record<string, unknown>;
}

export interface RecommendPayload {
  child_id: string;
  current_topic: string;
}

export interface RecommendResponse {
  recommended_topic: string;
  content_type: string;
  difficulty_level: number;
  reason: string;
}

export interface SessionStartPayload {
  child_id: string;
  preferred_topic?: string;
}

export interface SessionStartResponse {
  session_id: string;
  initial_topic: string;
  academic_tier: string;
  profile_loaded: boolean;
}

export interface SessionEndPayload {
  session_id: string;
  final_engagement_score: number;
  topics_covered: string[];
  completion_rate: number;
}

export interface SessionEndResponse {
  profile_updated: boolean;
  next_recommendation: string;
  streak_days: number;
}

// ─── API Calls ───

async function apiPost<T>(endpoint: string, body: unknown): Promise<T> {
  const resp = await fetch(`${BASE_URL}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    throw new Error(`API error ${resp.status}: ${await resp.text()}`);
  }
  return resp.json() as Promise<T>;
}

/** POST /telemetry → engagement assessment + routing decision */
export async function sendTelemetry(
  payload: TelemetryPayload
): Promise<TelemetryResponse> {
  return apiPost<TelemetryResponse>("/telemetry", payload);
}

/**
 * POST /generate → SSE streaming lesson content.
 * Calls onToken for each text chunk, onComplete when done.
 */
export async function generateLesson(
  payload: GeneratePayload,
  onToken: (token: string) => void,
  onComplete: () => void
): Promise<void> {
  const resp = await fetch(`${BASE_URL}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!resp.ok || !resp.body) {
    throw new Error(`Generate error ${resp.status}`);
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.complete) {
            onComplete();
            return;
          }
          if (data.token) {
            onToken(data.token);
          }
        } catch {
          // Skip malformed lines
        }
      }
    }
  }
  onComplete();
}

/** POST /recommend → next content suggestion */
export async function getRecommendation(
  payload: RecommendPayload
): Promise<RecommendResponse> {
  return apiPost<RecommendResponse>("/recommend", payload);
}

/** POST /session/start → initialize session */
export async function startSession(
  payload: SessionStartPayload
): Promise<SessionStartResponse> {
  return apiPost<SessionStartResponse>("/session/start", payload);
}

/** POST /session/end → close session & save progress */
export async function endSession(
  payload: SessionEndPayload
): Promise<SessionEndResponse> {
  return apiPost<SessionEndResponse>("/session/end", payload);
}

/** GET / → health check */
export async function checkHealth(): Promise<{
  service: string;
  ollama: string;
  model: string;
}> {
  const resp = await fetch(BASE_URL.replace("/api/v1", "/"));
  return resp.json();
}
