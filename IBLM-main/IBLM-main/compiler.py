"""
IBLM Core - Logic Compiler
==========================

The Brain of the IBLM: converts signals to rules and implements evolve().

BREAKTHROUGH CONCEPT:
This is where the magic happens. The LogicCompiler takes raw signals
from the InteractionObserver and COMPILES them into behavioral rules.

Key Innovations:
1. RULE GENERATION: Signals are grouped and compiled into rules
2. WEIGHT UPDATES: User corrections cause immediate weight changes
3. GARBAGE COLLECTION: Source interactions are DELETED after compilation
4. EVOLUTION: The evolve() method enables real-time self-correction

The evolve() method is the core innovation:
- Detects contradictions with existing rules
- Immediately rewrites memory when contradicted
- Applies time-based decay to prevent stale rules
- Consolidates similar rules to compress the kernel
"""

import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict

try:
    from .models import (
        Signal, SignalType, Rule, RuleCategory, KernelNode,
        StyleVector, UserProfile
    )
    from .kernel import UserKernel
    from .embeddings import EmbeddingEngine, SemanticMatcher
except ImportError:
    from models import (
        Signal, SignalType, Rule, RuleCategory, KernelNode,
        StyleVector, UserProfile
    )
    from kernel import UserKernel
    from embeddings import EmbeddingEngine, SemanticMatcher


@dataclass
class EvolutionReport:
    """Report of what changed during an evolve() call."""
    rules_created: int = 0
    rules_updated: int = 0
    rules_contradicted: int = 0
    rules_pruned: int = 0
    rules_consolidated: int = 0
    nodes_created: int = 0
    nodes_updated: int = 0
    profile_updates: List[str] = field(default_factory=list)
    style_updates: List[str] = field(default_factory=list)
    interactions_garbage_collected: int = 0
    
    def __str__(self) -> str:
        parts = []
        if self.rules_created:
            parts.append(f"+{self.rules_created} rules")
        if self.rules_updated:
            parts.append(f"~{self.rules_updated} updated")
        if self.rules_contradicted:
            parts.append(f"!{self.rules_contradicted} contradicted")
        if self.rules_pruned:
            parts.append(f"-{self.rules_pruned} pruned")
        if self.interactions_garbage_collected:
            parts.append(f"GC:{self.interactions_garbage_collected}")
        return ", ".join(parts) if parts else "no changes"


@dataclass
class SignalCluster:
    """A cluster of related signals ready for rule compilation."""
    signals: List[Signal]
    category: RuleCategory
    condition: str
    action: str
    confidence: float
    

class LogicCompiler:
    """
    The Brain of IBLM - compiles signals into rules and enables self-correction.
    
    ARCHITECTURE:
    
    Signals → Clustering → Rule Generation → Garbage Collection
                ↓
    Existing Rules ← Contradiction Detection ← evolve()
                ↓
    Weight Updates → Pruning → Consolidation
    
    CRITICAL METHOD: evolve()
    
    The evolve() method is the core innovation. It:
    1. Takes new signals from the Observer
    2. Detects contradictions with existing rules
    3. Updates weights based on reinforcement/contradiction
    4. Compiles signal clusters into new rules
    5. Garbage collects processed interactions
    6. Prunes low-weight rules
    7. Consolidates similar rules
    
    This enables the IBLM to learn and adapt in real-time.
    """
    
    # Weight adjustment constants
    CORRECTION_WEIGHT_BOOST = 0.3      # Boost for correction signals (high value)
    REINFORCEMENT_BOOST = 0.1          # Boost for reinforcing behavior
    CONTRADICTION_PENALTY = 0.5        # Penalty when contradicted
    REPEATED_PATTERN_MULTIPLIER = 1.5  # Multiplier for repeated patterns
    
    # Thresholds
    MIN_SIGNALS_FOR_RULE = 2           # Minimum signals to compile a rule
    MIN_CONFIDENCE_FOR_RULE = 0.5      # Minimum confidence for rule creation
    SIMILARITY_THRESHOLD = 0.75        # Threshold for semantic similarity
    
    def __init__(self, kernel: UserKernel):
        self.kernel = kernel
        self.embedding_engine = kernel.embedding_engine
        self.semantic_matcher = kernel.semantic_matcher
        
        # Signal to rule category mapping
        self._category_map = {
            SignalType.CORRECTION: RuleCategory.BEHAVIORAL_PATTERN,
            SignalType.PREFERENCE: RuleCategory.TECHNICAL_PREFERENCE,
            SignalType.STYLE: RuleCategory.COMMUNICATION_STYLE,
            SignalType.ENTITY: RuleCategory.PROJECT_CONTEXT,
            SignalType.EXPERTISE: RuleCategory.DOMAIN_EXPERTISE,
            SignalType.AVERSION: RuleCategory.TECHNICAL_PREFERENCE,
            SignalType.CONTEXT: RuleCategory.PROJECT_CONTEXT,
            SignalType.PERSONALITY: RuleCategory.PERSONALITY_TRAIT,
            SignalType.GOAL: RuleCategory.PROJECT_CONTEXT,
            SignalType.WORKFLOW: RuleCategory.WORKFLOW_PATTERN,
        }
    
    def evolve(self, signals: List[Signal]) -> EvolutionReport:
        """
        The core evolution algorithm.
        
        BREAKTHROUGH: This method enables real-time self-correction.
        
        Algorithm:
        
        1. CONTRADICTION DETECTION
           For each new signal, check existing rules.
           If signal contradicts a rule, mark rule for revision.
           
        2. WEIGHT ADJUSTMENT
           - Correction signals: +0.3 weight to corrected behavior
           - Repeated patterns: exponential weight increase
           - Contradicted rules: -0.5 weight penalty
           
        3. RULE COMPILATION
           If signal cluster count > THRESHOLD and confidence > MIN_CONFIDENCE:
           - Generate rule from signals
           - DELETE source interactions (garbage collection)
           
        4. PROFILE & STYLE UPDATES
           Update user profile and style vector based on signals.
           
        5. NODE MANAGEMENT
           Create/update knowledge nodes for entities.
           
        6. DECAY & PRUNING
           Apply time-based decay to all weights.
           Remove rules below MIN_WEIGHT threshold.
           
        7. CONSOLIDATION
           Merge semantically similar rules.
           Combine weights, average embeddings.
        
        Args:
            signals: New signals to process
            
        Returns:
            EvolutionReport with statistics about what changed
        """
        report = EvolutionReport()
        
        if not signals:
            return report
        
        # Step 1 & 2: Contradiction detection and weight adjustment
        for signal in signals:
            if signal.signal_type == SignalType.CORRECTION:
                contradictions = self._detect_contradictions(signal)
                for rule_id, similarity in contradictions:
                    rule = self.kernel.get_rule(rule_id)
                    if rule:
                        rule.contradict(self.CONTRADICTION_PENALTY * similarity)
                        report.rules_contradicted += 1
        
        # Group signals by type and content similarity
        signal_clusters = self._cluster_signals(signals)
        
        # Step 3: Rule compilation from clusters
        for cluster in signal_clusters:
            # Check if we should create a new rule
            if self._should_compile_rule(cluster):
                rule = self._compile_rule(cluster)
                if rule:
                    self.kernel.add_rule(rule)
                    report.rules_created += 1
            else:
                # Try to reinforce existing rules
                reinforced = self._reinforce_existing_rules(cluster)
                report.rules_updated += reinforced
        
        # Step 4: Update user profile and style
        profile_updates = self._update_profile(signals)
        report.profile_updates = profile_updates
        
        style_updates = self._update_style(signals)
        report.style_updates = style_updates
        
        # Step 5: Create/update nodes for entities
        for signal in signals:
            if signal.signal_type == SignalType.ENTITY:
                if self._create_or_update_node(signal):
                    report.nodes_created += 1
                else:
                    report.nodes_updated += 1
        
        # Step 6: Decay and pruning
        gc_result = self.kernel.garbage_collect()
        report.rules_pruned = gc_result["rules_pruned"]
        report.rules_consolidated = gc_result["rules_consolidated"]
        report.interactions_garbage_collected = gc_result["interactions_deleted"]
        
        # Clear processed signals
        self.kernel.clear_pending_signals()
        
        return report
    
    def _detect_contradictions(self, signal: Signal) -> List[Tuple[str, float]]:
        """
        Detect rules that contradict a signal.
        
        Returns list of (rule_id, similarity) tuples.
        """
        contradictions = []
        
        if signal.signal_type != SignalType.CORRECTION:
            return contradictions
        
        signal_embedding = self.embedding_engine.embed(signal.content)
        
        for rule_id, rule in self.kernel.rules.items():
            if rule.embedding:
                similarity = EmbeddingEngine.cosine_similarity(
                    signal_embedding, rule.embedding
                )
                
                # High similarity with a correction signal suggests contradiction
                if similarity > 0.5:
                    # Check for explicit negation
                    is_negation = any(
                        neg in signal.content.lower()
                        for neg in ['not', 'no', "don't", 'stop', 'avoid', 'instead']
                    )
                    
                    if is_negation:
                        contradictions.append((rule_id, similarity))
        
        return contradictions
    
    def _cluster_signals(self, signals: List[Signal]) -> List[SignalCluster]:
        """
        Group related signals into clusters for rule compilation.
        """
        clusters: List[SignalCluster] = []
        
        # Group by signal type first
        by_type: Dict[SignalType, List[Signal]] = defaultdict(list)
        for signal in signals:
            by_type[signal.signal_type].append(signal)
        
        # For each type, cluster by semantic similarity
        for signal_type, type_signals in by_type.items():
            if len(type_signals) == 1:
                # Single signal becomes its own cluster
                signal = type_signals[0]
                clusters.append(SignalCluster(
                    signals=[signal],
                    category=self._category_map.get(signal_type, RuleCategory.BEHAVIORAL_PATTERN),
                    condition=self._generate_condition(signal),
                    action=self._generate_action(signal),
                    confidence=signal.confidence,
                ))
            else:
                # Cluster by semantic similarity
                texts = [s.content for s in type_signals]
                similar_clusters = self.semantic_matcher.cluster_similar(
                    texts, threshold=self.SIMILARITY_THRESHOLD
                )
                
                for indices in similar_clusters:
                    cluster_signals = [type_signals[i] for i in indices]
                    avg_confidence = sum(s.confidence for s in cluster_signals) / len(cluster_signals)
                    
                    # Generate condition and action from cluster
                    condition = self._generate_cluster_condition(cluster_signals)
                    action = self._generate_cluster_action(cluster_signals)
                    
                    clusters.append(SignalCluster(
                        signals=cluster_signals,
                        category=self._category_map.get(signal_type, RuleCategory.BEHAVIORAL_PATTERN),
                        condition=condition,
                        action=action,
                        confidence=avg_confidence,
                    ))
        
        return clusters
    
    def _should_compile_rule(self, cluster: SignalCluster) -> bool:
        """Determine if a signal cluster should be compiled into a rule."""
        # Check cluster size
        if len(cluster.signals) < self.MIN_SIGNALS_FOR_RULE:
            # Single signals with high confidence can still become rules
            if cluster.signals and cluster.signals[0].confidence >= 0.8:
                return True
            return False
        
        # Check confidence
        if cluster.confidence < self.MIN_CONFIDENCE_FOR_RULE:
            return False
        
        # Check if similar rule exists (would be reinforced instead)
        existing = self._find_similar_rule(cluster)
        if existing:
            return False
        
        return True
    
    def _compile_rule(self, cluster: SignalCluster) -> Optional[Rule]:
        """
        Compile a signal cluster into a behavioral rule.
        
        BREAKTHROUGH: This is where raw signals become compiled knowledge.
        """
        if not cluster.signals:
            return None
        
        # Calculate weight based on signal strength
        base_weight = cluster.confidence
        
        # Boost for correction signals
        has_correction = any(
            s.signal_type == SignalType.CORRECTION for s in cluster.signals
        )
        if has_correction:
            base_weight = min(1.0, base_weight + self.CORRECTION_WEIGHT_BOOST)
        
        # Boost for repeated patterns
        if len(cluster.signals) > 2:
            base_weight = min(1.0, base_weight * self.REPEATED_PATTERN_MULTIPLIER)
        
        # Generate embedding
        combined_text = f"{cluster.condition} {cluster.action}"
        embedding = self.embedding_engine.embed(combined_text)
        
        rule = Rule(
            rule_id=str(uuid.uuid4()),
            category=cluster.category,
            condition=cluster.condition,
            action=cluster.action,
            weight=base_weight,
            embedding=embedding,
            source_count=len(cluster.signals),
        )
        
        return rule
    
    def _reinforce_existing_rules(self, cluster: SignalCluster) -> int:
        """Reinforce existing rules that match a signal cluster."""
        reinforced = 0
        
        # Find similar existing rules
        similar = self._find_similar_rule(cluster)
        if similar:
            rule_id, similarity = similar
            rule = self.kernel.get_rule(rule_id)
            if rule:
                # Boost proportional to similarity and cluster confidence
                boost = self.REINFORCEMENT_BOOST * similarity * cluster.confidence
                rule.reinforce(boost)
                reinforced += 1
        
        return reinforced
    
    def _find_similar_rule(self, cluster: SignalCluster) -> Optional[Tuple[str, float]]:
        """Find an existing rule similar to a signal cluster."""
        combined_text = f"{cluster.condition} {cluster.action}"
        cluster_embedding = self.embedding_engine.embed(combined_text)
        
        best_match = None
        best_similarity = 0.0
        
        for rule_id, rule in self.kernel.rules.items():
            if rule.category != cluster.category:
                continue
            
            if rule.embedding:
                similarity = EmbeddingEngine.cosine_similarity(
                    cluster_embedding, rule.embedding
                )
                if similarity > self.SIMILARITY_THRESHOLD and similarity > best_similarity:
                    best_match = rule_id
                    best_similarity = similarity
        
        return (best_match, best_similarity) if best_match else None
    
    def _generate_condition(self, signal: Signal) -> str:
        """Generate a rule condition from a signal."""
        type_conditions = {
            SignalType.CORRECTION: "When generating responses",
            SignalType.PREFERENCE: "When making technical choices",
            SignalType.STYLE: "When communicating",
            SignalType.AVERSION: "When considering options",
            SignalType.EXPERTISE: "When explaining concepts",
            SignalType.ENTITY: f"When working on {signal.metadata.get('type', 'project')}",
            SignalType.GOAL: "When planning work",
            SignalType.PERSONALITY: "When interacting",
            SignalType.CONTEXT: "When providing context",
            SignalType.WORKFLOW: "When following workflow",
        }
        return type_conditions.get(signal.signal_type, "Always")
    
    def _generate_action(self, signal: Signal) -> str:
        """Generate a rule action from a signal."""
        content = signal.content
        
        # Clean up the action based on signal type
        if signal.signal_type == SignalType.CORRECTION:
            if content.startswith("Prefer:"):
                return content
            return f"Follow: {content}"
        elif signal.signal_type == SignalType.PREFERENCE:
            return f"Prefer: {content}"
        elif signal.signal_type == SignalType.AVERSION:
            return content if content.startswith("Avoid:") else f"Avoid: {content}"
        elif signal.signal_type == SignalType.STYLE:
            return f"Adopt: {content.replace('style:', '')}"
        elif signal.signal_type == SignalType.EXPERTISE:
            return f"Acknowledge: {content}"
        elif signal.signal_type == SignalType.GOAL:
            return f"Support goal: {content}"
        else:
            return f"Apply: {content}"
    
    def _generate_cluster_condition(self, signals: List[Signal]) -> str:
        """Generate a condition from a cluster of signals."""
        # Use the first signal's type to determine condition pattern
        if signals:
            return self._generate_condition(signals[0])
        return "Always"
    
    def _generate_cluster_action(self, signals: List[Signal]) -> str:
        """Generate an action from a cluster of signals."""
        if not signals:
            return ""
        
        # Combine signal contents
        contents = [s.content for s in signals]
        
        # Find common themes
        if len(contents) == 1:
            return self._generate_action(signals[0])
        
        # For multiple signals, create a combined action
        signal_type = signals[0].signal_type
        if signal_type == SignalType.PREFERENCE:
            return f"Prefer: {', '.join(contents[:3])}"
        elif signal_type == SignalType.AVERSION:
            return f"Avoid: {', '.join(contents[:3])}"
        else:
            return f"Follow: {contents[0]} and related patterns"
    
    def _update_profile(self, signals: List[Signal]) -> List[str]:
        """Update user profile based on signals."""
        updates = []
        profile = self.kernel.profile
        
        for signal in signals:
            if signal.signal_type == SignalType.EXPERTISE:
                # Extract domain from content
                content = signal.content
                if "Expert:" in content:
                    domain = content.replace("Expert:", "").strip()
                    profile.update_expertise(domain, 0.8)
                    updates.append(f"expertise:{domain}")
                elif "Domain expertise:" in content:
                    domain = content.replace("Domain expertise:", "").strip()
                    profile.update_expertise(domain, 0.6)
                    updates.append(f"domain:{domain}")
            
            elif signal.signal_type == SignalType.PREFERENCE:
                # Check for language/tool preferences
                content = signal.content.lower()
                languages = ['python', 'javascript', 'typescript', 'rust', 'go', 'java']
                tools = ['react', 'vue', 'angular', 'fastapi', 'django', 'flask']
                
                for lang in languages:
                    if lang in content:
                        profile.add_preference("language", lang, is_positive=True)
                        updates.append(f"+language:{lang}")
                
                for tool in tools:
                    if tool in content:
                        profile.add_preference("tool", tool, is_positive=True)
                        updates.append(f"+tool:{tool}")
            
            elif signal.signal_type == SignalType.AVERSION:
                content = signal.content.lower()
                # Extract what to avoid
                avoid_match = content.replace("avoid:", "").strip()
                profile.add_preference("tool", avoid_match, is_positive=False)
                updates.append(f"-tech:{avoid_match}")
            
            elif signal.signal_type == SignalType.GOAL:
                goal = signal.content[:100]
                if goal not in profile.active_goals:
                    profile.active_goals.append(goal)
                    if len(profile.active_goals) > 5:
                        profile.active_goals = profile.active_goals[-5:]
                    updates.append(f"goal:{goal[:30]}")
        
        return updates
    
    def _update_style(self, signals: List[Signal]) -> List[str]:
        """Update style vector based on signals."""
        updates = []
        style = self.kernel.style_vector
        
        style_signals = [s for s in signals if s.signal_type == SignalType.STYLE]
        
        for signal in style_signals:
            content = signal.content.replace("style:", "")
            
            # Map styles to vector dimensions
            style_map = {
                "formal": ("formality", 0.8),
                "casual": ("formality", 0.2),
                "technical": ("technicality", 0.8),
                "simple": ("technicality", 0.2),
                "concise": ("verbosity", 0.2),
                "concise_questions": ("verbosity", 0.2),
                "detailed": ("verbosity", 0.8),
                "detailed_context": ("verbosity", 0.8),
                "direct": ("directness", 0.8),
                "diplomatic": ("directness", 0.2),
                "creative": ("creativity", 0.8),
                "conventional": ("creativity", 0.2),
                "fast": ("pace", 0.8),
                "thorough": ("pace", 0.2),
            }
            
            if content in style_map:
                dimension, value = style_map[content]
                style.update(dimension, value, strength=signal.confidence)
                updates.append(f"{dimension}→{value:.1f}")
        
        return updates
    
    def _create_or_update_node(self, signal: Signal) -> bool:
        """Create or update a knowledge node from an entity signal."""
        if signal.signal_type != SignalType.ENTITY:
            return False
        
        entity_name = signal.content
        entity_type = signal.metadata.get("type", "concept")
        
        # Check if node exists
        existing = self.kernel.find_node_by_name(entity_name)
        
        if existing:
            existing.reference()
            return False  # Updated existing
        else:
            # Create new node
            node = KernelNode(
                node_id=str(uuid.uuid4()),
                node_type=entity_type,
                name=entity_name,
                context=f"User mentioned {entity_name}",
            )
            self.kernel.add_node(node)
            
            # Link to active project if any
            if self.kernel.active_project:
                project_node = self.kernel.find_node_by_name(self.kernel.active_project)
                if project_node:
                    self.kernel.link_nodes(node.node_id, project_node.node_id)
            
            return True  # Created new
    
    def process_correction(
        self, 
        original_response: str, 
        correction: str
    ) -> EvolutionReport:
        """
        Process an explicit user correction.
        
        This is a high-priority learning event. When a user explicitly
        corrects the AI, we learn immediately and with high confidence.
        """
        report = EvolutionReport()
        
        # Create a high-confidence correction signal
        content_hash = self.embedding_engine.semantic_hash(
            f"{original_response}|{correction}"
        )
        
        correction_signal = Signal(
            signal_type=SignalType.CORRECTION,
            content=f"Correct: {correction}. Not: {original_response[:50]}",
            confidence=0.95,  # Very high confidence for explicit corrections
            source_hash=content_hash,
            metadata={
                "original": original_response[:100],
                "corrected": correction[:100],
            }
        )
        
        # Process the correction immediately
        return self.evolve([correction_signal])
    
    def force_rule(
        self,
        condition: str,
        action: str,
        category: RuleCategory = RuleCategory.BEHAVIORAL_PATTERN,
        weight: float = 0.9
    ) -> str:
        """
        Force-add a rule without going through signal pipeline.
        
        Use this for explicit user instructions like "Always use TypeScript".
        """
        embedding = self.embedding_engine.embed(f"{condition} {action}")
        
        rule = Rule(
            rule_id=str(uuid.uuid4()),
            category=category,
            condition=condition,
            action=action,
            weight=weight,
            embedding=embedding,
            source_count=1,
        )
        
        return self.kernel.add_rule(rule)


# =============================================================================
# IBLM v3 - SCOPED COMPILER WITH HYPOTHESIS ENGINE
# =============================================================================

@dataclass
class ScopedEvolutionReport:
    """Report of what changed during an evolve_scoped() call."""
    hypotheses_created: int = 0
    hypotheses_validated: int = 0
    hypotheses_rejected: int = 0
    hypotheses_expired: int = 0
    rules_promoted: int = 0
    rules_updated: int = 0
    rules_contradicted: int = 0
    context_nodes_created: int = 0
    context_nodes_updated: int = 0
    signals_processed: int = 0
    interactions_archived: int = 0
    
    def __str__(self) -> str:
        parts = []
        if self.hypotheses_created:
            parts.append(f"+{self.hypotheses_created} hypotheses")
        if self.rules_promoted:
            parts.append(f"↑{self.rules_promoted} promoted")
        if self.hypotheses_rejected:
            parts.append(f"✗{self.hypotheses_rejected} rejected")
        if self.context_nodes_created:
            parts.append(f"+{self.context_nodes_created} contexts")
        return ", ".join(parts) if parts else "no changes"
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "hypotheses_created": self.hypotheses_created,
            "hypotheses_validated": self.hypotheses_validated,
            "hypotheses_rejected": self.hypotheses_rejected,
            "hypotheses_expired": self.hypotheses_expired,
            "rules_promoted": self.rules_promoted,
            "rules_updated": self.rules_updated,
            "rules_contradicted": self.rules_contradicted,
            "context_nodes_created": self.context_nodes_created,
            "context_nodes_updated": self.context_nodes_updated,
            "signals_processed": self.signals_processed,
            "interactions_archived": self.interactions_archived,
        }


class ScopedCompiler:
    """
    v3 SCOPED COMPILER WITH HYPOTHESIS ENGINE
    
    BREAKTHROUGH: This compiler implements:
    1. SCOPED RULES - Rules attached to context nodes (no context collapse)
    2. HYPOTHESIS ENGINE - Signals create hypotheses, not rules directly
    3. COLD STORAGE - Logs archived, not deleted
    
    The evolve_scoped() algorithm:
    
    ┌─────────────────────────────────────────────────────────────┐
    │              evolve_scoped() ALGORITHM                       │
    ├─────────────────────────────────────────────────────────────┤
    │  1. SCOPE DETECTION                                          │
    │     - Extract context from signal (language, project, etc.)  │
    │     - Find or create ContextNode                             │
    │                                                              │
    │  2. HYPOTHESIS CREATION (not Rule!)                          │
    │     - New signal → Hypothesis (confidence: 0.1)              │
    │     - Set expiration                                         │
    │                                                              │
    │  3. HYPOTHESIS VALIDATION                                    │
    │     - Check pending hypotheses against new interactions      │
    │     - User adheres → validations++                           │
    │     - User contradicts → rejections++                        │
    │                                                              │
    │  4. PROMOTION/DEMOTION                                       │
    │     - If validations >= 3 → Promote to ScopedRule            │
    │     - If rejections >= 2 → Delete hypothesis                 │
    │     - If expired → Archive and delete                        │
    │                                                              │
    │  5. COLD STORAGE                                             │
    │     - Archive logs to disk, clear from RAM                   │
    └─────────────────────────────────────────────────────────────┘
    """
    
    # Context detection patterns
    LANGUAGE_KEYWORDS = {
        "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
        "java": "Java", "rust": "Rust", "go": "Go", "golang": "Go",
        "ruby": "Ruby", "php": "PHP", "swift": "Swift", "kotlin": "Kotlin",
        "c++": "C++", "cpp": "C++", "c#": "C#", "csharp": "C#",
    }
    
    FRAMEWORK_KEYWORDS = {
        "fastapi": "FastAPI", "django": "Django", "flask": "Flask",
        "react": "React", "vue": "Vue", "angular": "Angular",
        "express": "Express", "nextjs": "Next.js", "next.js": "Next.js",
        "spring": "Spring", "rails": "Rails",
    }
    
    DOMAIN_KEYWORDS = {
        "backend": "Backend", "frontend": "Frontend", "fullstack": "Fullstack",
        "api": "API", "database": "Database", "ml": "Machine Learning",
        "devops": "DevOps", "mobile": "Mobile", "web": "Web",
    }
    
    def __init__(self, kernel: "ScopedKernel"):
        """
        Initialize the scoped compiler.
        
        Args:
            kernel: The ScopedKernel to compile into
        """
        self.kernel = kernel
        self.embedding_engine = kernel.embedding_engine
        self.semantic_matcher = kernel.semantic_matcher
        
        # Signal type to relation mapping
        self._relation_map = {
            SignalType.PREFERENCE: RelationType.PREFERS,
            SignalType.AVERSION: RelationType.AVOIDS,
            SignalType.EXPERTISE: RelationType.EXPERT_IN,
            SignalType.CORRECTION: RelationType.PREFERS,
            SignalType.WORKFLOW: RelationType.USES,
        }
    
    def evolve_scoped(self, signals: List[Signal]) -> ScopedEvolutionReport:
        """
        The v3 scoped evolution algorithm.
        
        Key differences from v2 evolve():
        1. Creates Hypotheses instead of Rules
        2. Validates pending hypotheses
        3. Uses scoped context nodes
        4. Archives instead of deleting
        
        Args:
            signals: New signals to process
            
        Returns:
            ScopedEvolutionReport with statistics
        """
        report = ScopedEvolutionReport()
        
        if not signals:
            return report
        
        report.signals_processed = len(signals)
        
        # Step 1: Process each signal
        for signal in signals:
            # Detect scope from signal content
            scope_path, target_node_id = self._detect_scope(signal)
            
            # Ensure context node exists
            if target_node_id and target_node_id not in self.kernel.context_nodes:
                self._create_context_node(target_node_id, scope_path)
                report.context_nodes_created += 1
            
            # Step 2: Check for hypothesis validation/contradiction
            matching_hypotheses = self._find_matching_hypotheses(signal)
            
            for hypothesis in matching_hypotheses:
                if self._signal_validates_hypothesis(signal, hypothesis):
                    if hypothesis.validate():
                        # Promote to rule!
                        self._promote_hypothesis(hypothesis)
                        report.rules_promoted += 1
                    else:
                        report.hypotheses_validated += 1
                elif self._signal_contradicts_hypothesis(signal, hypothesis):
                    if hypothesis.reject():
                        self._archive_and_delete_hypothesis(hypothesis, "rejected")
                        report.hypotheses_rejected += 1
            
            # Step 3: Check for existing rule contradiction
            if signal.signal_type == SignalType.CORRECTION:
                contradicted = self._contradict_scoped_rules(signal, scope_path)
                report.rules_contradicted += contradicted
            
            # Step 4: Create new hypothesis from signal
            hypothesis = self._create_hypothesis(signal, scope_path, target_node_id)
            if hypothesis:
                self.kernel.hypotheses[hypothesis.hypothesis_id] = hypothesis
                report.hypotheses_created += 1
        
        # Step 5: Check for expired hypotheses
        expired = self._check_expired_hypotheses()
        report.hypotheses_expired = expired
        
        # Step 6: Record interaction for all pending hypotheses
        for h in self.kernel.hypotheses.values():
            h.record_interaction()
        
        return report
    
    def _detect_scope(self, signal: Signal) -> Tuple[List[str], Optional[str]]:
        """
        Detect the context scope from a signal.
        
        Returns:
            Tuple of (scope_path, target_node_id)
        """
        content = signal.content.lower()
        scope_path = []
        target_node_id = None
        
        # Check for language
        for keyword, name in self.LANGUAGE_KEYWORDS.items():
            if keyword in content:
                scope_path.append(name)
                target_node_id = f"lang_{name.lower()}"
                break
        
        # Check for framework
        for keyword, name in self.FRAMEWORK_KEYWORDS.items():
            if keyword in content:
                scope_path.append(name)
                target_node_id = f"fw_{name.lower().replace('.', '')}"
                break
        
        # Check for domain
        for keyword, name in self.DOMAIN_KEYWORDS.items():
            if keyword in content:
                scope_path.append(name)
                if not target_node_id:
                    target_node_id = f"domain_{name.lower()}"
                break
        
        # Check metadata for project context
        if "project" in signal.metadata:
            project = signal.metadata["project"]
            scope_path.append(project)
            target_node_id = f"project_{project.lower().replace(' ', '_')}"
        
        # Default to global if no scope detected
        if not target_node_id:
            target_node_id = "global"
            scope_path = ["Global"]
        
        return scope_path, target_node_id
    
    def _create_context_node(self, node_id: str, scope_path: List[str]) -> None:
        """Create a new context node."""
        try:
            from .models import ContextNode, ContextType
        except ImportError:
            from models import ContextNode, ContextType
        
        # Determine type from node_id prefix
        if node_id.startswith("lang_"):
            ctx_type = ContextType.LANGUAGE
            name = scope_path[-1] if scope_path else node_id
        elif node_id.startswith("fw_"):
            ctx_type = ContextType.FRAMEWORK
            name = scope_path[-1] if scope_path else node_id
        elif node_id.startswith("domain_"):
            ctx_type = ContextType.DOMAIN
            name = scope_path[-1] if scope_path else node_id
        elif node_id.startswith("project_"):
            ctx_type = ContextType.PROJECT
            name = scope_path[-1] if scope_path else node_id
        else:
            ctx_type = ContextType.TECHNOLOGY
            name = node_id
        
        node = ContextNode(
            node_id=node_id,
            context_type=ctx_type,
            name=name,
            description=f"Context: {' > '.join(scope_path)}",
        )
        
        # Generate embedding
        node.embedding = self.embedding_engine.embed(name)
        
        self.kernel.context_nodes[node_id] = node
    
    def _find_matching_hypotheses(self, signal: Signal) -> List["Hypothesis"]:
        """Find hypotheses that match the signal's scope."""
        try:
            from .models import Hypothesis, HypothesisState
        except ImportError:
            from models import Hypothesis, HypothesisState
        
        matches = []
        signal_embedding = self.embedding_engine.embed(signal.content)
        
        for hypothesis in self.kernel.hypotheses.values():
            if hypothesis.state not in [HypothesisState.PENDING, HypothesisState.VALIDATING]:
                continue
            
            # Check semantic similarity
            if hypothesis.embedding:
                similarity = EmbeddingEngine.cosine_similarity(
                    signal_embedding, hypothesis.embedding
                )
                if similarity > 0.6:
                    matches.append(hypothesis)
        
        return matches
    
    def _signal_validates_hypothesis(self, signal: Signal, hypothesis: "Hypothesis") -> bool:
        """Check if signal validates hypothesis (user adhered)."""
        # Validation: user continues to demonstrate the hypothesized behavior
        if signal.signal_type in [SignalType.PREFERENCE, SignalType.WORKFLOW]:
            similarity = self._semantic_similarity(signal.content, hypothesis.proposed_content)
            return similarity > 0.7
        return False
    
    def _signal_contradicts_hypothesis(self, signal: Signal, hypothesis: "Hypothesis") -> bool:
        """Check if signal contradicts hypothesis."""
        if signal.signal_type == SignalType.CORRECTION:
            similarity = self._semantic_similarity(signal.content, hypothesis.proposed_content)
            # Check for negation patterns
            negations = ["don't", "not", "never", "stop", "instead"]
            has_negation = any(neg in signal.content.lower() for neg in negations)
            return similarity > 0.5 and has_negation
        return False
    
    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts."""
        emb1 = self.embedding_engine.embed(text1)
        emb2 = self.embedding_engine.embed(text2)
        return EmbeddingEngine.cosine_similarity(emb1, emb2)
    
    def _promote_hypothesis(self, hypothesis: "Hypothesis") -> None:
        """Promote a validated hypothesis to a ScopedRule."""
        rule = hypothesis.to_scoped_rule()
        
        # Generate embedding
        rule.embedding = self.embedding_engine.embed(rule.content)
        
        # Add to kernel
        self.kernel.scoped_rules[rule.rule_id] = rule
        
        # Archive hypothesis
        self._archive_and_delete_hypothesis(hypothesis, "promoted")
    
    def _archive_and_delete_hypothesis(self, hypothesis: "Hypothesis", reason: str) -> None:
        """Archive hypothesis to cold storage and remove from RAM."""
        if self.kernel.cold_storage:
            self.kernel.cold_storage.archive_hypothesis(hypothesis, reason)
        
        if hypothesis.hypothesis_id in self.kernel.hypotheses:
            del self.kernel.hypotheses[hypothesis.hypothesis_id]
    
    def _contradict_scoped_rules(self, signal: Signal, scope_path: List[str]) -> int:
        """Contradict scoped rules that match the signal scope."""
        contradicted = 0
        signal_embedding = self.embedding_engine.embed(signal.content)
        
        for rule in self.kernel.scoped_rules.values():
            if not rule.matches_context(scope_path):
                continue
            
            if rule.embedding:
                similarity = EmbeddingEngine.cosine_similarity(
                    signal_embedding, rule.embedding
                )
                if similarity > 0.6:
                    rule.contradict()
                    contradicted += 1
        
        return contradicted
    
    def _create_hypothesis(
        self, 
        signal: Signal, 
        scope_path: List[str],
        target_node_id: str
    ) -> Optional["Hypothesis"]:
        """Create a new hypothesis from a signal."""
        try:
            from .models import Hypothesis, RelationType, HypothesisState
        except ImportError:
            from models import Hypothesis, RelationType, HypothesisState
        
        # Skip low-confidence signals
        if signal.confidence < 0.3:
            return None
        
        # Get relation type
        relation = self._relation_map.get(signal.signal_type, RelationType.USES)
        
        # Create hypothesis
        hypothesis = Hypothesis(
            hypothesis_id=f"hyp_{uuid.uuid4().hex[:8]}",
            proposed_content=signal.content,
            proposed_scope_path=scope_path,
            proposed_relation=relation,
            proposed_target_node=target_node_id,
            confidence=0.1,
            source_signal_type=signal.signal_type.name,
            source_hash=signal.source_hash,
        )
        
        # Set expiration (24 hours from now)
        from datetime import timedelta
        hypothesis.expires_at = datetime.now() + timedelta(hours=24)
        
        # Generate embedding
        hypothesis.embedding = self.embedding_engine.embed(signal.content)
        
        return hypothesis
    
    def _check_expired_hypotheses(self) -> int:
        """Check and archive expired hypotheses."""
        expired_count = 0
        expired_ids = []
        
        for h_id, hypothesis in self.kernel.hypotheses.items():
            if hypothesis.check_expiry():
                expired_ids.append(h_id)
        
        for h_id in expired_ids:
            hypothesis = self.kernel.hypotheses[h_id]
            self._archive_and_delete_hypothesis(hypothesis, "expired")
            expired_count += 1
        
        return expired_count
    
    def force_scoped_rule(
        self,
        content: str,
        scope_path: List[str],
        target_node_id: str,
        relation: "RelationType" = None,
        weight: float = 0.9
    ) -> str:
        """
        Force-add a scoped rule without going through hypothesis pipeline.
        
        Use for explicit user instructions like "In Python, always use async".
        """
        try:
            from .models import ScopedRule, RelationType
        except ImportError:
            from models import ScopedRule, RelationType
        
        if relation is None:
            relation = RelationType.PREFERS
        
        rule = ScopedRule(
            rule_id=f"rule_{uuid.uuid4().hex[:8]}",
            source_node="user",
            target_node=target_node_id,
            relation=relation,
            content=content,
            weight=weight,
            confidence=0.9,
            scope_path=scope_path,
            embedding=self.embedding_engine.embed(content),
            source_count=1,
        )
        
        self.kernel.scoped_rules[rule.rule_id] = rule
        return rule.rule_id
    
    # =========================================================================
    # v3.0 SCIENTIFIC MEMORY: SIMPLIFIED EVOLUTION
    # =========================================================================
    
    def scientific_evolve(self, signals: List[Signal]) -> Dict[str, int]:
        """
        v3.0 SCIENTIFIC MEMORY: The Simple, Elegant Evolution Algorithm.
        
        This replaces the complex hypothesis pipeline with a unified approach:
        1. Every signal creates or updates a ScopedRule (starting as HYPOTHESIS)
        2. Repeated validation boosts confidence (HYPOTHESIS → ESTABLISHED)
        3. Contradictions reduce confidence (can lead to DEPRECATED)
        4. Different scopes NEVER conflict
        
        Algorithm:
            for signal in signals:
                scope = detect_scope(signal)
                existing = find_rule_in_scope(signal.content, scope)
                
                if existing:
                    existing.validate()  # Boost confidence
                else:
                    create new ScopedRule(confidence=0.2, state=HYPOTHESIS)
        
        Returns:
            Dict with statistics
        """
        try:
            from .models import ScopedRule, RuleState, CollaborationRequest, SignalType
        except ImportError:
            from models import ScopedRule, RuleState, CollaborationRequest, SignalType
        
        stats = {
            "signals_processed": 0,
            "rules_created": 0,
            "rules_validated": 0,
            "rules_rejected": 0,
            "rules_established": 0,
            "rules_deprecated": 0,
            "collaboration_requests": [],
        }
        
        if not signals:
            return stats
        
        stats["signals_processed"] = len(signals)
        
        for signal in signals:
            # Step A: Detect Scope
            scope_path, target_node_id = self._detect_scope(signal)
            
            # Step B: Find existing rule IN THIS SCOPE
            existing_rule = self._find_rule_in_scope(signal.content, scope_path)
            
            if existing_rule:
                # Rule exists (matches semantically)
                
                # SOCRATIC CHECK:
                # If rule is ESTABLISHED and new signal differs significantly in content
                # and isn't an explicit correction -> Conflict!
                is_different_content = existing_rule.content.lower().strip() != signal.content.lower().strip()
                
                if (existing_rule.state == RuleState.ESTABLISHED and 
                    is_different_content and 
                    signal.signal_type != SignalType.CORRECTION and
                    signal.signal_type != SignalType.AVERSION):
                    
                    # Create Request
                    req = CollaborationRequest(
                        request_id=f"req_{uuid.uuid4().hex[:8]}",
                        trigger_signal=signal,
                        conflicting_rule=existing_rule,
                        reason=f"New signal '{signal.content}' differs from established rule '{existing_rule.content}'",
                        proposed_options=[
                            f"Replace with: {signal.content}",
                            f"Keep existing: {existing_rule.content}",
                            "Create context exception"
                        ]
                    )
                    stats["collaboration_requests"].append(req)
                    continue

                # VALIDATION: User repeated behavior -> Boost Confidence
                if signal.signal_type == SignalType.CORRECTION:
                    # User contradicted
                    existing_rule.reject()
                    stats["rules_rejected"] += 1
                    if existing_rule.state == RuleState.DEPRECATED:
                        stats["rules_deprecated"] += 1
                else:
                    # User confirmed
                    old_state = existing_rule.state
                    existing_rule.validate()
                    stats["rules_validated"] += 1
                    if old_state != RuleState.ESTABLISHED and existing_rule.state == RuleState.ESTABLISHED:
                        stats["rules_established"] += 1
            else:
                # HYPOTHESIS: New behavior observed -> Create Weak Rule
                relation = self._relation_map.get(signal.signal_type, RelationType.PREFERS)
                
                new_rule = ScopedRule(
                    rule_id=f"rule_{uuid.uuid4().hex[:8]}",
                    content=signal.content,
                    scope_path=scope_path,
                    target_node=target_node_id or "global",
                    relation=relation,
                    confidence=0.2,  # Low confidence start (HYPOTHESIS)
                    # state will be HYPOTHESIS by default
                )
                
                # Generate embedding
                new_rule.embedding = self.embedding_engine.embed(signal.content)
                
                self.kernel.scoped_rules[new_rule.rule_id] = new_rule
                stats["rules_created"] += 1
        
        return stats
    
    def _find_rule_in_scope(self, content: str, scope_path: List[str]) -> Optional["ScopedRule"]:
        """
        Find an existing rule with similar content IN THE SAME SCOPE.
        
        This is key to the Scientific Memory: rules are scoped, so
        "Prefers verbose" in Writing and "Prefers concise" in Coding
        are stored separately and never conflict.
        """
        content_embedding = self.embedding_engine.embed(content)
        
        for rule in self.kernel.scoped_rules.values():
            # Must match scope
            if rule.scope_path != scope_path:
                continue
            
            # Check semantic similarity
            if rule.embedding:
                similarity = EmbeddingEngine.cosine_similarity(
                    content_embedding, rule.embedding
                )
                if similarity > 0.75:  # High similarity threshold
                    return rule
        
        return None
    
    # =========================================================================
    # v4.0 SHADOW MODE & ADAPTIVE SOCRATIC
    # =========================================================================
    
    SOCRATIC_THRESHOLD = 8.0  # Only ask user if severity > this
    
    def shadow_predict(self, query: str, scope_path: List[str]) -> Optional[Dict[str, Any]]:
        """
        v4.0 SHADOW MODE: Predict what the user will do WITHOUT injecting.
        
        Returns a prediction dict if a SHADOW rule matches, else None.
        Used for silent validation of rules before graduation.
        """
        for rule in self.kernel.scoped_rules.values():
            if rule.state != RuleState.SHADOW:
                continue
            
            # Scope matching (allow subset)
            if scope_path and rule.scope_path:
                if not any(s.lower() in [p.lower() for p in scope_path] for s in rule.scope_path):
                    continue
            
            # Check if this rule's content matches the query context
            query_embedding = self.embedding_engine.embed(query)
            if rule.embedding:
                similarity = EmbeddingEngine.cosine_similarity(query_embedding, rule.embedding)
                if similarity > 0.3:  # Lower threshold for testing
                    return {
                        "rule_id": rule.rule_id,
                        "predicted_content": rule.content,
                        "confidence": rule.confidence,
                    }
        return None
    
    def shadow_validate(self, rule_id: str, user_action: str, matched: bool) -> Dict[str, Any]:
        """
        v4.0 SHADOW MODE: Validate shadow prediction against user's actual action.
        
        Args:
            rule_id: The shadow rule that made a prediction
            user_action: What the user actually did
            matched: Whether the prediction matched the action
        
        Returns:
            Stats about the validation
        """
        rule = self.kernel.scoped_rules.get(rule_id)
        if not rule:
            return {"error": "Rule not found"}
        
        if matched:
            # Silent promotion
            rule.validate(boost=0.2)
            return {"action": "promoted", "new_confidence": rule.confidence, "new_state": rule.state.value}
        else:
            # Silent demotion
            rule.reject(penalty=0.1)
            return {"action": "demoted", "new_confidence": rule.confidence, "new_state": rule.state.value}
    
    def adaptive_socratic(self, signal: Signal, conflicting_rule: "ScopedRule") -> Optional["CollaborationRequest"]:
        """
        v4.0 ADAPTIVE SOCRATIC: Only interrupt user for high-severity conflicts.
        
        Severity = goal_priority * rule_confidence
        If severity > THRESHOLD -> Ask user
        Else -> Silently self-correct
        """
        # Find relevant goal for this scope
        scope_path, _ = self._detect_scope(signal)
        goals = self.kernel.get_active_goals(scope_path) if hasattr(self.kernel, 'get_active_goals') else []
        
        # Calculate severity
        max_goal_priority = max([g.decay_priority() for g in goals], default=5)
        severity = max_goal_priority * conflicting_rule.confidence
        
        if severity > self.SOCRATIC_THRESHOLD:
            # High severity -> Ask user
            try:
                from .models import CollaborationRequest
            except ImportError:
                from models import CollaborationRequest
            
            return CollaborationRequest(
                request_id=f"req_{uuid.uuid4().hex[:8]}",
                trigger_signal=signal,
                conflicting_rule=conflicting_rule,
                reason=f"High-priority conflict (severity: {severity:.1f})",
                proposed_options=[
                    f"Replace with: {signal.content}",
                    f"Keep existing: {conflicting_rule.content}",
                    "Create exception for this context"
                ]
            )
        else:
            # Low severity -> Silently update hypothesis
            conflicting_rule.reject(penalty=0.05)  # Gentle demotion
            return None


# Import RelationType for ScopedCompiler
try:
    from .models import RelationType, RuleState
except ImportError:
    from models import RelationType, RuleState


