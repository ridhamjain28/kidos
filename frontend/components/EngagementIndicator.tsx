/**
 * KidOS MVP - Engagement Indicator Component
 * =============================================
 * Visual indicator showing child's real-time engagement state.
 * Color-coded: Green (high) → Yellow (medium) → Red (low).
 */

import React from "react";
import { View, Text, StyleSheet, Animated } from "react-native";
import { Ionicons } from "@expo/vector-icons";

interface EngagementIndicatorProps {
  score: number;
  mood: string;
  frustrationLevel: string;
  compact?: boolean;
}

export function EngagementIndicator({
  score,
  mood,
  frustrationLevel,
  compact = false,
}: EngagementIndicatorProps) {
  const moodEmoji =
    mood === "happy"
      ? "😊"
      : mood === "frustrated"
      ? "😤"
      : mood === "tired"
      ? "😴"
      : "😐";

  const barColor =
    score > 70 ? "#10B981" : score > 40 ? "#F59E0B" : "#EF4444";

  const bgColor =
    score > 70 ? "#ECFDF5" : score > 40 ? "#FFFBEB" : "#FEF2F2";

  const barWidth = `${Math.max(5, Math.min(100, score))}%`;

  if (compact) {
    return (
      <View style={[styles.compactContainer, { backgroundColor: bgColor }]}>
        <Text style={styles.compactEmoji}>{moodEmoji}</Text>
        <View style={styles.compactBarTrack}>
          <View
            style={[
              styles.compactBarFill,
              { width: barWidth as any, backgroundColor: barColor },
            ]}
          />
        </View>
        <Text style={[styles.compactScore, { color: barColor }]}>
          {score}%
        </Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: bgColor }]}>
      <View style={styles.header}>
        <Text style={styles.emoji}>{moodEmoji}</Text>
        <View style={styles.headerText}>
          <Text style={styles.label}>Engagement</Text>
          <Text style={[styles.score, { color: barColor }]}>{score}%</Text>
        </View>
      </View>

      {/* Progress Bar */}
      <View style={styles.barTrack}>
        <View
          style={[
            styles.barFill,
            { width: barWidth as any, backgroundColor: barColor },
          ]}
        />
      </View>

      {/* Status Row */}
      <View style={styles.statusRow}>
        <View style={styles.statusItem}>
          <Ionicons
            name={frustrationLevel === "high" ? "alert-circle" : "checkmark-circle"}
            size={14}
            color={frustrationLevel === "high" ? "#EF4444" : "#10B981"}
          />
          <Text style={styles.statusText}>
            Frustration: {frustrationLevel}
          </Text>
        </View>
        <View style={styles.statusItem}>
          <Ionicons name="happy" size={14} color="#64748B" />
          <Text style={styles.statusText}>Mood: {mood}</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
    gap: 10,
  },
  emoji: { fontSize: 28 },
  headerText: { flex: 1 },
  label: { fontSize: 12, color: "#64748B", fontWeight: "500" },
  score: { fontSize: 22, fontWeight: "800" },

  barTrack: {
    height: 8,
    backgroundColor: "#E2E8F0",
    borderRadius: 4,
    overflow: "hidden",
    marginBottom: 10,
  },
  barFill: {
    height: "100%",
    borderRadius: 4,
  },

  statusRow: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  statusItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  statusText: { fontSize: 11, color: "#64748B" },

  // Compact variant
  compactContainer: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 6,
    gap: 8,
  },
  compactEmoji: { fontSize: 16 },
  compactBarTrack: {
    flex: 1,
    height: 4,
    backgroundColor: "#E2E8F0",
    borderRadius: 2,
    overflow: "hidden",
  },
  compactBarFill: {
    height: "100%",
    borderRadius: 2,
  },
  compactScore: { fontSize: 12, fontWeight: "700", minWidth: 32 },
});
