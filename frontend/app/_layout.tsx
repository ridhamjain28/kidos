/**
 * KidOS MVP - Root Layout
 * =========================
 * Expo Router layout with tab navigation.
 */

import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { StatusBar } from "expo-status-bar";
import { View } from "react-native";

const TEAL = "#0D9488";
const TEAL_LIGHT = "#F0FDFA";

export default function RootLayout() {
  return (
    <View style={{ flex: 1, backgroundColor: TEAL_LIGHT }}>
      <StatusBar style="dark" />
      <Tabs
        screenOptions={{
          headerStyle: { backgroundColor: TEAL },
          headerTintColor: "#fff",
          headerTitleStyle: { fontWeight: "bold", fontSize: 18 },
          tabBarActiveTintColor: TEAL,
          tabBarInactiveTintColor: "#94A3B8",
          tabBarStyle: {
            backgroundColor: "#fff",
            borderTopWidth: 0,
            elevation: 8,
            shadowColor: "#000",
            shadowOffset: { width: 0, height: -2 },
            shadowOpacity: 0.1,
            shadowRadius: 8,
            height: 60,
            paddingBottom: 8,
          },
          tabBarLabelStyle: {
            fontSize: 11,
            fontWeight: "600",
          },
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            title: "Home",
            headerTitle: "🦉 KidOS",
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="home" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="learn"
          options={{
            title: "Learn",
            headerTitle: "📚 Lesson",
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="book" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="feed"
          options={{
            title: "Discover",
            headerTitle: "🔍 Discover",
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="compass" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="games"
          options={{
            title: "Games",
            headerTitle: "🎮 Games",
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="game-controller" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="parent"
          options={{
            title: "Parents",
            headerTitle: "👨‍👩‍👧 Parent Zone",
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="shield-checkmark" size={size} color={color} />
            ),
          }}
        />
      </Tabs>
    </View>
  );
}
