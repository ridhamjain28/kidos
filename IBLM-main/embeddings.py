"""
IBLM Core - Embedding Engine
============================

Lightweight embedding utilities for semantic matching without external dependencies.

BREAKTHROUGH CONCEPT:
Traditional systems rely on expensive external embedding APIs.
We implement a hybrid approach:
1. Fast TF-IDF based embeddings for local operation
2. Optional external embedding integration for production
3. Cosine similarity for relevance matching

This enables the kernel to run completely offline while still
maintaining semantic understanding.
"""

import math
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
import hashlib


@dataclass
class EmbeddingConfig:
    """Configuration for the embedding engine."""
    vector_size: int = 128
    use_external: bool = False
    external_provider: Optional[str] = None  # "openai", "cohere", etc.
    cache_embeddings: bool = True
    max_cache_size: int = 10000


class EmbeddingEngine:
    """
    Lightweight semantic embedding engine.
    
    BREAKTHROUGH: Zero external dependencies for basic operation.
    
    The engine uses a hybrid approach:
    1. TF-IDF vectors for fast local embeddings
    2. Semantic hashing for approximate matching
    3. Optional external API integration for production use
    
    This allows the IBLM to work completely offline while maintaining
    the ability to upgrade to more sophisticated embeddings when needed.
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        
        # Document frequency cache (for IDF)
        self._df: Counter = Counter()
        self._total_docs: int = 0
        
        # Embedding cache
        self._cache: Dict[str, List[float]] = {}
        
        # External embedding function (can be set later)
        self._external_embed: Optional[Callable[[str], List[float]]] = None
        
        # Vocabulary for consistent vectorization
        self._vocabulary: Dict[str, int] = {}
        self._vocab_lock: bool = False
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization with normalization."""
        # Lowercase and split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        
        # Remove very short tokens and common stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                     'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                     'from', 'as', 'or', 'and', 'but', 'if', 'then', 'so', 'than',
                     'that', 'this', 'these', 'those', 'it', 'its'}
        
        return [t for t in tokens if len(t) > 2 and t not in stopwords]
    
    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute term frequency with logarithmic scaling."""
        tf: Counter = Counter(tokens)
        total = len(tokens) if tokens else 1
        
        # Log-normalized TF
        return {term: (1 + math.log(count)) / total for term, count in tf.items()}
    
    def _compute_idf(self, term: str) -> float:
        """Compute inverse document frequency."""
        df = self._df.get(term, 0)
        if df == 0:
            return 0.0
        return math.log(self._total_docs / df)
    
    def train(self, documents: List[str]) -> None:
        """
        Train the embedding engine on a corpus of documents.
        
        This builds the vocabulary and IDF statistics needed for
        TF-IDF vectorization.
        """
        # Reset statistics
        self._df = Counter()
        self._total_docs = len(documents)
        
        # Build vocabulary and document frequencies
        for doc in documents:
            tokens = set(self._tokenize(doc))
            for token in tokens:
                self._df[token] += 1
                if token not in self._vocabulary:
                    self._vocabulary[token] = len(self._vocabulary)
        
        # Lock vocabulary after training
        self._vocab_lock = True
    
    def _hash_embed(self, text: str) -> List[float]:
        """
        Generate embedding using locality-sensitive hashing.
        
        This is a fast fallback when no training data is available.
        Uses random projections based on token hashes.
        """
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self.config.vector_size
        
        # Initialize embedding
        embedding = [0.0] * self.config.vector_size
        
        for token in tokens:
            # Use token hash to generate pseudo-random projection
            token_hash = hashlib.md5(token.encode()).hexdigest()
            for i in range(min(16, self.config.vector_size)):
                # Convert hex to signed float (-1 to 1)
                hex_val = int(token_hash[i*2:(i+1)*2], 16)
                projection = (hex_val / 127.5) - 1.0
                embedding[i % self.config.vector_size] += projection
        
        # Normalize
        magnitude = math.sqrt(sum(x*x for x in embedding)) or 1.0
        return [x / magnitude for x in embedding]
    
    def _tfidf_embed(self, text: str) -> List[float]:
        """
        Generate embedding using TF-IDF vectorization.
        
        Projects the TF-IDF vector into a fixed-size space using
        vocabulary indices modulo vector_size.
        """
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self.config.vector_size
        
        # Compute TF
        tf = self._compute_tf(tokens)
        
        # Initialize embedding
        embedding = [0.0] * self.config.vector_size
        
        for term, term_tf in tf.items():
            idf = self._compute_idf(term)
            tfidf = term_tf * idf
            
            # Project into embedding space
            if term in self._vocabulary:
                idx = self._vocabulary[term] % self.config.vector_size
            else:
                # Hash-based index for OOV terms
                idx = hash(term) % self.config.vector_size
            
            embedding[idx] += tfidf
        
        # Normalize
        magnitude = math.sqrt(sum(x*x for x in embedding)) or 1.0
        return [x / magnitude for x in embedding]
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Uses the best available method:
        1. External API if configured and available
        2. TF-IDF if trained
        3. Hash-based fallback
        """
        # Check cache
        cache_key = hashlib.sha256(text.encode()).hexdigest()[:16]
        if self.config.cache_embeddings and cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try external embedding first
        if self.config.use_external and self._external_embed:
            try:
                embedding = self._external_embed(text)
                if self.config.cache_embeddings:
                    self._cache[cache_key] = embedding
                return embedding
            except Exception:
                pass  # Fall through to local methods
        
        # Use TF-IDF if trained, otherwise hash-based
        if self._vocab_lock and self._total_docs > 0:
            embedding = self._tfidf_embed(text)
        else:
            embedding = self._hash_embed(text)
        
        # Cache result
        if self.config.cache_embeddings:
            if len(self._cache) >= self.config.max_cache_size:
                # Simple eviction: clear half the cache
                keys = list(self._cache.keys())[:len(self._cache)//2]
                for k in keys:
                    del self._cache[k]
            self._cache[cache_key] = embedding
        
        return embedding
    
    def set_external_provider(self, embed_fn: Callable[[str], List[float]]) -> None:
        """
        Set an external embedding provider.
        
        Example usage:
            import openai
            engine.set_external_provider(
                lambda text: openai.Embedding.create(input=text, model="text-embedding-ada-002")["data"][0]["embedding"]
            )
        """
        self._external_embed = embed_fn
        self.config.use_external = True
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Returns a value between -1 and 1, where 1 is identical,
        0 is orthogonal, and -1 is opposite.
        """
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same dimension")
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    @staticmethod
    def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
        """Compute Euclidean distance between two vectors."""
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same dimension")
        
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))
    
    def find_similar(
        self, 
        query: str, 
        candidates: List[Tuple[str, List[float]]], 
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[Tuple[str, float]]:
        """
        Find most similar items to query from candidates.
        
        Args:
            query: The query text
            candidates: List of (id, embedding) tuples
            top_k: Number of results to return
            threshold: Minimum similarity score
            
        Returns:
            List of (id, similarity_score) tuples, sorted by score descending
        """
        query_embedding = self.embed(query)
        
        results = []
        for item_id, embedding in candidates:
            similarity = self.cosine_similarity(query_embedding, embedding)
            if similarity >= threshold:
                results.append((item_id, similarity))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embed(text) for text in texts]
    
    def semantic_hash(self, text: str, bits: int = 64) -> str:
        """
        Generate a semantic hash for approximate matching.
        
        Unlike cryptographic hashes, semantically similar texts
        will have similar hashes (measured by Hamming distance).
        """
        embedding = self.embed(text)
        
        # Convert to binary hash
        hash_bits = []
        for i in range(min(bits, len(embedding))):
            hash_bits.append('1' if embedding[i] > 0 else '0')
        
        # Pad if needed
        while len(hash_bits) < bits:
            hash_bits.append('0')
        
        # Convert to hex
        binary_str = ''.join(hash_bits)
        return hex(int(binary_str, 2))[2:].zfill(bits // 4)
    
    def to_dict(self) -> Dict:
        """Serialize the engine state."""
        return {
            "config": {
                "vector_size": self.config.vector_size,
                "use_external": self.config.use_external,
                "external_provider": self.config.external_provider,
                "cache_embeddings": self.config.cache_embeddings,
                "max_cache_size": self.config.max_cache_size,
            },
            "df": dict(self._df),
            "total_docs": self._total_docs,
            "vocabulary": self._vocabulary,
            "vocab_lock": self._vocab_lock,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EmbeddingEngine":
        """Deserialize the engine state."""
        config = EmbeddingConfig(**data.get("config", {}))
        engine = cls(config)
        engine._df = Counter(data.get("df", {}))
        engine._total_docs = data.get("total_docs", 0)
        engine._vocabulary = data.get("vocabulary", {})
        engine._vocab_lock = data.get("vocab_lock", False)
        return engine


# Semantic similarity utilities
class SemanticMatcher:
    """
    High-level semantic matching utilities.
    
    Provides convenient methods for common matching tasks
    used throughout the IBLM system.
    """
    
    def __init__(self, engine: EmbeddingEngine):
        self.engine = engine
    
    def is_similar(self, text1: str, text2: str, threshold: float = 0.7) -> bool:
        """Check if two texts are semantically similar."""
        emb1 = self.engine.embed(text1)
        emb2 = self.engine.embed(text2)
        return EmbeddingEngine.cosine_similarity(emb1, emb2) >= threshold
    
    def find_contradiction(
        self, 
        new_statement: str, 
        existing_statements: List[str]
    ) -> Optional[Tuple[int, str]]:
        """
        Find if new statement contradicts any existing statement.
        
        Returns (index, statement) of the contradiction, or None.
        
        BREAKTHROUGH: This is key to the evolve() mechanism.
        When a contradiction is found, we can immediately update
        the kernel's rules.
        """
        new_emb = self.engine.embed(new_statement)
        
        # Contradiction indicators
        negation_words = {'not', 'never', 'dont', "don't", 'no', 'avoid', 
                         'stop', 'instead', 'rather', 'but', 'however'}
        
        new_tokens = set(new_statement.lower().split())
        has_negation = bool(new_tokens & negation_words)
        
        for i, existing in enumerate(existing_statements):
            existing_emb = self.engine.embed(existing)
            similarity = EmbeddingEngine.cosine_similarity(new_emb, existing_emb)
            
            existing_tokens = set(existing.lower().split())
            existing_negation = bool(existing_tokens & negation_words)
            
            # High similarity but opposite polarity suggests contradiction
            if similarity > 0.5 and has_negation != existing_negation:
                return (i, existing)
            
            # Very high similarity with explicit negation
            if similarity > 0.7 and has_negation:
                return (i, existing)
        
        return None
    
    def cluster_similar(
        self, 
        texts: List[str], 
        threshold: float = 0.75
    ) -> List[List[int]]:
        """
        Cluster similar texts together.
        
        Used for rule consolidation - merging similar rules
        to reduce kernel size.
        """
        embeddings = [self.engine.embed(t) for t in texts]
        n = len(texts)
        
        # Simple single-linkage clustering
        clusters: List[List[int]] = [[i] for i in range(n)]
        cluster_map = {i: i for i in range(n)}
        
        for i in range(n):
            for j in range(i + 1, n):
                if cluster_map[i] == cluster_map[j]:
                    continue
                    
                sim = EmbeddingEngine.cosine_similarity(embeddings[i], embeddings[j])
                if sim >= threshold:
                    # Merge clusters
                    old_cluster = cluster_map[j]
                    new_cluster = cluster_map[i]
                    
                    for k in range(n):
                        if cluster_map[k] == old_cluster:
                            cluster_map[k] = new_cluster
                            clusters[new_cluster].append(k)
                    
                    clusters[old_cluster] = []
        
        # Return non-empty clusters
        return [c for c in clusters if c]
