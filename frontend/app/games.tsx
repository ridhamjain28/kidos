/**
 * KidOS MVP - Games Hub Screen
 * ================================
 * Placeholder for games (to be migrated from web app).
 */

import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const GAMES = [
  { id: "memory", emoji: "🃏", title: "Memory Zoo", desc: "Match animal pairs!", color: "#ECFDF5" },
  { id: "math", emoji: "➕", title: "Math Quest", desc: "Solve fun puzzles!", color: "#EFF6FF" },
  { id: "words", emoji: "🔤", title: "Word Hunter", desc: "Find hidden words!", color: "#FEF3C7" },
  { id: "paint", emoji: "🎨", title: "Magic Paint", desc: "Draw & create!", color: "#FCE7F3" },
  { id: "bubble", emoji: "🫧", title: "Bubble Pop", desc: "Pop to learn!", color: "#F0FDFA" },
  { id: "speak", emoji: "🗣️", title: "Speak World", desc: "Practice speaking!", color: "#FDF4FF" },
];

export default function GamesScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.header}>Choose a Game!</Text>
      <View style={styles.grid}>
        {GAMES.map((game) => (
          <TouchableOpacity
            key={game.id}
            style={[styles.card, { backgroundColor: game.color }]}
            activeOpacity={0.85}
          >
            <Text style={styles.emoji}>{game.emoji}</Text>
            <Text style={styles.title}>{game.title}</Text>
            <Text style={styles.desc}>{game.desc}</Text>
            <View style={styles.comingSoon}>
              <Ionicons name="lock-closed" size={12} color="#94A3B8" />
              <Text style={styles.comingSoonText}>Coming soon</Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F0FDFA" },
  content: { padding: 16, paddingBottom: 40 },
  header: {
    fontSize: 22,
    fontWeight: "800",
    color: "#0F172A",
    marginBottom: 16,
    textAlign: "center",
  },
  grid: { flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between", gap: 12 },
  card: {
    width: "47%",
    borderRadius: 18,
    padding: 20,
    alignItems: "center",
    marginBottom: 4,
  },
  emoji: { fontSize: 40, marginBottom: 8 },
  title: { fontSize: 15, fontWeight: "700", color: "#1E293B", marginBottom: 2 },
  desc: { fontSize: 12, color: "#64748B", textAlign: "center", marginBottom: 8 },
  comingSoon: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#F1F5F9",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  comingSoonText: { fontSize: 10, color: "#94A3B8", fontWeight: "600" },
});
