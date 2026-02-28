/**
 * KidOS MVP - Discover Feed Screen
 * ====================================
 * Shows recommended topics and content cards.
 */

import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
} from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useSessionStore } from "../stores/sessionStore";
import { getRecommendation, RecommendResponse } from "../services/api";

const CONTENT_CARDS = [
  { topic: "animals", emoji: "🦁", title: "Amazing Animals", description: "Discover incredible creatures!" },
  { topic: "planets", emoji: "🪐", title: "Solar System", description: "Journey through space!" },
  { topic: "gravity", emoji: "🍎", title: "How Things Fall", description: "Why do things drop?" },
  { topic: "colors", emoji: "🌈", title: "Rainbow Science", description: "The magic of light!" },
  { topic: "numbers", emoji: "🧮", title: "Number Fun", description: "Math can be cool!" },
  { topic: "habitats", emoji: "🌳", title: "Where Animals Live", description: "Explore habitats!" },
];

export default function FeedScreen() {
  const router = useRouter();
  const { childId } = useSessionStore();
  const [recommendation, setRecommendation] = useState<RecommendResponse | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchRecommendation = async () => {
    try {
      const rec = await getRecommendation({ child_id: childId, current_topic: "" });
      setRecommendation(rec);
    } catch {
      // Backend offline
    }
  };

  useEffect(() => {
    fetchRecommendation();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchRecommendation();
    setRefreshing(false);
  };

  const handleCardPress = (topic: string) => {
    const store = useSessionStore.getState();
    store.setCurrentTopic(topic);
    router.push("/learn");
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#0D9488" />}
    >
      {/* AI Recommendation Banner */}
      {recommendation && (
        <TouchableOpacity
          style={styles.recBanner}
          onPress={() => handleCardPress(recommendation.recommended_topic)}
          activeOpacity={0.85}
        >
          <View style={styles.recHeader}>
            <Ionicons name="sparkles" size={18} color="#F59E0B" />
            <Text style={styles.recLabel}>AI Recommends</Text>
          </View>
          <Text style={styles.recTopic}>
            {recommendation.recommended_topic.charAt(0).toUpperCase() +
              recommendation.recommended_topic.slice(1)}
          </Text>
          <Text style={styles.recReason}>{recommendation.reason}</Text>
          <View style={styles.recMeta}>
            <View style={styles.recPill}>
              <Text style={styles.recPillText}>{recommendation.content_type}</Text>
            </View>
            <View style={styles.recPill}>
              <Text style={styles.recPillText}>Level {recommendation.difficulty_level}</Text>
            </View>
          </View>
        </TouchableOpacity>
      )}

      {/* Content Cards */}
      <Text style={styles.sectionTitle}>Explore Topics</Text>
      {CONTENT_CARDS.map((card) => (
        <TouchableOpacity
          key={card.topic}
          style={styles.card}
          onPress={() => handleCardPress(card.topic)}
          activeOpacity={0.85}
        >
          <Text style={styles.cardEmoji}>{card.emoji}</Text>
          <View style={styles.cardBody}>
            <Text style={styles.cardTitle}>{card.title}</Text>
            <Text style={styles.cardDesc}>{card.description}</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#CBD5E1" />
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F0FDFA" },
  content: { padding: 16, paddingBottom: 40 },

  recBanner: {
    backgroundColor: "#FFFBEB",
    borderRadius: 16,
    padding: 18,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: "#FDE68A",
  },
  recHeader: { flexDirection: "row", alignItems: "center", marginBottom: 8, gap: 6 },
  recLabel: { fontSize: 12, fontWeight: "700", color: "#D97706" },
  recTopic: { fontSize: 22, fontWeight: "800", color: "#92400E", marginBottom: 4 },
  recReason: { fontSize: 13, color: "#B45309", marginBottom: 10 },
  recMeta: { flexDirection: "row", gap: 8 },
  recPill: {
    backgroundColor: "#FEF3C7",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  recPillText: { fontSize: 11, fontWeight: "600", color: "#92400E" },

  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#0F172A",
    marginBottom: 12,
    marginLeft: 4,
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    flexDirection: "row",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  cardEmoji: { fontSize: 36, marginRight: 14 },
  cardBody: { flex: 1 },
  cardTitle: { fontSize: 16, fontWeight: "700", color: "#1E293B", marginBottom: 2 },
  cardDesc: { fontSize: 13, color: "#64748B" },
});
