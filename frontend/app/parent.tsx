/**
 * KidOS MVP - Parent Zone Screen
 * ==================================
 * PIN-gated area with engagement insights and session history.
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useSessionStore } from "../stores/sessionStore";

const DEFAULT_PIN = "1234";

export default function ParentScreen() {
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [pinInput, setPinInput] = useState("");
  const { engagementScore, mood, topicsCovered, childId } = useSessionStore();

  const handleUnlock = () => {
    if (pinInput === DEFAULT_PIN) {
      setIsUnlocked(true);
      setPinInput("");
    } else {
      Alert.alert("Wrong PIN", "Default PIN is 1234");
      setPinInput("");
    }
  };

  if (!isUnlocked) {
    return (
      <View style={styles.lockScreen}>
        <Ionicons name="lock-closed" size={48} color="#0D9488" />
        <Text style={styles.lockTitle}>Parent Zone</Text>
        <Text style={styles.lockSubtitle}>Enter PIN to access</Text>
        <TextInput
          style={styles.pinInput}
          value={pinInput}
          onChangeText={setPinInput}
          placeholder="Enter PIN"
          keyboardType="number-pad"
          secureTextEntry
          maxLength={4}
        />
        <TouchableOpacity style={styles.unlockBtn} onPress={handleUnlock}>
          <Text style={styles.unlockBtnText}>Unlock</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Lock button */}
      <TouchableOpacity
        style={styles.lockBtn}
        onPress={() => setIsUnlocked(false)}
      >
        <Ionicons name="lock-open" size={16} color="#94A3B8" />
        <Text style={styles.lockBtnText}>Lock</Text>
      </TouchableOpacity>

      {/* Engagement Insights */}
      <View style={styles.insightCard}>
        <Text style={styles.insightTitle}>📊 Engagement Insights</Text>
        <View style={styles.statRow}>
          <View style={styles.stat}>
            <Text style={styles.statValue}>{engagementScore}%</Text>
            <Text style={styles.statLabel}>Engagement</Text>
          </View>
          <View style={styles.stat}>
            <Text style={styles.statValue}>
              {mood === "happy" ? "😊" : mood === "frustrated" ? "😤" : "😐"}
            </Text>
            <Text style={styles.statLabel}>Mood</Text>
          </View>
          <View style={styles.stat}>
            <Text style={styles.statValue}>{topicsCovered.length}</Text>
            <Text style={styles.statLabel}>Topics</Text>
          </View>
        </View>
      </View>

      {/* Topics Covered */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Topics Covered</Text>
        {topicsCovered.length > 0 ? (
          topicsCovered.map((t, i) => (
            <View key={i} style={styles.topicRow}>
              <Ionicons name="checkmark-circle" size={18} color="#10B981" />
              <Text style={styles.topicName}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </Text>
            </View>
          ))
        ) : (
          <Text style={styles.emptyText}>No topics covered yet in this session.</Text>
        )}
      </View>

      {/* Agent Activity */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🤖 Agent Activity</Text>
        <Text style={styles.agentInfo}>
          The agentic system monitors your child's engagement in real-time:
        </Text>
        <View style={styles.agentList}>
          <View style={styles.agentItem}>
            <Text style={styles.agentEmoji}>📊</Text>
            <View>
              <Text style={styles.agentName}>Observer Agent</Text>
              <Text style={styles.agentDesc}>Tracks engagement & frustration every 30s</Text>
            </View>
          </View>
          <View style={styles.agentItem}>
            <Text style={styles.agentEmoji}>🎯</Text>
            <View>
              <Text style={styles.agentName}>Orchestrator Agent</Text>
              <Text style={styles.agentDesc}>Routes to the right teaching approach</Text>
            </View>
          </View>
          <View style={styles.agentItem}>
            <Text style={styles.agentEmoji}>📚</Text>
            <View>
              <Text style={styles.agentName}>Teaching Agent</Text>
              <Text style={styles.agentDesc}>Generates personalized lessons via local AI</Text>
            </View>
          </View>
          <View style={styles.agentItem}>
            <Text style={styles.agentEmoji}>🎬</Text>
            <View>
              <Text style={styles.agentName}>Recommendation Agent</Text>
              <Text style={styles.agentDesc}>Suggests next content based on interests</Text>
            </View>
          </View>
        </View>
      </View>

      {/* Privacy Notice */}
      <View style={styles.privacyCard}>
        <Ionicons name="shield-checkmark" size={20} color="#0D9488" />
        <Text style={styles.privacyText}>
          All data stays on this device. No cloud sync, no tracking.
          100% local-first privacy.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F0FDFA" },
  content: { padding: 16, paddingBottom: 40 },

  lockScreen: {
    flex: 1,
    backgroundColor: "#F0FDFA",
    justifyContent: "center",
    alignItems: "center",
    padding: 32,
  },
  lockTitle: { fontSize: 24, fontWeight: "800", color: "#0F172A", marginTop: 16 },
  lockSubtitle: { fontSize: 14, color: "#64748B", marginBottom: 24 },
  pinInput: {
    width: 200,
    borderWidth: 2,
    borderColor: "#CBD5E1",
    borderRadius: 14,
    padding: 14,
    fontSize: 24,
    textAlign: "center",
    letterSpacing: 8,
    marginBottom: 16,
    backgroundColor: "#fff",
  },
  unlockBtn: {
    backgroundColor: "#0D9488",
    paddingHorizontal: 40,
    paddingVertical: 14,
    borderRadius: 14,
  },
  unlockBtnText: { color: "#fff", fontSize: 16, fontWeight: "700" },

  lockBtn: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-end",
    gap: 4,
    marginBottom: 12,
  },
  lockBtnText: { fontSize: 13, color: "#94A3B8" },

  insightCard: {
    backgroundColor: "#fff",
    borderRadius: 18,
    padding: 20,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  insightTitle: { fontSize: 17, fontWeight: "700", color: "#0F172A", marginBottom: 16 },
  statRow: { flexDirection: "row", justifyContent: "space-around" },
  stat: { alignItems: "center" },
  statValue: { fontSize: 28, fontWeight: "800", color: "#0D9488" },
  statLabel: { fontSize: 12, color: "#64748B", marginTop: 4 },

  section: {
    backgroundColor: "#fff",
    borderRadius: 18,
    padding: 18,
    marginBottom: 16,
  },
  sectionTitle: { fontSize: 16, fontWeight: "700", color: "#0F172A", marginBottom: 12 },
  topicRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8 },
  topicName: { fontSize: 15, color: "#334155" },
  emptyText: { fontSize: 14, color: "#94A3B8", fontStyle: "italic" },

  agentInfo: { fontSize: 13, color: "#64748B", marginBottom: 12 },
  agentList: { gap: 12 },
  agentItem: { flexDirection: "row", gap: 12, alignItems: "center" },
  agentEmoji: { fontSize: 28 },
  agentName: { fontSize: 14, fontWeight: "700", color: "#1E293B" },
  agentDesc: { fontSize: 12, color: "#64748B" },

  privacyCard: {
    flexDirection: "row",
    backgroundColor: "#ECFDF5",
    borderRadius: 14,
    padding: 14,
    gap: 10,
    alignItems: "center",
  },
  privacyText: { flex: 1, fontSize: 12, color: "#065F46", lineHeight: 18 },
});
