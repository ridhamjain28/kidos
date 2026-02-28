"""
KidOS MVP - ChromaDB Vector Store
===================================
Stores and queries behavioral embeddings for child learning profiles.
Uses ChromaDB in persistent mode (local directory, no server needed).
Uses a simple hash-based embedding to avoid downloading large models.
"""

import hashlib
import chromadb
import chromadb.utils.embedding_functions as ef
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.config import CHROMA_PATH


class SimpleHashEmbedding(ef.EmbeddingFunction):
    """Deterministic hash-based embedding that works fully offline.
    Not semantically meaningful, but sufficient for MVP matching."""

    def name(self) -> str:
        return "simple_hash_128d"

    def __call__(self, input: List[str]) -> List[List[float]]:
        results = []
        for text in input:
            h = hashlib.sha256(text.encode()).hexdigest()
            # Convert hex digest to 128 floats in [-1, 1]
            vec = []
            for i in range(0, min(len(h), 64), 1):
                val = (int(h[i], 16) - 7.5) / 7.5
                vec.append(val)
            # Pad to 128 dims
            vec = (vec * 4)[:128]
            results.append(vec)
        return results


class VectorStore:
    """ChromaDB wrapper for behavioral embedding storage and retrieval."""

    def __init__(self, persist_dir: str = CHROMA_PATH):
        self.client = chromadb.PersistentClient(path=persist_dir)
        embed_fn = SimpleHashEmbedding()
        self.behaviors = self.client.get_or_create_collection(
            name="behavioral_embeddings",
            metadata={"hnsw:space": "cosine"},
            embedding_function=embed_fn,
        )
        self.topics = self.client.get_or_create_collection(
            name="topic_interests",
            metadata={"hnsw:space": "cosine"},
            embedding_function=embed_fn,
        )

    def store_behavior(
        self,
        child_id: str,
        behavior_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Store a behavioral observation as an embedding."""
        doc_id = f"{child_id}_{behavior_type}_{datetime.now().timestamp()}"
        meta = {
            "child_id": child_id,
            "behavior_type": behavior_type,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {}),
        }
        self.behaviors.add(
            documents=[description],
            metadatas=[meta],
            ids=[doc_id],
        )

    def query_behaviors(
        self, child_id: str, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find behaviors similar to a query for a specific child."""
        results = self.behaviors.query(
            query_texts=[query],
            n_results=top_k,
            where={"child_id": child_id},
        )
        if not results["documents"][0]:
            return []

        return [
            {
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            }
            for i in range(len(results["documents"][0]))
        ]

    def store_topic_interest(self, child_id: str, topic: str, engagement_score: int):
        """Track topic engagement as a searchable embedding."""
        doc_id = f"{child_id}_topic_{topic}"
        try:
            self.topics.update(
                ids=[doc_id],
                documents=[f"Child engaged with {topic} at score {engagement_score}"],
                metadatas=[{
                    "child_id": child_id,
                    "topic": topic,
                    "engagement_score": engagement_score,
                    "updated_at": datetime.now().isoformat(),
                }],
            )
        except Exception:
            self.topics.add(
                ids=[doc_id],
                documents=[f"Child engaged with {topic} at score {engagement_score}"],
                metadatas=[{
                    "child_id": child_id,
                    "topic": topic,
                    "engagement_score": engagement_score,
                    "updated_at": datetime.now().isoformat(),
                }],
            )

    def get_top_interests(self, child_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Get child's top topic interests by engagement score."""
        results = self.topics.get(
            where={"child_id": child_id},
        )
        if not results["ids"]:
            return []

        interests = [
            {"topic": m["topic"], "engagement_score": m["engagement_score"]}
            for m in results["metadatas"]
        ]
        interests.sort(key=lambda x: x["engagement_score"], reverse=True)
        return interests[:top_k]

    def find_similar_topics(self, query: str, top_k: int = 3) -> List[str]:
        """Find topics similar to a given query across all children."""
        results = self.topics.query(query_texts=[query], n_results=top_k)
        if not results["metadatas"][0]:
            return []
        return [m["topic"] for m in results["metadatas"][0]]
