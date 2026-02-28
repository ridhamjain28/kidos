/**
 * KidOS MVP - Home Screen
 * =========================
 * Welcome screen with session start, engagement indicator, and quick actions.
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
} from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useSessionStore } from "../stores/sessionStore";
import { useSession } from "../hooks/useSession";
import { checkHealth, getRecommendation } from "../services/api";

const TOPICS = [
  { id: "animals", emoji: "🦁", label: "Animals" },
  { id: "planets", emoji: "🪐", label: "Space" },
  { id: "numbers", emoji: "🔢", label: "Math" },
  { id: "colors", emoji: "🎨", label: "Colors" },
  { id: "gravity", emoji: "🍎", label: "Science" },
];

export default function HomeScreen() {
  const router = useRouter();
  const { begin } = useSession();
  const { sessionId, engagementScore, mood, childId } = useSessionStore();
  const [backendStatus, setBackendStatus] = useState<string>("checking...");
  const [recommendation, setRecommendation] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkHealth()
      .then((h) => setBackendStatus(`${h.ollama === "online" ? "✅" : "⚠️"} ${h.ollama}`))
      .catch(() => setBackendStatus("❌ offline"));
  }, []);

  useEffect(() => {
    getRecommendation({ child_id: childId, current_topic: "" })
      .then((r) => setRecommendation(r.recommended_topic))
      .catch(() => {});
  }, [childId]);

  const handleStartLesson = async (topic: string) => {
    setLoading(true);
    const session = await begin(topic);
    setLoading(false);
    if (session) {
      router.push("/learn");
    }
  };

  const moodEmoji =
    mood === "happy" ? "😊" : mood === "frustrated" ? "😤" : mood === "tired" ? "😴" : "😐";

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Hero Card */}
      <View style={styles.heroCard}>
        <Text style={styles.heroEmoji}>🦉</Text>
        <Text style={styles.heroTitle}>Hey there, Explorer!</Text>
        <Text style={styles.heroSubtitle}>What do you want to learn today?</Text>

        {sessionId ? (
          <View style={styles.engagementBadge}>
            <Text style={styles.engagementText}>
              {moodEmoji} Engagement: {engagementScore}%
            </Text>
          </View>
        ) : null}
      </View>

      {/* Recommended */}
      {recommendation ? (
        <TouchableOpacity
          style={styles.recommendCard}
          onPress={() => handleStartLesson(recommendation)}
          activeOpacity={0.85}
        >
          <View style={styles.recommendBadge}>
            <Ionicons name="sparkles" size={16} color="#F59E0B" />
            <Text style={styles.recommendBadgeText}>Recommended for you</Text>
          </View>
          <Text style={styles.recommendTopic}>
            {TOPICS.find((t) => t.id === recommendation)?.emoji || "📚"}{" "}
            {recommendation.charAt(0).toUpperCase() + recommendation.slice(1)}
          </Text>
        </TouchableOpacity>
      ) : null}

      {/* Topic Grid */}
      <Text style={styles.sectionTitle}>Pick a Topic</Text>
      <View style={styles.topicGrid}>
        {TOPICS.map((topic) => (
          <TouchableOpacity
            key={topic.id}
            style={styles.topicCard}
            onPress={() => handleStartLesson(topic.id)}
            activeOpacity={0.85}
          >
            <Text style={styles.topicEmoji}>{topic.emoji}</Text>
            <Text style={styles.topicLabel}>{topic.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#0D9488" />
          <Text style={styles.loadingText}>Starting lesson...</Text>
        </View>
      )}

      {/* Status Footer */}
      <View style={styles.statusBar}>
        <Ionicons name="server" size={14} color="#94A3B8" />
        <Text style={styles.statusText}>Backend: {backendStatus}</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F0FDFA" },
  content: { padding: 20, paddingBottom: 40 },

  heroCard: {
    backgroundColor: "#fff",
    borderRadius: 24,
    padding: 28,
    alignItems: "center",
    marginBottom: 20,
    shadowColor: "#0D9488",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  heroEmoji: { fontSize: 48, marginBottom: 8 },
  heroTitle: { fontSize: 24, fontWeight: "800", color: "#0F172A", marginBottom: 4 },
  heroSubtitle: { fontSize: 15, color: "#64748B", marginBottom: 12 },
  engagementBadge: {
    backgroundColor: "#F0FDFA",
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 20,
    marginTop: 8,
  },
  engagementText: { fontSize: 13, fontWeight: "600", color: "#0D9488" },

  recommendCard: {
    backgroundColor: "#FFFBEB",
    borderRadius: 16,
    padding: 18,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: "#FDE68A",
  },
  recommendBadge: { flexDirection: "row", alignItems: "center", marginBottom: 8 },
  recommendBadgeText: { fontSize: 12, fontWeight: "600", color: "#D97706", marginLeft: 6 },
  recommendTopic: { fontSize: 20, fontWeight: "700", color: "#92400E" },

  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#0F172A",
    marginBottom: 12,
    marginLeft: 4,
  },
  topicGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    gap: 12,
  },
  topicCard: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 20,
    width: "47%",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  topicEmoji: { fontSize: 36, marginBottom: 8 },
  topicLabel: { fontSize: 14, fontWeight: "600", color: "#334155" },

  loadingOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(240,253,250,0.9)",
    justifyContent: "center",
    alignItems: "center",
  },
  loadingText: { marginTop: 12, fontSize: 15, color: "#0D9488", fontWeight: "600" },

  statusBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginTop: 24,
    gap: 6,
  },
  statusText: { fontSize: 12, color: "#94A3B8" },
});
