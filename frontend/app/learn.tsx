/**
 * KidOS MVP - Active Lesson Screen
 * ===================================
 * Streams lesson content from the Teaching Agent via SSE.
 * Sends telemetry and shows engagement state.
 */

import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useSessionStore } from "../stores/sessionStore";
import { useTelemetry } from "../hooks/useTelemetry";
import { generateLesson, getRecommendation } from "../services/api";

export default function LearnScreen() {
  const router = useRouter();
  const store = useSessionStore();
  const [nextTopic, setNextTopic] = useState("");

  const onTelemetryUpdate = useCallback(
    (data: any) => {
      store.updateEngagement(data);
    },
    [store]
  );

  const { recordTap, recordError, recordSuccess } = useTelemetry(onTelemetryUpdate);

  // Start streaming lesson when topic is set
  useEffect(() => {
    if (!store.currentTopic || !store.childId) return;
    if (store.isLessonStreaming || store.streamedContent) return;

    store.setStreaming(true);
    store.clearContent();

    generateLesson(
      {
        child_id: store.childId,
        topic: store.currentTopic,
        academic_tier: store.academicTier,
        mood: store.mood,
        prompt_modifiers: store.promptModifiers,
      },
      (token) => {
        store.appendContent(token);
      },
      () => {
        store.setStreaming(false);
      }
    ).catch((err) => {
      console.error("[Learn] Stream error:", err);
      store.setStreaming(false);
      store.appendContent("\n\n⚠️ Could not connect to the learning server. Make sure the backend is running!");
    });
  }, [store.currentTopic]);

  // Fetch next recommendation
  useEffect(() => {
    if (!store.isLessonStreaming && store.streamedContent) {
      getRecommendation({
        child_id: store.childId,
        current_topic: store.currentTopic,
      })
        .then((r) => setNextTopic(r.recommended_topic))
        .catch(() => {});
    }
  }, [store.isLessonStreaming, store.streamedContent]);

  const handleNext = () => {
    store.clearContent();
    store.setCurrentTopic(nextTopic || "animals");
  };

  const moodEmoji =
    store.mood === "happy"
      ? "😊"
      : store.mood === "frustrated"
      ? "😤"
      : store.mood === "tired"
      ? "😴"
      : "😐";

  const engagementColor =
    store.engagementScore > 70
      ? "#10B981"
      : store.engagementScore > 40
      ? "#F59E0B"
      : "#EF4444";

  return (
    <View style={styles.container}>
      {/* Engagement Header */}
      <View style={styles.header}>
        <View style={styles.topicBadge}>
          <Text style={styles.topicText}>
            📚 {store.currentTopic || "No topic selected"}
          </Text>
        </View>
        <View style={[styles.engagementPill, { backgroundColor: engagementColor + "20" }]}>
          <Text style={[styles.engagementText, { color: engagementColor }]}>
            {moodEmoji} {store.engagementScore}%
          </Text>
        </View>
      </View>

      {/* Lesson Content */}
      <ScrollView
        style={styles.lessonScroll}
        contentContainerStyle={styles.lessonContent}
        onTouchStart={recordTap}
      >
        {store.streamedContent ? (
          <Text style={styles.lessonText}>{store.streamedContent}</Text>
        ) : (
          <View style={styles.emptyState}>
            <Text style={styles.emptyEmoji}>🦉</Text>
            <Text style={styles.emptyText}>
              {store.currentTopic
                ? "Loading your lesson..."
                : "Go to Home and pick a topic!"}
            </Text>
          </View>
        )}

        {store.isLessonStreaming && (
          <View style={styles.streamingIndicator}>
            <ActivityIndicator size="small" color="#0D9488" />
            <Text style={styles.streamingText}>Professor Hoot is teaching...</Text>
          </View>
        )}
      </ScrollView>

      {/* Action Buttons */}
      {!store.isLessonStreaming && store.streamedContent ? (
        <View style={styles.actionBar}>
          <TouchableOpacity
            style={styles.actionBtnSecondary}
            onPress={() => {
              recordSuccess();
              router.push("/");
            }}
          >
            <Ionicons name="home" size={20} color="#0D9488" />
            <Text style={styles.actionTextSecondary}>Home</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionBtnPrimary}
            onPress={() => {
              recordSuccess();
              handleNext();
            }}
          >
            <Text style={styles.actionTextPrimary}>
              Next: {nextTopic || "..."} →
            </Text>
          </TouchableOpacity>
        </View>
      ) : null}

      {/* Agent Info (Debug) */}
      <View style={styles.debugBar}>
        <Text style={styles.debugText}>
          Agent: {store.agentRouted} | Action: {store.nextAction}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F0FDFA" },

  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#E2E8F0",
  },
  topicBadge: {
    backgroundColor: "#F0FDFA",
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 12,
  },
  topicText: { fontSize: 14, fontWeight: "600", color: "#0D9488" },
  engagementPill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  engagementText: { fontSize: 13, fontWeight: "700" },

  lessonScroll: { flex: 1 },
  lessonContent: { padding: 20, paddingBottom: 40 },
  lessonText: {
    fontSize: 18,
    lineHeight: 30,
    color: "#1E293B",
    fontWeight: "400",
  },

  emptyState: { alignItems: "center", marginTop: 60 },
  emptyEmoji: { fontSize: 64, marginBottom: 16 },
  emptyText: { fontSize: 16, color: "#94A3B8", textAlign: "center" },

  streamingIndicator: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 20,
    gap: 8,
  },
  streamingText: { fontSize: 13, color: "#0D9488", fontStyle: "italic" },

  actionBar: {
    flexDirection: "row",
    padding: 16,
    gap: 12,
    backgroundColor: "#fff",
    borderTopWidth: 1,
    borderTopColor: "#E2E8F0",
  },
  actionBtnPrimary: {
    flex: 2,
    backgroundColor: "#0D9488",
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: "center",
  },
  actionTextPrimary: { color: "#fff", fontSize: 16, fontWeight: "700" },
  actionBtnSecondary: {
    flex: 1,
    backgroundColor: "#F0FDFA",
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "center",
    gap: 6,
  },
  actionTextSecondary: { color: "#0D9488", fontSize: 14, fontWeight: "600" },

  debugBar: {
    backgroundColor: "#1E293B",
    paddingVertical: 4,
    paddingHorizontal: 12,
  },
  debugText: { fontSize: 10, color: "#94A3B8", textAlign: "center" },
});
