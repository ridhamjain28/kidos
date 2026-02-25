"""
IBLM Core - Data Models
=======================

Core data structures for the Individual Behavior Learning Machine.
These models form the foundation of the "Living Kernel" architecture.

BREAKTHROUGH CONCEPT:
Instead of storing raw text (traditional RAG), we store:
- Behavioral RULES (compiled from multiple interactions)
- Style VECTORS (multi-dimensional user preferences)
- Knowledge NODES (graph structure with decay/weight)

This achieves O(log n) context growth instead of O(n).
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import hashlib
import json


class SignalType(Enum):
    """
    Types of implicit signals extracted from user interactions.
    
    These are the "atoms" of learning - each interaction may emit
    multiple signals that the LogicCompiler converts to rules.
    """
    CORRECTION = auto()      # User corrects AI behavior ("No, do X instead")
    PREFERENCE = auto()      # User expresses preference ("I prefer X")
    STYLE = auto()           # User demonstrates communication style
    ENTITY = auto()          # User introduces new entity (project, concept)
    EXPERTISE = auto()       # User demonstrates domain expertise
    AVERSION = auto()        # User shows dislike ("Don't use X")
    CONTEXT = auto()         # User provides background context
    PERSONALITY = auto()     # User reveals personality trait
    GOAL = auto()            # User states objective or goal
    WORKFLOW = auto()        # User shows preferred workflow pattern


class RuleCategory(Enum):
    """Categories for compiled behavioral rules."""
    COMMUNICATION_STYLE = auto()   # How user prefers to communicate
    TECHNICAL_PREFERENCE = auto()  # Technical choices and tools
    DOMAIN_EXPERTISE = auto()      # Areas of user expertise
    BEHAVIORAL_PATTERN = auto()    # Recurring behaviors
    PROJECT_CONTEXT = auto()       # Project-specific rules
    PERSONALITY_TRAIT = auto()     # Core personality aspects
    WORKFLOW_PATTERN = auto()      # How user works


@dataclass
class Signal:
    """
    An implicit signal extracted from a user-AI interaction.
    
    Signals are temporary - they exist only until the LogicCompiler
    processes them into Rules. This is key to our garbage collection.
    
    Attributes:
        signal_type: The category of signal detected
        content: The actual information extracted
        confidence: How confident we are in this extraction (0.0-1.0)
        source_hash: Hash of source interaction (for deduplication)
        timestamp: When signal was extracted
        metadata: Additional context about the signal
    """
    signal_type: SignalType
    content: str
    confidence: float
    source_hash: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_type": self.signal_type.name,
            "content": self.content,
            "confidence": self.confidence,
            "source_hash": self.source_hash,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Signal":
        return cls(
            signal_type=SignalType[data["signal_type"]],
            content=data["content"],
            confidence=data["confidence"],
            source_hash=data["source_hash"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Rule:
    """
    A compiled behavioral rule - the core unit of the User Kernel.
    
    BREAKTHROUGH: Rules are COMPILED from multiple raw interactions.
    Once a rule reaches sufficient confidence, the source interactions
    are DELETED (garbage collected). This is how we achieve infinite scaling.
    
    Example Rule Chain:
    - Interaction 1: "Use Python" -> Signal(PREFERENCE, "Python")
    - Interaction 2: "No TypeScript" -> Signal(AVERSION, "TypeScript")
    - Interaction 3: "Python is my main language" -> Signal(EXPERTISE, "Python")
    - COMPILED RULE: "User is Python expert, avoid TypeScript" (weight: 0.9)
    - SOURCE INTERACTIONS: DELETED
    
    Attributes:
        rule_id: Unique identifier
        category: The type of rule
        condition: When this rule applies (semantic description)
        action: What behavior this rule dictates
        weight: Importance/confidence (0.0-1.0), decays over time
        embedding: Vector representation for semantic matching
        source_count: How many interactions contributed to this rule
        last_activated: Last time this rule was used
        last_reinforced: Last time this rule was strengthened
        contradictions: Count of times this rule was contradicted
    """
    rule_id: str
    category: RuleCategory
    condition: str
    action: str
    weight: float
    embedding: Optional[List[float]] = None
    source_count: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    last_activated: datetime = field(default_factory=datetime.now)
    last_reinforced: datetime = field(default_factory=datetime.now)
    contradictions: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def reinforce(self, boost: float = 0.1) -> None:
        """Strengthen this rule (called when user behavior confirms it)."""
        self.weight = min(1.0, self.weight + boost)
        self.last_reinforced = datetime.now()
        self.source_count += 1
    
    def contradict(self, penalty: float = 0.3) -> None:
        """Weaken this rule (called when user contradicts it)."""
        self.weight = max(0.0, self.weight - penalty)
        self.contradictions += 1
    
    def decay(self, decay_rate: float = 0.01) -> None:
        """Apply time-based decay to this rule's weight."""
        days_since_use = (datetime.now() - self.last_activated).days
        decay = decay_rate * days_since_use
        self.weight = max(0.0, self.weight - decay)
    
    def activate(self) -> None:
        """Mark this rule as recently used."""
        self.last_activated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "category": self.category.name,
            "condition": self.condition,
            "action": self.action,
            "weight": self.weight,
            "embedding": self.embedding,
            "source_count": self.source_count,
            "created_at": self.created_at.isoformat(),
            "last_activated": self.last_activated.isoformat(),
            "last_reinforced": self.last_reinforced.isoformat(),
            "contradictions": self.contradictions,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rule":
        return cls(
            rule_id=data["rule_id"],
            category=RuleCategory[data["category"]],
            condition=data["condition"],
            action=data["action"],
            weight=data["weight"],
            embedding=data.get("embedding"),
            source_count=data.get("source_count", 1),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activated=datetime.fromisoformat(data["last_activated"]),
            last_reinforced=datetime.fromisoformat(data["last_reinforced"]),
            contradictions=data.get("contradictions", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class KernelNode:
    """
    A node in the User Kernel's knowledge graph.
    
    Nodes represent entities, concepts, and relationships the user has
    introduced. They form a semantic network with weighted edges.
    
    Examples:
    - Node("Project_Alpha", type="project", context="ML pipeline")
    - Node("FastAPI", type="technology", context="preferred framework")
    
    Attributes:
        node_id: Unique identifier
        node_type: Category (project, technology, concept, person, etc.)
        name: Human-readable name
        context: Description/context about this node
        embedding: Vector representation
        weight: Importance/relevance score
        edges: Connections to other nodes (node_id -> edge_weight)
        properties: Additional key-value properties
    """
    node_id: str
    node_type: str
    name: str
    context: str
    embedding: Optional[List[float]] = None
    weight: float = 0.5
    edges: Dict[str, float] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_referenced: datetime = field(default_factory=datetime.now)
    reference_count: int = 1
    
    def add_edge(self, target_id: str, weight: float = 0.5) -> None:
        """Add or strengthen connection to another node."""
        if target_id in self.edges:
            self.edges[target_id] = min(1.0, self.edges[target_id] + 0.1)
        else:
            self.edges[target_id] = weight
    
    def reference(self) -> None:
        """Mark this node as recently referenced."""
        self.last_referenced = datetime.now()
        self.reference_count += 1
        self.weight = min(1.0, self.weight + 0.05)
    
    def decay(self, decay_rate: float = 0.005) -> None:
        """Apply time-based decay."""
        days_since_ref = (datetime.now() - self.last_referenced).days
        decay = decay_rate * days_since_ref
        self.weight = max(0.1, self.weight - decay)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "name": self.name,
            "context": self.context,
            "embedding": self.embedding,
            "weight": self.weight,
            "edges": self.edges,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "last_referenced": self.last_referenced.isoformat(),
            "reference_count": self.reference_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KernelNode":
        return cls(
            node_id=data["node_id"],
            node_type=data["node_type"],
            name=data["name"],
            context=data["context"],
            embedding=data.get("embedding"),
            weight=data.get("weight", 0.5),
            edges=data.get("edges", {}),
            properties=data.get("properties", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_referenced=datetime.fromisoformat(data["last_referenced"]),
            reference_count=data.get("reference_count", 1),
        )


@dataclass
class StyleVector:
    """
    Multi-dimensional representation of user's communication style.
    
    BREAKTHROUGH: Instead of storing "user prefers concise responses" as text,
    we encode it as a vector that can be efficiently matched and updated.
    
    Dimensions:
    - formality: 0.0 (casual) to 1.0 (formal)
    - verbosity: 0.0 (concise) to 1.0 (detailed)
    - technicality: 0.0 (simple) to 1.0 (technical)
    - directness: 0.0 (diplomatic) to 1.0 (blunt)
    - creativity: 0.0 (conventional) to 1.0 (creative)
    - pace: 0.0 (thorough) to 1.0 (fast-paced)
    """
    formality: float = 0.5
    verbosity: float = 0.5
    technicality: float = 0.5
    directness: float = 0.5
    creativity: float = 0.5
    pace: float = 0.5
    
    # Learning rate for updates
    learning_rate: float = 0.1
    
    # Confidence in each dimension (increases with more data)
    confidence: Dict[str, float] = field(default_factory=lambda: {
        "formality": 0.1,
        "verbosity": 0.1,
        "technicality": 0.1,
        "directness": 0.1,
        "creativity": 0.1,
        "pace": 0.1,
    })
    
    def update(self, dimension: str, target_value: float, strength: float = 1.0) -> None:
        """
        Update a style dimension towards a target value.
        
        Uses exponential moving average with adaptive learning rate
        based on confidence level.
        """
        if hasattr(self, dimension):
            current = getattr(self, dimension)
            # Adaptive learning rate: learn faster when less confident
            effective_lr = self.learning_rate * (1.0 - self.confidence.get(dimension, 0.1))
            new_value = current + effective_lr * strength * (target_value - current)
            setattr(self, dimension, max(0.0, min(1.0, new_value)))
            
            # Increase confidence
            self.confidence[dimension] = min(0.95, self.confidence[dimension] + 0.05)
    
    def to_vector(self) -> List[float]:
        """Export as a simple vector for matching."""
        return [
            self.formality,
            self.verbosity,
            self.technicality,
            self.directness,
            self.creativity,
            self.pace,
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "formality": self.formality,
            "verbosity": self.verbosity,
            "technicality": self.technicality,
            "directness": self.directness,
            "creativity": self.creativity,
            "pace": self.pace,
            "learning_rate": self.learning_rate,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StyleVector":
        sv = cls(
            formality=data.get("formality", 0.5),
            verbosity=data.get("verbosity", 0.5),
            technicality=data.get("technicality", 0.5),
            directness=data.get("directness", 0.5),
            creativity=data.get("creativity", 0.5),
            pace=data.get("pace", 0.5),
            learning_rate=data.get("learning_rate", 0.1),
        )
        sv.confidence = data.get("confidence", sv.confidence)
        return sv
    
    def describe(self) -> str:
        """Generate natural language description of the style."""
        descriptions = []
        
        if self.confidence["formality"] > 0.3:
            if self.formality < 0.3:
                descriptions.append("casual and friendly")
            elif self.formality > 0.7:
                descriptions.append("formal and professional")
        
        if self.confidence["verbosity"] > 0.3:
            if self.verbosity < 0.3:
                descriptions.append("prefers concise responses")
            elif self.verbosity > 0.7:
                descriptions.append("appreciates detailed explanations")
        
        if self.confidence["technicality"] > 0.3:
            if self.technicality < 0.3:
                descriptions.append("prefers simple explanations")
            elif self.technicality > 0.7:
                descriptions.append("comfortable with technical depth")
        
        if self.confidence["directness"] > 0.3:
            if self.directness < 0.3:
                descriptions.append("appreciates diplomatic phrasing")
            elif self.directness > 0.7:
                descriptions.append("prefers direct, blunt communication")
        
        if self.confidence["pace"] > 0.3:
            if self.pace < 0.3:
                descriptions.append("thorough, step-by-step approach")
            elif self.pace > 0.7:
                descriptions.append("fast-paced, gets to the point")
        
        return "; ".join(descriptions) if descriptions else "style still being learned"


@dataclass
class UserProfile:
    """
    Complete profile of the user - the "Individual" in IBLM.
    
    This is the core of Individual Behavior Learning - we build a complete
    picture of WHO the user is, not just what they've said.
    
    The profile evolves continuously as the user interacts, becoming
    an increasingly accurate "digital twin" of the user's preferences,
    expertise, and working style.
    """
    # Core identity
    expertise_domains: List[str] = field(default_factory=list)
    expertise_levels: Dict[str, float] = field(default_factory=dict)  # domain -> level (0-1)
    
    # Professional context
    role: Optional[str] = None
    industry: Optional[str] = None
    current_projects: List[str] = field(default_factory=list)
    
    # Technical preferences
    preferred_languages: List[str] = field(default_factory=list)
    preferred_tools: List[str] = field(default_factory=list)
    avoided_technologies: List[str] = field(default_factory=list)
    
    # Communication style
    style_vector: StyleVector = field(default_factory=StyleVector)
    
    # Personality traits (inferred from interactions)
    traits: Dict[str, float] = field(default_factory=dict)
    
    # Goals and objectives
    active_goals: List[str] = field(default_factory=list)
    
    # Interaction patterns
    typical_session_length: float = 0.5  # 0=short, 1=long
    question_complexity: float = 0.5     # 0=simple, 1=complex
    iteration_preference: float = 0.5    # 0=one-shot, 1=iterative
    
    # Learning state
    total_interactions: int = 0
    profile_confidence: float = 0.0  # Overall confidence in profile accuracy
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_expertise(self, domain: str, demonstrated_level: float) -> None:
        """Update expertise level for a domain based on demonstrated knowledge."""
        if domain not in self.expertise_domains:
            self.expertise_domains.append(domain)
            self.expertise_levels[domain] = demonstrated_level
        else:
            # Exponential moving average
            current = self.expertise_levels[domain]
            self.expertise_levels[domain] = current * 0.7 + demonstrated_level * 0.3
    
    def add_preference(self, category: str, item: str, is_positive: bool = True) -> None:
        """Add a preference (liked or avoided technology/tool)."""
        if category == "language":
            target = self.preferred_languages if is_positive else self.avoided_technologies
        elif category == "tool":
            target = self.preferred_tools if is_positive else self.avoided_technologies
        else:
            return
        
        if item not in target:
            target.append(item)
            
        # Remove from opposite list if present
        opposite = self.avoided_technologies if is_positive else self.preferred_languages + self.preferred_tools
        if item in opposite:
            opposite.remove(item)
    
    def record_interaction(self) -> None:
        """Record that an interaction occurred."""
        self.total_interactions += 1
        self.last_updated = datetime.now()
        # Increase profile confidence (diminishing returns)
        self.profile_confidence = min(0.95, 1.0 - (1.0 / (1.0 + self.total_interactions * 0.1)))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "expertise_domains": self.expertise_domains,
            "expertise_levels": self.expertise_levels,
            "role": self.role,
            "industry": self.industry,
            "current_projects": self.current_projects,
            "preferred_languages": self.preferred_languages,
            "preferred_tools": self.preferred_tools,
            "avoided_technologies": self.avoided_technologies,
            "style_vector": self.style_vector.to_dict(),
            "traits": self.traits,
            "active_goals": self.active_goals,
            "typical_session_length": self.typical_session_length,
            "question_complexity": self.question_complexity,
            "iteration_preference": self.iteration_preference,
            "total_interactions": self.total_interactions,
            "profile_confidence": self.profile_confidence,
            "last_updated": self.last_updated.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        profile = cls(
            expertise_domains=data.get("expertise_domains", []),
            expertise_levels=data.get("expertise_levels", {}),
            role=data.get("role"),
            industry=data.get("industry"),
            current_projects=data.get("current_projects", []),
            preferred_languages=data.get("preferred_languages", []),
            preferred_tools=data.get("preferred_tools", []),
            avoided_technologies=data.get("avoided_technologies", []),
            traits=data.get("traits", {}),
            active_goals=data.get("active_goals", []),
            typical_session_length=data.get("typical_session_length", 0.5),
            question_complexity=data.get("question_complexity", 0.5),
            iteration_preference=data.get("iteration_preference", 0.5),
            total_interactions=data.get("total_interactions", 0),
            profile_confidence=data.get("profile_confidence", 0.0),
        )
        if "style_vector" in data:
            profile.style_vector = StyleVector.from_dict(data["style_vector"])
        if "last_updated" in data:
            profile.last_updated = datetime.fromisoformat(data["last_updated"])
        return profile
    
    def generate_persona_prompt(self) -> str:
        """
        Generate a natural language description of the user.
        
        This is used by the ContextInjector to give the LLM a "telepathic"
        understanding of who it's talking to.
        """
        parts = []
        
        # Role and industry
        if self.role:
            parts.append(f"The user is a {self.role}")
            if self.industry:
                parts.append(f"in the {self.industry} industry")
        
        # Expertise
        if self.expertise_domains:
            high_expertise = [d for d, l in self.expertise_levels.items() if l > 0.7]
            if high_expertise:
                parts.append(f"Expert in: {', '.join(high_expertise)}")
        
        # Preferences
        if self.preferred_languages:
            parts.append(f"Preferred languages: {', '.join(self.preferred_languages[:3])}")
        
        if self.avoided_technologies:
            parts.append(f"Avoid: {', '.join(self.avoided_technologies[:3])}")
        
        # Style
        style_desc = self.style_vector.describe()
        if style_desc != "style still being learned":
            parts.append(f"Communication style: {style_desc}")
        
        # Goals
        if self.active_goals:
            parts.append(f"Current focus: {self.active_goals[0]}")
        
        return ". ".join(parts) + "." if parts else ""


@dataclass
class InteractionLog:
    """
    Temporary storage for a raw interaction.
    
    CRITICAL: These are DELETED after being compiled into Rules.
    This is the garbage collection mechanism that enables infinite scaling.
    
    We keep a hash of the interaction for deduplication even after deletion.
    """
    log_id: str
    user_input: str
    ai_output: str
    timestamp: datetime = field(default_factory=datetime.now)
    signals_extracted: List[str] = field(default_factory=list)  # Signal IDs
    processed: bool = False
    compilation_target: Optional[str] = None  # Rule ID if compiled
    
    @property
    def content_hash(self) -> str:
        """Generate hash of content for deduplication."""
        content = f"{self.user_input}|{self.ai_output}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "log_id": self.log_id,
            "user_input": self.user_input,
            "ai_output": self.ai_output,
            "timestamp": self.timestamp.isoformat(),
            "signals_extracted": self.signals_extracted,
            "processed": self.processed,
            "compilation_target": self.compilation_target,
            "content_hash": self.content_hash,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InteractionLog":
        return cls(
            log_id=data["log_id"],
            user_input=data["user_input"],
            ai_output=data["ai_output"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            signals_extracted=data.get("signals_extracted", []),
            processed=data.get("processed", False),
            compilation_target=data.get("compilation_target"),
        )


# Hash set for tracking processed interactions (survives garbage collection)
@dataclass
class ProcessedInteractionRegistry:
    """
    Registry of processed interaction hashes.
    
    Even after garbage collection deletes the raw interactions,
    we keep the hashes to prevent reprocessing duplicates.
    """
    hashes: Set[str] = field(default_factory=set)
    max_size: int = 10000  # Limit to prevent unbounded growth
    
    def register(self, content_hash: str) -> None:
        """Register a processed interaction."""
        if len(self.hashes) >= self.max_size:
            # Remove oldest (arbitrary since set is unordered, but prevents unbounded growth)
            self.hashes.pop()
        self.hashes.add(content_hash)
    
    def is_processed(self, content_hash: str) -> bool:
        """Check if an interaction was already processed."""
        return content_hash in self.hashes
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hashes": list(self.hashes),
            "max_size": self.max_size,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessedInteractionRegistry":
        registry = cls(max_size=data.get("max_size", 10000))
        registry.hashes = set(data.get("hashes", []))
        return registry


# =============================================================================
# IBLM v3 - SCOPED PROBABILISTIC KERNEL DATA STRUCTURES
# =============================================================================

class HypothesisState(Enum):
    """State of a hypothesis in the validation pipeline."""
    PENDING = auto()      # Awaiting validation
    VALIDATING = auto()   # Accumulating validations
    PROMOTED = auto()     # Promoted to ScopedRule
    REJECTED = auto()     # Rejected due to contradictions
    EXPIRED = auto()      # Expired without enough validations


class ContextType(Enum):
    """Types of context nodes for scoping."""
    LANGUAGE = auto()     # Programming language (Python, JavaScript, etc.)
    FRAMEWORK = auto()    # Framework (FastAPI, React, etc.)
    DOMAIN = auto()       # Domain (Backend, Frontend, ML, etc.)
    PROJECT = auto()      # Specific project
    TECHNOLOGY = auto()   # General technology
    PARADIGM = auto()     # Programming paradigm (OOP, Functional, etc.)
    ENVIRONMENT = auto()  # Environment (Dev, Prod, Testing)


class RelationType(Enum):
    """Types of relationships between User and Context nodes."""
    PREFERS = auto()      # User prefers this approach
    AVOIDS = auto()       # User avoids this approach
    REQUIRES = auto()     # User requires this
    EXPERT_IN = auto()    # User is expert in this
    LEARNING = auto()     # User is learning this
    USES = auto()         # User uses this


class RuleState(Enum):
    """
    v3.0 SCIENTIFIC MEMORY: Rule lifecycle states.
    
    A rule starts as HYPOTHESIS and progresses through validation:
    HYPOTHESIS → VALIDATING → ESTABLISHED → (optionally DEPRECATED)
    
    Only ESTABLISHED rules are injected into prompts.
    """
    HYPOTHESIS = "hypothesis"      # Newly formed theory (confidence < 0.5)
    SHADOW = "shadow"              # v4.0: Silent testing phase (0.4 <= confidence < 0.6)
    VALIDATING = "validating"      # Being tested (0.6 <= confidence < 0.8)
    ESTABLISHED = "established"    # Proven fact (confidence >= 0.8)
    DEPRECATED = "deprecated"      # Disproven or outdated (confidence < 0.2)


@dataclass
class ContextNode:
    """
    v3 SCOPED CONTEXT NODE
    
    A node representing a context scope for rules.
    Rules are scoped to these nodes, eliminating context collapse.
    
    Example:
        - ContextNode("python", LANGUAGE, "Python Programming")
        - ContextNode("fastapi", FRAMEWORK, "FastAPI Web Framework", parent="python")
        - ContextNode("backend", DOMAIN, "Backend Development")
    
    Hierarchy enables scope inheritance:
        User prefers async -> Python (applies to all Python sub-contexts)
    """
    node_id: str
    context_type: ContextType
    name: str
    description: str = ""
    parent_id: Optional[str] = None  # For hierarchical scoping
    children_ids: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    weight: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    last_referenced: datetime = field(default_factory=datetime.now)
    reference_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def reference(self) -> None:
        """Mark this context as recently referenced."""
        self.last_referenced = datetime.now()
        self.reference_count += 1
        self.weight = min(1.0, self.weight + 0.02)
    
    def get_scope_path(self, all_nodes: Dict[str, "ContextNode"]) -> List[str]:
        """Get the full scope path from root to this node."""
        path = [self.name]
        current = self
        while current.parent_id and current.parent_id in all_nodes:
            current = all_nodes[current.parent_id]
            path.insert(0, current.name)
        return path
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "context_type": self.context_type.name,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "embedding": self.embedding,
            "weight": self.weight,
            "created_at": self.created_at.isoformat(),
            "last_referenced": self.last_referenced.isoformat(),
            "reference_count": self.reference_count,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextNode":
        return cls(
            node_id=data["node_id"],
            context_type=ContextType[data["context_type"]],
            name=data["name"],
            description=data.get("description", ""),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            embedding=data.get("embedding"),
            weight=data.get("weight", 0.5),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_referenced=datetime.fromisoformat(data["last_referenced"]),
            reference_count=data.get("reference_count", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ScopedRule:
    """
    v3.0 SCIENTIFIC MEMORY RULE
    
    A behavioral rule scoped to specific context nodes with lifecycle state.
    
    LIFECYCLE: HYPOTHESIS → VALIDATING → ESTABLISHED → (DEPRECATED)
    Only ESTABLISHED rules are injected into prompts.
    
    Scoping eliminates context collapse:
        - User --[prefers async]--> Python
        - User --[prefers promises]--> JavaScript
        No contradiction! Different scopes.
    """
    rule_id: str
    content: str
    scope_path: List[str] = field(default_factory=list)  # ["Python", "FastAPI"]
    target_node: str = "global"  # Context node ID
    relation: RelationType = RelationType.PREFERS
    source_node: str = "user"
    
    # Scientific Memory fields
    confidence: float = 0.2       # Starts low (hypothesis)
    state: RuleState = RuleState.HYPOTHESIS
    validation_count: int = 0     # Times validated
    rejection_count: int = 0      # Times contradicted
    
    # Metadata
    weight: float = 0.5
    embedding: Optional[List[float]] = None
    source_count: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    last_activated: datetime = field(default_factory=datetime.now)
    promoted_from: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # =============================
    # SCIENTIFIC MEMORY METHODS
    # =============================
    
    def is_hypothesis(self) -> bool:
        """Is this rule just a theory?"""
        return self.state == RuleState.HYPOTHESIS
    
    def is_established(self) -> bool:
        """Is this rule a proven fact?"""
        return self.state == RuleState.ESTABLISHED
    
    def validate(self, boost: float = 0.15) -> None:
        """User confirmed this behavior. Boost confidence."""
        self.validation_count += 1
        self.confidence = min(1.0, self.confidence + boost)
        self.source_count += 1
        self.last_activated = datetime.now()
        self._update_state()
    
    def reject(self, penalty: float = 0.25) -> None:
        """User contradicted this behavior. Reduce confidence."""
        self.rejection_count += 1
        self.confidence = max(0.0, self.confidence - penalty)
        self._update_state()
    
    def _update_state(self) -> None:
        """Auto-transition state based on confidence thresholds (v4.0 with SHADOW)."""
        if self.confidence >= 0.8:
            self.state = RuleState.ESTABLISHED
        elif self.confidence >= 0.6:
            self.state = RuleState.VALIDATING
        elif self.confidence >= 0.4:
            self.state = RuleState.SHADOW  # v4.0: Silent testing phase
        elif self.confidence < 0.2:
            self.state = RuleState.DEPRECATED
        else:
            self.state = RuleState.HYPOTHESIS
    
    def activate(self) -> None:
        """Mark rule as recently used."""
        self.last_activated = datetime.now()
    
    def reinforce(self, boost: float = 0.05) -> None:
        """Strengthen this rule (alias for validate with smaller boost)."""
        self.validate(boost)
    
    def contradict(self, penalty: float = 0.15) -> None:
        """Weaken this rule (alias for reject)."""
        self.reject(penalty)
    
    def matches_context(self, active_context: List[str]) -> bool:
        """Check if this rule applies to the given context."""
        if not self.scope_path:
            return True  # Global rule
        
        # Check if scope_path is a prefix of or matches active_context
        for i, scope in enumerate(self.scope_path):
            if i >= len(active_context):
                return False
            if scope.lower() != active_context[i].lower():
                return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "content": self.content,
            "scope_path": self.scope_path,
            "target_node": self.target_node,
            "relation": self.relation.name,
            "source_node": self.source_node,
            "confidence": self.confidence,
            "state": self.state.value,
            "validation_count": self.validation_count,
            "rejection_count": self.rejection_count,
            "weight": self.weight,
            "embedding": self.embedding,
            "source_count": self.source_count,
            "created_at": self.created_at.isoformat(),
            "last_activated": self.last_activated.isoformat(),
            "promoted_from": self.promoted_from,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScopedRule":
        rule = cls(
            rule_id=data["rule_id"],
            content=data["content"],
            scope_path=data.get("scope_path", []),
            target_node=data.get("target_node", "global"),
            relation=RelationType[data.get("relation", "PREFERS")],
            source_node=data.get("source_node", "user"),
            confidence=data.get("confidence", 0.2),
            validation_count=data.get("validation_count", 0),
            rejection_count=data.get("rejection_count", 0),
            weight=data.get("weight", 0.5),
            embedding=data.get("embedding"),
            source_count=data.get("source_count", 1),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activated=datetime.fromisoformat(data["last_activated"]),
            promoted_from=data.get("promoted_from"),
            metadata=data.get("metadata", {}),
        )
        # Set state from string
        state_str = data.get("state", "hypothesis")
        rule.state = RuleState(state_str)
        return rule


@dataclass
class Hypothesis:
    """
    v3 HYPOTHESIS
    
    A tentative rule awaiting validation before becoming a ScopedRule.
    
    BREAKTHROUGH: Instead of immediately creating rules from signals,
    we create hypotheses that must be validated:
    
    Lifecycle:
        1. Signal detected → Hypothesis created (confidence: 0.1)
        2. User adheres to hypothesis → validations++
        3. User contradicts hypothesis → rejections++
        4. If validations >= 3 → Promote to ScopedRule (confidence: 0.8)
        5. If rejections >= 2 → Delete hypothesis
        6. If expired → Archive and delete
    
    This dramatically improves accuracy by requiring multiple confirmations.
    """
    hypothesis_id: str
    proposed_content: str
    proposed_scope_path: List[str]
    proposed_relation: RelationType
    proposed_target_node: str
    
    # Validation tracking
    confidence: float = 0.1  # Starts low
    validations: int = 0     # Times user adhered
    rejections: int = 0      # Times user contradicted
    
    # State
    state: HypothesisState = HypothesisState.PENDING
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None  # Will be set on creation
    validation_interactions: int = 0  # Counter for interaction-based expiry
    
    # Source tracking
    source_signal_type: Optional[str] = None
    source_hash: Optional[str] = None
    embedding: Optional[List[float]] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Thresholds (class-level defaults)
    VALIDATION_THRESHOLD: int = 3   # Validations needed to promote
    REJECTION_THRESHOLD: int = 2    # Rejections to delete
    INTERACTION_EXPIRY: int = 10    # Expire after N interactions without validation
    
    def validate(self) -> bool:
        """
        Record a validation (user adhered to hypothesis).
        Returns True if promoted to rule.
        """
        self.validations += 1
        self.confidence = min(0.9, self.confidence + 0.2)
        self.state = HypothesisState.VALIDATING
        
        if self.validations >= self.VALIDATION_THRESHOLD:
            self.state = HypothesisState.PROMOTED
            return True
        return False
    
    def reject(self) -> bool:
        """
        Record a rejection (user contradicted hypothesis).
        Returns True if should be deleted.
        """
        self.rejections += 1
        self.confidence = max(0.0, self.confidence - 0.3)
        
        if self.rejections >= self.REJECTION_THRESHOLD:
            self.state = HypothesisState.REJECTED
            return True
        return False
    
    def check_expiry(self) -> bool:
        """Check if hypothesis has expired. Returns True if expired."""
        from datetime import datetime
        
        # Time-based expiry
        if self.expires_at and datetime.now() > self.expires_at:
            self.state = HypothesisState.EXPIRED
            return True
        
        # Interaction-based expiry
        if self.validation_interactions >= self.INTERACTION_EXPIRY:
            self.state = HypothesisState.EXPIRED
            return True
        
        return False
    
    def record_interaction(self) -> None:
        """Record that an interaction occurred (for expiry tracking)."""
        self.validation_interactions += 1
    
    def to_scoped_rule(self) -> ScopedRule:
        """Convert promoted hypothesis to a ScopedRule."""
        import uuid
        return ScopedRule(
            rule_id=f"rule_{uuid.uuid4().hex[:8]}",
            source_node="user",
            target_node=self.proposed_target_node,
            relation=self.proposed_relation,
            content=self.proposed_content,
            weight=0.7,
            confidence=0.8,
            scope_path=self.proposed_scope_path,
            embedding=self.embedding,
            source_count=self.validations,
            promoted_from=self.hypothesis_id,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "proposed_content": self.proposed_content,
            "proposed_scope_path": self.proposed_scope_path,
            "proposed_relation": self.proposed_relation.name,
            "proposed_target_node": self.proposed_target_node,
            "confidence": self.confidence,
            "validations": self.validations,
            "rejections": self.rejections,
            "state": self.state.name,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "validation_interactions": self.validation_interactions,
            "source_signal_type": self.source_signal_type,
            "source_hash": self.source_hash,
            "embedding": self.embedding,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hypothesis":
        h = cls(
            hypothesis_id=data["hypothesis_id"],
            proposed_content=data["proposed_content"],
            proposed_scope_path=data.get("proposed_scope_path", []),
            proposed_relation=RelationType[data["proposed_relation"]],
            proposed_target_node=data["proposed_target_node"],
            confidence=data.get("confidence", 0.1),
            validations=data.get("validations", 0),
            rejections=data.get("rejections", 0),
            state=HypothesisState[data.get("state", "PENDING")],
            created_at=datetime.fromisoformat(data["created_at"]),
            validation_interactions=data.get("validation_interactions", 0),
            source_signal_type=data.get("source_signal_type"),
            source_hash=data.get("source_hash"),
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
        )
        if data.get("expires_at"):
            h.expires_at = datetime.fromisoformat(data["expires_at"])
        return h


@dataclass
class CollaborationRequest:
    """
    v3.1 SOCRATIC CONFLICT RESOLUTION
    
    A request for user collaboration when a contradiction is detected
    between a new signal and an ESTABLISHED rule.
    
    Instead of assuming (v2) or silent hypothesis (v3.0), we now
    ask the user primarily when there is a CONFLICT.
    """
    request_id: str
    trigger_signal: Signal
    conflicting_rule: ScopedRule
    reason: str
    proposed_options: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "trigger_signal": self.trigger_signal.to_dict(),
            "conflicting_rule": self.conflicting_rule.to_dict(),
            "reason": self.reason,
            "proposed_options": self.proposed_options,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# IBLM v3.1 - GOAL-CONSTRAINED KERNEL
# =============================================================================

@dataclass
class UserGoal:
    """
    v3.1 USER GOAL (Constraint)
    
    A high-priority constraint that OVERRIDES UserFacts.
    Goals represent what the user WANTS, not just what they DO.
    
    Example:
        Goal: "Write clean, maintainable code" (Priority 10)
        Fact: "User types fast" (Priority 5)
        Result: Speed is sacrificed for cleanliness.
    """
    goal_id: str
    content: str
    scope_path: List[str] = field(default_factory=list)
    secondary_context: List[str] = field(default_factory=list)  # v4.0: Alternative to fuzzy scoping
    priority: int = 10  # Higher = More Important
    confidence: float = 0.8
    expiry: Optional[datetime] = None  # None = permanent
    created_at: datetime = field(default_factory=datetime.now)
    last_reinforced: datetime = field(default_factory=datetime.now)  # v4.0: Goal Entropy
    half_life_days: int = 7  # v4.0: Decay rate
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def decay_priority(self) -> int:
        """v4.0 GOAL ENTROPY: Calculate decayed priority based on time since reinforcement."""
        from datetime import timedelta
        days_since = (datetime.now() - self.last_reinforced).days
        decay_factor = 0.5 ** (days_since / self.half_life_days)
        return max(1, int(self.priority * decay_factor))
    
    def reinforce(self) -> None:
        """Reinforce this goal to reset decay."""
        self.last_reinforced = datetime.now()
    
    def is_active(self) -> bool:
        """Check if goal is still active (not expired and has meaningful priority)."""
        if self.expiry and datetime.now() >= self.expiry:
            return False
        return self.decay_priority() >= 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "content": self.content,
            "scope_path": self.scope_path,
            "priority": self.priority,
            "confidence": self.confidence,
            "expiry": self.expiry.isoformat() if self.expiry else None,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserGoal":
        return cls(
            goal_id=data["goal_id"],
            content=data["content"],
            scope_path=data.get("scope_path", []),
            priority=data.get("priority", 10),
            confidence=data.get("confidence", 0.8),
            expiry=datetime.fromisoformat(data["expiry"]) if data.get("expiry") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class UserFact:
    """
    v3.1 USER FACT (Preference)
    
    A lower-priority behavioral observation. Facts can be overridden by Goals.
    
    Example:
        Fact: "User likes chocolate" (Priority 5)
        Goal: "User wants to lose weight" (Priority 10)
        -> Goal overrides Fact.
    """
    fact_id: str
    content: str
    scope_path: List[str] = field(default_factory=list)
    priority: int = 5  # Lower than Goals
    confidence: float = 0.5
    source: str = "observation"  # "observation", "explicit", "inferred"
    created_at: datetime = field(default_factory=datetime.now)
    last_validated: datetime = field(default_factory=datetime.now)
    validation_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self, boost: float = 0.1) -> None:
        """User confirmed this fact."""
        self.validation_count += 1
        self.confidence = min(1.0, self.confidence + boost)
        self.last_validated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "content": self.content,
            "scope_path": self.scope_path,
            "priority": self.priority,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "last_validated": self.last_validated.isoformat(),
            "validation_count": self.validation_count,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserFact":
        return cls(
            fact_id=data["fact_id"],
            content=data["content"],
            scope_path=data.get("scope_path", []),
            priority=data.get("priority", 5),
            confidence=data.get("confidence", 0.5),
            source=data.get("source", "observation"),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_validated=datetime.fromisoformat(data.get("last_validated", data["created_at"])),
            validation_count=data.get("validation_count", 0),
            metadata=data.get("metadata", {}),
        )
