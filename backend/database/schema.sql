-- KidOS MVP - Database Schema
-- SQLite tables for child profiles, sessions, and content tracking.

-- Child Profile Table
CREATE TABLE IF NOT EXISTS child_profiles (
    child_id TEXT PRIMARY KEY,
    name TEXT DEFAULT 'Kiddo',
    age INTEGER DEFAULT 7,
    academic_tier TEXT DEFAULT 'Level 1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Session History Table
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    child_id TEXT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    final_engagement_score INTEGER DEFAULT 50,
    topics_covered TEXT DEFAULT '[]',
    completion_rate REAL DEFAULT 0.0,
    FOREIGN KEY (child_id) REFERENCES child_profiles(child_id)
);

-- Content Interaction Table
CREATE TABLE IF NOT EXISTS content_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    content_topic TEXT NOT NULL,
    content_type TEXT DEFAULT 'lesson',
    engagement_score INTEGER DEFAULT 50,
    completed BOOLEAN DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Recommendations Cache
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id TEXT NOT NULL,
    recommended_topic TEXT NOT NULL,
    content_type TEXT DEFAULT 'lesson',
    confidence_score REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES child_profiles(child_id)
);
