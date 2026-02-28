/**
 * KidOS MVP - Lesson Card Component
 * ====================================
 * Displays a lesson topic card with engagement score and action button.
 */

import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

interface LessonCardProps {
  topic: string;
  emoji?: string;
  description?: string;
  contentType?: string;
  difficulty?: number;
  engagementScore?: number;
  onPress: () => void;
}

export function LessonCard({
  topic,
  emoji = "📚",
  description,
  contentType = "lesson",
  difficulty = 1,
  engagementScore,
  onPress,
}: LessonCardProps) {
  const difficultyLabel = ["Beginner", "Intermediate", "Advanced"][
    Math.min(difficulty - 1, 2)
  ];
  const difficultyColor = ["#10B981", "#F59E0B", "#EF4444"][
    Math.min(difficulty - 1, 2)
  ];

  const typeIcon =
    contentType === "video"
      ? "play-circle"
      : contentType === "quiz"
      ? "help-circle"
      : "book";

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.85}
    >
      <Text style={styles.emoji}>{emoji}</Text>

      <View style={styles.body}>
        <Text style={styles.topic}>
          {topic.charAt(0).toUpperCase() + topic.slice(1)}
        </Text>
        {description && <Text style={styles.description}>{description}</Text>}

        <View style={styles.meta}>
          <View style={styles.pill}>
            <Ionicons name={typeIcon as any} size={12} color="#64748B" />
            <Text style={styles.pillText}>{contentType}</Text>
          </View>
          <View style={[styles.pill, { backgroundColor: difficultyColor + "15" }]}>
            <Text style={[styles.pillText, { color: difficultyColor }]}>
              {difficultyLabel}
            </Text>
          </View>
        </View>
      </View>

      {engagementScore !== undefined && (
        <View style={styles.scoreBadge}>
          <Text style={styles.scoreText}>{engagementScore}%</Text>
        </View>
      )}

      <Ionicons name="chevron-forward" size={20} color="#CBD5E1" />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 16,
    marginBottom: 10,
    flexDirection: "row",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  emoji: { fontSize: 32, marginRight: 12 },
  body: { flex: 1 },
  topic: { fontSize: 16, fontWeight: "700", color: "#1E293B", marginBottom: 2 },
  description: { fontSize: 12, color: "#64748B", marginBottom: 6 },
  meta: { flexDirection: "row", gap: 6 },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#F1F5F9",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    gap: 4,
  },
  pillText: { fontSize: 10, fontWeight: "600", color: "#64748B" },
  scoreBadge: {
    backgroundColor: "#F0FDFA",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    marginRight: 8,
  },
  scoreText: { fontSize: 12, fontWeight: "700", color: "#0D9488" },
});
