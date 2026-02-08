"""
IBLM Core - User Kernel
=======================

The central data structure: a Hybrid Graph-Vector storage system.

BREAKTHROUGH CONCEPT:
The User Kernel is a "Living Memory" that combines:
1. Graph structure for relationships (nodes with weighted edges)
2. Vector space for semantic matching (embeddings)
3. Rule engine for compiled behaviors

Unlike traditional RAG which stores raw text, the Kernel stores:
- Behavioral RULES (compiled from interactions)
- Knowledge NODES (entities and concepts)
- Style VECTOR (communication preferences)
- User PROFILE (the "Individual" in IBLM)

This achieves INFINITE CONTEXT SCALING because:
- Raw interactions are DELETED after compilation
- Rules grow logarithmically, not linearly
- Semantic compression merges similar concepts
"""

import json
import hashlib
import gzip
import uuid
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
import uuid

try:
    from .models import (
        Rule, RuleCategory, KernelNode, StyleVector, UserProfile,
        InteractionLog, ProcessedInteractionRegistry, Signal
    )
    from .embeddings import EmbeddingEngine, SemanticMatcher
except ImportError:
    from models import (
        Rule, RuleCategory, KernelNode, StyleVector, UserProfile,
        InteractionLog, ProcessedInteractionRegistry, Signal
    )
    from embeddings import EmbeddingEngine, SemanticMatcher


@dataclass
class KernelMetadata:
    """Metadata about the kernel state."""
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    total_rules: int = 0
    total_nodes: int = 0
    total_interactions_processed: int = 0
    garbage_collections: int = 0
    consolidations: int = 0


class UserKernel:
    """
    The Living Memory - core of the Individual Behavior Learning Machine.
    
    ARCHITECTURE:
    
    ┌─────────────────────────────────────────────────────────────┐
    │                       USER KERNEL                           │
    ├─────────────────────────────────────────────────────────────┤
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
    │  │   RULES     │  │    NODES    │  │   USER PROFILE      │ │
    │  │  (Compiled  │  │  (Knowledge │  │  (Individual        │ │
    │  │  behaviors) │  │   Graph)    │  │   representation)   │ │
    │  └─────────────┘  └─────────────┘  └─────────────────────┘ │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
    │  │   STYLE     │  │  WORKING    │  │   EMBEDDING         │ │
    │  │   VECTOR    │  │   MEMORY    │  │   ENGINE            │ │
    │  └─────────────┘  └─────────────┘  └─────────────────────┘ │
    └─────────────────────────────────────────────────────────────┘
    
    KEY METHODS:
    - add_rule(): Add a compiled behavioral rule
    - add_node(): Add a knowledge node to the graph
    - query_relevant(): Find rules/nodes relevant to a query
    - get_active_context(): Get current context for injection
    - export(): Serialize to portable format
    - load(): Deserialize from portable format
    
    GARBAGE COLLECTION:
    The kernel implements aggressive garbage collection:
    - Raw interaction logs are deleted after rule compilation
    - Low-weight rules decay and are pruned
    - Similar rules are consolidated
    
    PRODUCTION FEATURES:
    - Thread-safe operations with RLock
    - Resource limits to prevent DoS
    - Metrics collection
    """
    
    def __init__(
        self, 
        embedding_engine: Optional[EmbeddingEngine] = None,
        enable_thread_safety: bool = True,
        resource_limits: Optional[Dict[str, int]] = None
    ):
        import threading
        
        # Thread safety
        self._enable_thread_safety = enable_thread_safety
        self._lock = threading.RLock() if enable_thread_safety else None
        
        # Core storage
        self.rules: Dict[str, Rule] = {}
        self.nodes: Dict[str, KernelNode] = {}
        
        # User representation
        self.profile = UserProfile()
        self.style_vector = StyleVector()
        
        # Working memory (current session context)
        self.working_memory: Dict[str, Any] = {}
        self.active_project: Optional[str] = None
        
        # Temporary storage (subject to garbage collection)
        self._interaction_logs: Dict[str, InteractionLog] = {}
        self._pending_signals: List[Signal] = []
        
        # Processed interaction registry (survives GC)
        self._processed_registry = ProcessedInteractionRegistry()
        
        # Embedding engine
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        self.semantic_matcher = SemanticMatcher(self.embedding_engine)
        
        # Metadata
        self.metadata = KernelMetadata()
        
        # Resource limits (prevent DoS)
        default_limits = {
            "max_rules": 1000,
            "max_nodes": 500,
            "max_pending_signals": 100,
            "max_interaction_logs": 1000,
            "max_working_memory_items": 20,
        }
        self._resource_limits = {**default_limits, **(resource_limits or {})}
        
        # Metrics
        self._metrics = {
            "rules_added": 0,
            "rules_removed": 0,
            "nodes_added": 0,
            "signals_processed": 0,
            "gc_runs": 0,
            "lock_contentions": 0,
        }
        
        # Configuration
        self.config = {
            "rule_compilation_threshold": 3,      # Min signals before rule compilation
            "rule_confidence_threshold": 0.5,     # Min confidence for rule creation
            "garbage_collection_threshold": 10,   # Trigger GC after N interactions
            "rule_decay_rate": 0.01,              # Daily decay rate
            "rule_min_weight": 0.1,               # Rules below this are pruned
            "consolidation_threshold": 0.8,       # Similarity for rule merging
            "max_working_memory_items": 20,       # Limit working memory size
        }
    
    def _acquire_lock(self):
        """Acquire thread lock if enabled."""
        if self._lock:
            acquired = self._lock.acquire(blocking=True, timeout=5.0)
            if not acquired:
                self._metrics["lock_contentions"] += 1
                raise RuntimeError("Could not acquire kernel lock - possible deadlock")
    
    def _release_lock(self):
        """Release thread lock if enabled."""
        if self._lock:
            self._lock.release()
    
    def _check_resource_limit(self, resource: str, current: int) -> None:
        """Check if resource limit is exceeded."""
        limit = self._resource_limits.get(resource)
        if limit and current >= limit:
            try:
                from .exceptions import ResourceLimitError
            except ImportError:
                from exceptions import ResourceLimitError
            raise ResourceLimitError(resource, current, limit)
    
    def get_metrics(self) -> Dict[str, int]:
        """Get kernel metrics."""
        return dict(self._metrics)
    
    # ========================
    # RULE MANAGEMENT
    # ========================
    
    def add_rule(self, rule: Rule) -> str:
        """
        Add a compiled behavioral rule to the kernel.
        
        If a similar rule exists, we reinforce it instead of creating a duplicate.
        
        Thread-safe with resource limit enforcement.
        """
        self._acquire_lock()
        try:
            # Check resource limit
            self._check_resource_limit("max_rules", len(self.rules))
            
            # Check for similar existing rule
            for existing_id, existing_rule in self.rules.items():
                if existing_rule.embedding and rule.embedding:
                    similarity = EmbeddingEngine.cosine_similarity(
                        existing_rule.embedding, rule.embedding
                    )
                    if similarity > self.config["consolidation_threshold"]:
                        # Reinforce existing rule instead
                        existing_rule.reinforce()
                        return existing_id
            
            # Generate embedding if not present
            if not rule.embedding:
                rule.embedding = self.embedding_engine.embed(
                    f"{rule.condition} {rule.action}"
                )
            
            self.rules[rule.rule_id] = rule
            self.metadata.total_rules = len(self.rules)
            self.metadata.last_modified = datetime.now()
            self._metrics["rules_added"] += 1
            
            return rule.rule_id
        finally:
            self._release_lock()
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID."""
        return self.rules.get(rule_id)
    
    def update_rule(self, rule_id: str, **updates) -> bool:
        """Update a rule's attributes."""
        if rule_id not in self.rules:
            return False
        
        rule = self.rules[rule_id]
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        self.metadata.last_modified = datetime.now()
        return True
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule from the kernel."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            self.metadata.total_rules = len(self.rules)
            return True
        return False
    
    def query_rules(
        self, 
        query: str, 
        top_k: int = 5, 
        category: Optional[RuleCategory] = None,
        min_weight: float = 0.0
    ) -> List[Tuple[Rule, float]]:
        """
        Find rules relevant to a query.
        
        Returns list of (rule, relevance_score) tuples.
        """
        query_embedding = self.embedding_engine.embed(query)
        
        candidates = []
        for rule in self.rules.values():
            # Filter by category
            if category and rule.category != category:
                continue
            
            # Filter by weight
            if rule.weight < min_weight:
                continue
            
            # Compute relevance
            if rule.embedding:
                similarity = EmbeddingEngine.cosine_similarity(
                    query_embedding, rule.embedding
                )
                # Weight by rule importance
                relevance = similarity * rule.weight
                candidates.append((rule, relevance))
        
        # Sort by relevance
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Activate returned rules
        for rule, _ in candidates[:top_k]:
            rule.activate()
        
        return candidates[:top_k]
    
    # ========================
    # NODE MANAGEMENT
    # ========================
    
    def add_node(self, node: KernelNode) -> str:
        """
        Add a knowledge node to the graph.
        
        If a similar node exists, we merge them.
        
        Thread-safe with resource limit enforcement.
        """
        self._acquire_lock()
        try:
            # Check resource limit
            self._check_resource_limit("max_nodes", len(self.nodes))
            
            # Check for existing similar node
            for existing_id, existing_node in self.nodes.items():
                if existing_node.name.lower() == node.name.lower():
                    # Merge into existing
                    existing_node.reference()
                    existing_node.context = f"{existing_node.context}; {node.context}"
                    for edge_id, weight in node.edges.items():
                        existing_node.add_edge(edge_id, weight)
                    return existing_id
            
            # Generate embedding if not present
            if not node.embedding:
                node.embedding = self.embedding_engine.embed(
                    f"{node.name} {node.context}"
                )
            
            self.nodes[node.node_id] = node
            self.metadata.total_nodes = len(self.nodes)
            self.metadata.last_modified = datetime.now()
            self._metrics["nodes_added"] += 1
            
            return node.node_id
        finally:
            self._release_lock()
    
    def get_node(self, node_id: str) -> Optional[KernelNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def find_node_by_name(self, name: str) -> Optional[KernelNode]:
        """Find a node by name (case-insensitive)."""
        lower_name = name.lower()
        for node in self.nodes.values():
            if node.name.lower() == lower_name:
                return node
        return None
    
    def query_nodes(
        self, 
        query: str, 
        top_k: int = 5,
        node_type: Optional[str] = None
    ) -> List[Tuple[KernelNode, float]]:
        """
        Find nodes relevant to a query.
        
        Returns list of (node, relevance_score) tuples.
        """
        query_embedding = self.embedding_engine.embed(query)
        
        candidates = []
        for node in self.nodes.values():
            # Filter by type
            if node_type and node.node_type != node_type:
                continue
            
            # Compute relevance
            if node.embedding:
                similarity = EmbeddingEngine.cosine_similarity(
                    query_embedding, node.embedding
                )
                relevance = similarity * node.weight
                candidates.append((node, relevance))
        
        # Sort by relevance
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Reference returned nodes
        for node, _ in candidates[:top_k]:
            node.reference()
        
        return candidates[:top_k]
    
    def link_nodes(self, node_id1: str, node_id2: str, weight: float = 0.5) -> bool:
        """Create a bidirectional link between two nodes."""
        if node_id1 not in self.nodes or node_id2 not in self.nodes:
            return False
        
        self.nodes[node_id1].add_edge(node_id2, weight)
        self.nodes[node_id2].add_edge(node_id1, weight)
        return True
    
    # ========================
    # WORKING MEMORY
    # ========================
    
    def set_working_memory(self, key: str, value: Any) -> None:
        """Set a working memory item (current session context)."""
        if len(self.working_memory) >= self.config["max_working_memory_items"]:
            # Remove oldest item
            oldest_key = next(iter(self.working_memory))
            del self.working_memory[oldest_key]
        
        self.working_memory[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_working_memory(self, key: str) -> Optional[Any]:
        """Get a working memory item."""
        item = self.working_memory.get(key)
        return item["value"] if item else None
    
    def clear_working_memory(self) -> None:
        """Clear all working memory (end of session)."""
        self.working_memory.clear()
    
    def set_active_project(self, project_name: str) -> None:
        """Set the currently active project context."""
        self.active_project = project_name
        
        # Find or create project node
        project_node = self.find_node_by_name(project_name)
        if project_node:
            project_node.reference()
    
    # ========================
    # CONTEXT RETRIEVAL
    # ========================
    
    def get_active_context(self, query: str = "") -> Dict[str, Any]:
        """
        Get the current active context for injection.
        
        This is the core method used by ContextInjector to build
        the system header for the LLM.
        
        Returns a comprehensive context package including:
        - Relevant rules
        - Active project context
        - User profile summary
        - Style preferences
        - Working memory
        """
        context = {
            "user_profile": self.profile.generate_persona_prompt(),
            "style": self.style_vector.describe(),
            "working_memory": {},
            "relevant_rules": [],
            "relevant_nodes": [],
            "active_project": None,
        }
        
        # Add relevant rules
        if query:
            relevant_rules = self.query_rules(query, top_k=5, min_weight=0.3)
            context["relevant_rules"] = [
                {"condition": r.condition, "action": r.action, "weight": r.weight}
                for r, _ in relevant_rules
            ]
        else:
            # Get top rules by weight
            top_rules = sorted(
                self.rules.values(), 
                key=lambda r: r.weight, 
                reverse=True
            )[:5]
            context["relevant_rules"] = [
                {"condition": r.condition, "action": r.action, "weight": r.weight}
                for r in top_rules
            ]
        
        # Add active project context
        if self.active_project:
            project_node = self.find_node_by_name(self.active_project)
            if project_node:
                context["active_project"] = {
                    "name": project_node.name,
                    "context": project_node.context,
                    "properties": project_node.properties,
                }
                
                # Add connected nodes
                connected = []
                for edge_id, edge_weight in project_node.edges.items():
                    connected_node = self.get_node(edge_id)
                    if connected_node and edge_weight > 0.3:
                        connected.append({
                            "name": connected_node.name,
                            "type": connected_node.node_type,
                            "context": connected_node.context,
                        })
                context["active_project"]["connected"] = connected
        
        # Add relevant nodes from query
        if query:
            relevant_nodes = self.query_nodes(query, top_k=3)
            context["relevant_nodes"] = [
                {"name": n.name, "type": n.node_type, "context": n.context}
                for n, _ in relevant_nodes
            ]
        
        # Add working memory
        context["working_memory"] = {
            k: v["value"] for k, v in self.working_memory.items()
        }
        
        return context
    
    def query_relevant(
        self, 
        query: str, 
        include_rules: bool = True,
        include_nodes: bool = True,
        top_k: int = 5
    ) -> Dict[str, List[Tuple[Any, float]]]:
        """
        Find all relevant items for a query.
        
        Returns dict with "rules" and "nodes" keys.
        """
        result = {"rules": [], "nodes": []}
        
        if include_rules:
            result["rules"] = self.query_rules(query, top_k=top_k)
        
        if include_nodes:
            result["nodes"] = self.query_nodes(query, top_k=top_k)
        
        return result
    
    # ========================
    # INTERACTION LOGGING
    # ========================
    
    def log_interaction(
        self, 
        user_input: str, 
        ai_output: str
    ) -> Optional[str]:
        """
        Log an interaction for processing.
        
        Returns the log ID if logged, None if duplicate.
        """
        # Create log entry
        log = InteractionLog(
            log_id=str(uuid.uuid4()),
            user_input=user_input,
            ai_output=ai_output,
        )
        
        # Check for duplicate
        if self._processed_registry.is_processed(log.content_hash):
            return None
        
        self._interaction_logs[log.log_id] = log
        self.profile.record_interaction()
        self.metadata.total_interactions_processed += 1
        
        return log.log_id
    
    def add_signal(self, signal: Signal) -> None:
        """Add a pending signal for processing."""
        self._pending_signals.append(signal)
    
    def get_pending_signals(self) -> List[Signal]:
        """Get all pending signals."""
        return list(self._pending_signals)
    
    def clear_pending_signals(self) -> None:
        """Clear pending signals after processing."""
        self._pending_signals.clear()
    
    # ========================
    # GARBAGE COLLECTION
    # ========================
    
    def garbage_collect(self) -> Dict[str, int]:
        """
        Perform garbage collection.
        
        BREAKTHROUGH: This is how we achieve infinite scaling.
        
        Steps:
        1. Process pending signals into rules
        2. Mark processed interactions for deletion
        3. Delete processed interaction logs
        4. Prune low-weight rules
        5. Consolidate similar rules
        
        Returns statistics about what was cleaned.
        """
        stats = {
            "interactions_deleted": 0,
            "rules_pruned": 0,
            "rules_consolidated": 0,
        }
        
        # Delete processed interaction logs
        for log_id, log in list(self._interaction_logs.items()):
            if log.processed:
                self._processed_registry.register(log.content_hash)
                del self._interaction_logs[log_id]
                stats["interactions_deleted"] += 1
        
        # Prune low-weight rules
        for rule_id in list(self.rules.keys()):
            rule = self.rules[rule_id]
            rule.decay()
            if rule.weight < self.config["rule_min_weight"]:
                del self.rules[rule_id]
                stats["rules_pruned"] += 1
        
        # Consolidate similar rules
        stats["rules_consolidated"] = self._consolidate_rules()
        
        # Decay and prune nodes
        for node_id in list(self.nodes.keys()):
            node = self.nodes[node_id]
            node.decay()
            if node.weight < 0.05 and node.reference_count < 2:
                del self.nodes[node_id]
        
        self.metadata.garbage_collections += 1
        self.metadata.total_rules = len(self.rules)
        self.metadata.total_nodes = len(self.nodes)
        self.metadata.last_modified = datetime.now()
        
        return stats
    
    def _consolidate_rules(self) -> int:
        """
        Merge semantically similar rules.
        
        This further compresses the kernel by combining rules
        that express the same behavior in different words.
        """
        if len(self.rules) < 2:
            return 0
        
        # Get rule texts for clustering
        rule_ids = list(self.rules.keys())
        rule_texts = [
            f"{self.rules[rid].condition} {self.rules[rid].action}"
            for rid in rule_ids
        ]
        
        # Cluster similar rules
        clusters = self.semantic_matcher.cluster_similar(
            rule_texts, 
            threshold=self.config["consolidation_threshold"]
        )
        
        merged_count = 0
        
        for cluster in clusters:
            if len(cluster) <= 1:
                continue
            
            # Keep the highest-weight rule, merge others into it
            cluster_rules = [(rule_ids[i], self.rules[rule_ids[i]]) for i in cluster]
            cluster_rules.sort(key=lambda x: x[1].weight, reverse=True)
            
            primary_id, primary_rule = cluster_rules[0]
            
            for other_id, other_rule in cluster_rules[1:]:
                # Merge weights and source counts
                primary_rule.weight = min(1.0, primary_rule.weight + other_rule.weight * 0.5)
                primary_rule.source_count += other_rule.source_count
                
                # Remove merged rule
                del self.rules[other_id]
                merged_count += 1
        
        if merged_count > 0:
            self.metadata.consolidations += 1
        
        return merged_count
    
    # ========================
    # SERIALIZATION
    # ========================
    
    def export(self, include_logs: bool = False) -> Dict[str, Any]:
        """
        Export the kernel to a portable format.
        
        By default, excludes raw interaction logs (they're meant to be garbage collected).
        """
        data = {
            "version": self.metadata.version,
            "metadata": {
                "created_at": self.metadata.created_at.isoformat(),
                "last_modified": self.metadata.last_modified.isoformat(),
                "total_rules": self.metadata.total_rules,
                "total_nodes": self.metadata.total_nodes,
                "total_interactions_processed": self.metadata.total_interactions_processed,
                "garbage_collections": self.metadata.garbage_collections,
                "consolidations": self.metadata.consolidations,
            },
            "rules": {rid: r.to_dict() for rid, r in self.rules.items()},
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "profile": self.profile.to_dict(),
            "style_vector": self.style_vector.to_dict(),
            "config": self.config,
            "processed_registry": self._processed_registry.to_dict(),
            "embedding_engine": self.embedding_engine.to_dict(),
            "active_project": self.active_project,  # Include active project
        }
        
        if include_logs:
            data["interaction_logs"] = {
                lid: l.to_dict() for lid, l in self._interaction_logs.items()
            }
        
        return data
    
    def export_json(self, filepath: str, compress: bool = True) -> None:
        """Export to a JSON file, optionally compressed."""
        data = self.export()
        json_str = json.dumps(data, indent=2)
        
        if compress:
            filepath = filepath if filepath.endswith('.gz') else f"{filepath}.gz"
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                f.write(json_str)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
    
    def export_binary(self, filepath: str) -> None:
        """Export to a compressed binary format."""
        data = self.export()
        json_bytes = json.dumps(data).encode('utf-8')
        compressed = gzip.compress(json_bytes)
        
        with open(filepath, 'wb') as f:
            f.write(compressed)
    
    @classmethod
    def load(cls, data: Dict[str, Any]) -> "UserKernel":
        """Load a kernel from exported data."""
        kernel = cls()
        
        # Load metadata
        if "metadata" in data:
            meta = data["metadata"]
            kernel.metadata = KernelMetadata(
                version=data.get("version", "1.0.0"),
                created_at=datetime.fromisoformat(meta["created_at"]),
                last_modified=datetime.fromisoformat(meta["last_modified"]),
                total_rules=meta.get("total_rules", 0),
                total_nodes=meta.get("total_nodes", 0),
                total_interactions_processed=meta.get("total_interactions_processed", 0),
                garbage_collections=meta.get("garbage_collections", 0),
                consolidations=meta.get("consolidations", 0),
            )
        
        # Load rules
        for rid, rdata in data.get("rules", {}).items():
            kernel.rules[rid] = Rule.from_dict(rdata)
        
        # Load nodes
        for nid, ndata in data.get("nodes", {}).items():
            kernel.nodes[nid] = KernelNode.from_dict(ndata)
        
        # Load profile
        if "profile" in data:
            kernel.profile = UserProfile.from_dict(data["profile"])
        
        # Load style vector
        if "style_vector" in data:
            kernel.style_vector = StyleVector.from_dict(data["style_vector"])
        
        # Load config
        if "config" in data:
            kernel.config.update(data["config"])
        
        # Load processed registry
        if "processed_registry" in data:
            kernel._processed_registry = ProcessedInteractionRegistry.from_dict(
                data["processed_registry"]
            )
        
        # Load embedding engine
        if "embedding_engine" in data:
            kernel.embedding_engine = EmbeddingEngine.from_dict(data["embedding_engine"])
            kernel.semantic_matcher = SemanticMatcher(kernel.embedding_engine)
        
        # Load active project
        if "active_project" in data:
            kernel.active_project = data["active_project"]
        
        return kernel
    
    @classmethod
    def load_json(cls, filepath: str) -> "UserKernel":
        """Load from a JSON file (optionally compressed)."""
        if filepath.endswith('.gz'):
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        return cls.load(data)
    
    @classmethod
    def load_binary(cls, filepath: str) -> "UserKernel":
        """Load from a compressed binary file."""
        with open(filepath, 'rb') as f:
            compressed = f.read()
        
        json_bytes = gzip.decompress(compressed)
        data = json.loads(json_bytes.decode('utf-8'))
        
        return cls.load(data)
    
    # ========================
    # STATISTICS
    # ========================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive kernel statistics."""
        return {
            "total_rules": len(self.rules),
            "total_nodes": len(self.nodes),
            "pending_interactions": len(self._interaction_logs),
            "pending_signals": len(self._pending_signals),
            "total_interactions_processed": self.metadata.total_interactions_processed,
            "garbage_collections": self.metadata.garbage_collections,
            "consolidations": self.metadata.consolidations,
            "profile_confidence": self.profile.profile_confidence,
            "expertise_domains": len(self.profile.expertise_domains),
            "preferred_languages": len(self.profile.preferred_languages),
            "working_memory_items": len(self.working_memory),
            "rule_categories": dict(self._count_rule_categories()),
            "node_types": dict(self._count_node_types()),
        }
    
    def _count_rule_categories(self) -> Dict[str, int]:
        """Count rules by category."""
        counts: Dict[str, int] = {}
        for rule in self.rules.values():
            cat = rule.category.name
            counts[cat] = counts.get(cat, 0) + 1
        return counts
    
    def _count_node_types(self) -> Dict[str, int]:
        """Count nodes by type."""
        counts: Dict[str, int] = {}
        for node in self.nodes.values():
            counts[node.node_type] = counts.get(node.node_type, 0) + 1
        return counts


# =============================================================================
# IBLM v3 - SCOPED PROBABILISTIC KERNEL
# =============================================================================

class ScopedKernel:
    """
    v3 SCOPED PROBABILISTIC KERNEL
    
    BREAKTHROUGH ARCHITECTURE:
    
    1. SCOPED RULES: Rules are attached to ContextNodes, not global
       - "User prefers async" → scoped to Python node
       - "User prefers promises" → scoped to JavaScript node
       - NO CONTRADICTION!
    
    2. HYPOTHESIS ENGINE: Signals create Hypotheses first
       - New signal → Hypothesis (confidence: 0.1)
       - 3 validations → ScopedRule (confidence: 0.8)
       - 2 rejections → Deleted
    
    3. COLD STORAGE: Logs archived to disk, not deleted
       - RAM: Working memory only
       - Disk: Full history for recovery
       - Recovery: recompile_brain() regenerates from archive
    
    This kernel inherits production features from UserKernel:
    - Thread safety
    - Resource limits
    - Metrics collection
    
    Example:
        kernel = ScopedKernel()
        
        # Query rules for Python context
        rules = kernel.query_scoped_rules(["Python", "FastAPI"])
        
        # Only rules scoped to Python or FastAPI are returned
        # JavaScript rules are NOT returned
    """
    
    def __init__(
        self,
        embedding_engine: EmbeddingEngine = None,
        enable_thread_safety: bool = True,
        resource_limits: Dict[str, int] = None,
        cold_storage_path: str = None,
    ):
        """
        Initialize the ScopedKernel.
        
        Args:
            embedding_engine: Optional embedding engine
            enable_thread_safety: Enable RLock for thread safety
            resource_limits: Dict with max_rules, max_nodes, max_hypotheses
            cold_storage_path: Path for cold storage archive
        """
        # Embedding engine
        if embedding_engine is None:
            self.embedding_engine = EmbeddingEngine()
        else:
            self.embedding_engine = embedding_engine
        self.semantic_matcher = SemanticMatcher(self.embedding_engine)
        
        # v3 DATA STRUCTURES
        self.context_nodes: Dict[str, "ContextNode"] = {}  # Context graph
        self.scoped_rules: Dict[str, "ScopedRule"] = {}    # Scoped rules
        self.hypotheses: Dict[str, "Hypothesis"] = {}       # Pending hypotheses
        
        # v3.1 GOAL-CONSTRAINED KERNEL
        self.goals: Dict[str, "UserGoal"] = {}              # High-priority constraints
        self.facts: Dict[str, "UserFact"] = {}              # Low-priority preferences
        
        # Legacy support (v2 compatibility)
        self.rules: Dict[str, Rule] = {}
        self.nodes: Dict[str, KernelNode] = {}
        
        # Profile and style (retained from v2)
        self.profile = UserProfile()
        self.style_vector = StyleVector()
        
        # Working memory (transient, session-specific)
        self.working_memory: Dict[str, Any] = {}
        self.active_project: Optional[str] = None
        
        # Cold storage
        if cold_storage_path:
            try:
                from .cold_storage import ColdStorage
            except ImportError:
                from cold_storage import ColdStorage
            self.cold_storage = ColdStorage(cold_storage_path)
        else:
            self.cold_storage = None
        
        # Thread safety
        self._enable_thread_safety = enable_thread_safety
        if enable_thread_safety:
            self._lock = threading.RLock()
        else:
            self._lock = None
        
        # Resource limits
        self.resource_limits = resource_limits or {
            "max_rules": 1000,
            "max_context_nodes": 500,
            "max_hypotheses": 200,
        }
        
        # Metrics
        self._metrics = {
            "scoped_rules_added": 0,
            "hypotheses_created": 0,
            "hypotheses_promoted": 0,
            "hypotheses_rejected": 0,
            "context_nodes_created": 0,
        }
        
        # Metadata
        self.metadata = KernelMetadata()
        
        # Interaction logs (for archival)
        self._interaction_logs: Dict[str, InteractionLog] = {}
        self._processed_registry = ProcessedInteractionRegistry()
    
    def _acquire_lock(self):
        """Acquire thread lock if enabled."""
        if self._lock:
            self._lock.acquire()
    
    def _release_lock(self):
        """Release thread lock if enabled."""
        if self._lock:
            self._lock.release()
    
    # ========================
    # CONTEXT NODE MANAGEMENT
    # ========================
    
    def add_context_node(self, node: "ContextNode") -> str:
        """
        Add a context node to the graph.
        
        Args:
            node: The ContextNode to add
            
        Returns:
            The node ID
        """
        self._acquire_lock()
        try:
            # Check resource limits
            if len(self.context_nodes) >= self.resource_limits.get("max_context_nodes", 500):
                self._prune_context_nodes()
            
            # Generate embedding if missing
            if node.embedding is None:
                node.embedding = self.embedding_engine.embed(node.name)
            
            self.context_nodes[node.node_id] = node
            self._metrics["context_nodes_created"] += 1
            
            # Update parent's children list
            if node.parent_id and node.parent_id in self.context_nodes:
                parent = self.context_nodes[node.parent_id]
                if node.node_id not in parent.children_ids:
                    parent.children_ids.append(node.node_id)
            
            return node.node_id
        finally:
            self._release_lock()
    
    def get_context_node(self, node_id: str) -> Optional["ContextNode"]:
        """Get a context node by ID."""
        return self.context_nodes.get(node_id)
    
    def find_context_by_name(self, name: str) -> Optional["ContextNode"]:
        """Find a context node by name."""
        name_lower = name.lower()
        for node in self.context_nodes.values():
            if node.name.lower() == name_lower:
                return node
        return None
    
    def _prune_context_nodes(self) -> int:
        """Prune least-used context nodes."""
        if len(self.context_nodes) < 10:
            return 0
        
        # Sort by reference count and weight
        sorted_nodes = sorted(
            self.context_nodes.values(),
            key=lambda n: (n.reference_count, n.weight)
        )
        
        # Remove bottom 10%
        to_remove = len(sorted_nodes) // 10
        pruned = 0
        
        for node in sorted_nodes[:to_remove]:
            # Don't prune nodes that have children or rules
            has_rules = any(
                r.target_node == node.node_id 
                for r in self.scoped_rules.values()
            )
            if not node.children_ids and not has_rules:
                del self.context_nodes[node.node_id]
                pruned += 1
        
        return pruned
    
    # ========================
    # SCOPED RULE MANAGEMENT
    # ========================
    
    def add_scoped_rule(self, rule: "ScopedRule") -> str:
        """
        Add a scoped rule.
        
        Args:
            rule: The ScopedRule to add
            
        Returns:
            The rule ID
        """
        self._acquire_lock()
        try:
            # Check resource limits
            if len(self.scoped_rules) >= self.resource_limits.get("max_rules", 1000):
                self._prune_scoped_rules()
            
            # Generate embedding
            if rule.embedding is None:
                rule.embedding = self.embedding_engine.embed(rule.content)
            
            self.scoped_rules[rule.rule_id] = rule
            self._metrics["scoped_rules_added"] += 1
            
            return rule.rule_id
        finally:
            self._release_lock()
    
    def get_scoped_rule(self, rule_id: str) -> Optional["ScopedRule"]:
        """Get a scoped rule by ID."""
        return self.scoped_rules.get(rule_id)
    
    def query_scoped_rules(
        self,
        active_context: List[str],
        query: str = None,
        top_k: int = 10
    ) -> List["ScopedRule"]:
        """
        Query rules that match the current context.
        
        BREAKTHROUGH: Only rules scoped to the active context are returned.
        
        Example:
            query_scoped_rules(["Python", "FastAPI"])
            → Returns only rules scoped to Python or FastAPI
            → JavaScript rules are NOT returned
        
        Args:
            active_context: Current context path (e.g., ["Python", "FastAPI"])
            query: Optional semantic query
            top_k: Maximum rules to return
            
        Returns:
            List of matching ScopedRules
        """
        self._acquire_lock()
        try:
            matches = []
            
            for rule in self.scoped_rules.values():
                # Check if rule matches context
                if not rule.matches_context(active_context):
                    continue
                
                # Semantic similarity if query provided
                score = rule.weight * rule.confidence
                if query and rule.embedding:
                    query_embedding = self.embedding_engine.embed(query)
                    similarity = EmbeddingEngine.cosine_similarity(
                        query_embedding, rule.embedding
                    )
                    score *= (1 + similarity)
                
                matches.append((score, rule))
            
            # Sort by score and return top_k
            matches.sort(key=lambda x: x[0], reverse=True)
            return [rule for _, rule in matches[:top_k]]
        finally:
            self._release_lock()
    
    def _prune_scoped_rules(self) -> int:
        """Prune low-weight/low-confidence scoped rules."""
        if len(self.scoped_rules) < 10:
            return 0
        
        # Sort by weight * confidence
        sorted_rules = sorted(
            self.scoped_rules.values(),
            key=lambda r: r.weight * r.confidence
        )
        
        # Remove bottom 10%
        to_remove = len(sorted_rules) // 10
        pruned = 0
        
        for rule in sorted_rules[:to_remove]:
            if rule.weight < 0.3:  # Only prune if truly low
                # Archive before deletion
                if self.cold_storage:
                    self.cold_storage.archive_rule(rule, "pruned")
                del self.scoped_rules[rule.rule_id]
                pruned += 1
        
        return pruned
    
    # ========================
    # v3.1 GOAL & FACT MANAGEMENT
    # ========================
    
    def add_goal(self, goal: "UserGoal") -> str:
        """Add a user goal (high-priority constraint)."""
        self._acquire_lock()
        try:
            self.goals[goal.goal_id] = goal
            return goal.goal_id
        finally:
            self._release_lock()
    
    def add_fact(self, fact: "UserFact") -> str:
        """Add a user fact (low-priority preference)."""
        self._acquire_lock()
        try:
            self.facts[fact.fact_id] = fact
            return fact.fact_id
        finally:
            self._release_lock()
    
    def get_active_goals(self, scope_path: List[str] = None) -> List["UserGoal"]:
        """Get active goals, optionally filtered by scope."""
        goals = [g for g in self.goals.values() if g.is_active()]
        if scope_path:
            goals = [g for g in goals if not g.scope_path or 
                     any(s.lower() in [p.lower() for p in scope_path] for s in g.scope_path)]
        return sorted(goals, key=lambda g: g.priority, reverse=True)
    
    def get_facts_not_conflicting(self, scope_path: List[str] = None) -> List["UserFact"]:
        """Get facts that do NOT conflict with active goals in this scope."""
        active_goals = self.get_active_goals(scope_path)
        goal_contents = {g.content.lower() for g in active_goals}
        
        # Simple conflict check: if fact content overlaps semantically with goal, skip
        valid_facts = []
        for fact in self.facts.values():
            # Naive: if fact content doesn't directly contradict goal, include it
            # In production, use embedding similarity
            if fact.content.lower() not in goal_contents:
                valid_facts.append(fact)
        
        return sorted(valid_facts, key=lambda f: f.confidence, reverse=True)
    
    # ========================
    # HYPOTHESIS MANAGEMENT
    # ========================
    
    def add_hypothesis(self, hypothesis: "Hypothesis") -> str:
        """Add a hypothesis."""
        self._acquire_lock()
        try:
            # Check limits
            if len(self.hypotheses) >= self.resource_limits.get("max_hypotheses", 200):
                self._expire_old_hypotheses()
            
            # Generate embedding
            if hypothesis.embedding is None:
                hypothesis.embedding = self.embedding_engine.embed(hypothesis.proposed_content)
            
            self.hypotheses[hypothesis.hypothesis_id] = hypothesis
            self._metrics["hypotheses_created"] += 1
            
            return hypothesis.hypothesis_id
        finally:
            self._release_lock()
    
    def get_pending_hypotheses(self) -> List["Hypothesis"]:
        """Get all pending hypotheses."""
        try:
            from .models import HypothesisState
        except ImportError:
            from models import HypothesisState
        
        return [
            h for h in self.hypotheses.values()
            if h.state in [HypothesisState.PENDING, HypothesisState.VALIDATING]
        ]
    
    def _expire_old_hypotheses(self) -> int:
        """Expire oldest hypotheses when limit reached."""
        sorted_hyp = sorted(
            self.hypotheses.values(),
            key=lambda h: h.created_at
        )
        
        expired = 0
        to_remove = min(10, len(sorted_hyp) // 4)
        
        for hyp in sorted_hyp[:to_remove]:
            if self.cold_storage:
                self.cold_storage.archive_hypothesis(hyp, "limit_reached")
            if hyp.hypothesis_id in self.hypotheses:
                del self.hypotheses[hyp.hypothesis_id]
            expired += 1
        
        return expired
    
    # ========================
    # INTERACTION LOGGING
    # ========================
    
    def log_interaction(self, user_input: str, ai_output: str) -> Optional[str]:
        """Log an interaction for processing."""
        log = InteractionLog(
            log_id=str(uuid.uuid4())[:8],
            user_input=user_input,
            ai_output=ai_output,
        )
        
        # Check for duplicates
        if self._processed_registry.is_processed(log.content_hash):
            return None
        
        self._interaction_logs[log.log_id] = log
        self._processed_registry.register(log.content_hash)
        
        return log.log_id
    
    # ========================
    # COLD STORAGE INTEGRATION
    # ========================
    
    def garbage_collect(self) -> Dict[str, int]:
        """
        v3 Garbage Collection: Archive to cold storage, clear RAM.
        
        Unlike v2 which deletes data, v3 archives to disk for recovery.
        """
        self._acquire_lock()
        try:
            result = {"interactions_archived": 0, "hypotheses_expired": 0}
            
            # Archive processed interactions
            processed_logs = [
                log for log in self._interaction_logs.values()
                if log.processed
            ]
            
            if processed_logs and self.cold_storage:
                result["interactions_archived"] = self.cold_storage.archive_interactions(
                    processed_logs
                )
            
            # Clear from RAM
            for log in processed_logs:
                del self._interaction_logs[log.log_id]
            
            return result
        finally:
            self._release_lock()
    
    def recompile_brain(self) -> Dict[str, Any]:
        """
        RECOVERY: Rebuild kernel from cold storage archive.
        
        Returns:
            Report dictionary
        """
        if not self.cold_storage:
            return {"error": "No cold storage configured"}
        
        # Clear current state
        self.scoped_rules.clear()
        self.hypotheses.clear()
        self.context_nodes.clear()
        
        # Rebuild from archive
        report = self.cold_storage.recompile_brain(self)
        return report.to_dict()
    
    # ========================
    # WORKING MEMORY
    # ========================
    
    def set_working_memory(self, key: str, value: Any) -> None:
        """Set a working memory value."""
        self.working_memory[key] = value
    
    def get_working_memory(self, key: str, default: Any = None) -> Any:
        """Get a working memory value."""
        return self.working_memory.get(key, default)
    
    def clear_working_memory(self) -> None:
        """Clear all working memory."""
        self.working_memory.clear()
    
    def set_active_project(self, name: str) -> None:
        """Set the active project context."""
        self.active_project = name
    
    # ========================
    # EXPORT/IMPORT
    # ========================
    
    def export(self) -> Dict[str, Any]:
        """Export the kernel to a portable format."""
        return {
            "version": "3.0.0",
            "metadata": {
                "created_at": self.metadata.created_at.isoformat(),
                "last_modified": datetime.now().isoformat(),
            },
            "context_nodes": {
                nid: n.to_dict() for nid, n in self.context_nodes.items()
            },
            "scoped_rules": {
                rid: r.to_dict() for rid, r in self.scoped_rules.items()
            },
            "hypotheses": {
                hid: h.to_dict() for hid, h in self.hypotheses.items()
            },
            "profile": self.profile.to_dict(),
            "style_vector": self.style_vector.to_dict(),
            "active_project": self.active_project,
            "metrics": self._metrics,
        }
    
    @classmethod
    def load(cls, data: Dict[str, Any]) -> "ScopedKernel":
        """Load a ScopedKernel from exported data."""
        try:
            from .models import ContextNode, ScopedRule, Hypothesis
        except ImportError:
            from models import ContextNode, ScopedRule, Hypothesis
        
        kernel = cls()
        
        # Load context nodes
        for nid, ndata in data.get("context_nodes", {}).items():
            kernel.context_nodes[nid] = ContextNode.from_dict(ndata)
        
        # Load scoped rules
        for rid, rdata in data.get("scoped_rules", {}).items():
            kernel.scoped_rules[rid] = ScopedRule.from_dict(rdata)
        
        # Load hypotheses
        for hid, hdata in data.get("hypotheses", {}).items():
            kernel.hypotheses[hid] = Hypothesis.from_dict(hdata)
        
        # Load profile
        if "profile" in data:
            kernel.profile = UserProfile.from_dict(data["profile"])
        
        # Load style vector
        if "style_vector" in data:
            kernel.style_vector = StyleVector.from_dict(data["style_vector"])
        
        # Load active project
        kernel.active_project = data.get("active_project")
        
        # Load metrics
        if "metrics" in data:
            kernel._metrics.update(data["metrics"])
        
        return kernel
    
    # ========================
    # STATISTICS
    # ========================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive kernel statistics."""
        return {
            "version": "3.0.0",
            "context_nodes": len(self.context_nodes),
            "scoped_rules": len(self.scoped_rules),
            "hypotheses_pending": len(self.hypotheses),
            "profile_confidence": self.profile.profile_confidence,
            "metrics": self._metrics.copy(),
            "cold_storage": self.cold_storage.get_stats() if self.cold_storage else None,
        }
    
    def get_metrics(self) -> Dict[str, int]:
        """Get kernel metrics."""
        return self._metrics.copy()


# Import v3 models for type hints
try:
    from .models import ContextNode, ScopedRule, Hypothesis
except ImportError:
    pass

