"""
IBLM Core - Main Interface
==========================

The unified API for the Individual Behavior Learning Machine.

This is the main entry point for using IBLM. It provides a clean,
simple interface that orchestrates all components:

- InteractionObserver: Extracts signals from conversations
- LogicCompiler: Compiles signals into rules, implements evolve()
- UserKernel: Stores the living memory
- ContextInjector: Injects personalized context

USAGE:
    from iblm import IBLM
    
    # Create or load a brain
    brain = IBLM()
    
    # Observe interactions
    brain.observe("Use Python", "Here's Python code...")
    brain.observe("Actually use TypeScript", "Converting to TS...")
    
    # Get enhanced context for a new prompt
    context = brain.inject("Write a function")
    print(context.system_header)  # Contains preference for TypeScript
    
    # Export the brain for later use
    brain.save("my_brain.json")
    
    # Load in a new session
    brain2 = IBLM.load("my_brain.json")

BREAKTHROUGH: The brain captures WHO the user is, not just what they said.
"""

import uuid
import json
import gzip
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from pathlib import Path

try:
    from .models import (
        Signal, SignalType, Rule, RuleCategory, 
        KernelNode, StyleVector, UserProfile
    )
    from .kernel import UserKernel
    from .observer import InteractionObserver
    from .compiler import LogicCompiler, EvolutionReport
    from .injector import ContextInjector, InjectionConfig, InjectionResult
    from .embeddings import EmbeddingEngine, EmbeddingConfig
except ImportError:
    from models import (
        Signal, SignalType, Rule, RuleCategory, 
        KernelNode, StyleVector, UserProfile
    )
    from kernel import UserKernel
    from observer import InteractionObserver
    from compiler import LogicCompiler, EvolutionReport
    from injector import ContextInjector, InjectionConfig, InjectionResult
    from embeddings import EmbeddingEngine, EmbeddingConfig


@dataclass
class IBLMConfig:
    """Configuration for the IBLM instance."""
    # Kernel behavior
    auto_evolve: bool = True           # Automatically evolve after observe
    auto_gc: bool = True               # Automatic garbage collection
    gc_threshold: int = 20             # Interactions before GC
    
    # Injection settings
    injection_format: str = "natural"   # "natural" or "structured"
    max_context_tokens: int = 500       # Max tokens in system header
    
    # Embedding settings
    embedding_size: int = 128           # Embedding vector dimension
    cache_embeddings: bool = True       # Cache embeddings
    
    # Persistence
    auto_save: bool = False             # Auto-save after evolution
    save_path: Optional[str] = None     # Path for auto-save
    
    # Production features
    enable_validation: bool = True      # Input validation
    enable_thread_safety: bool = True   # Thread-safe operations
    enable_rate_limiting: bool = False  # Rate limiting (off by default)
    enable_encryption: bool = False     # Encryption for exports
    
    # Resource limits
    max_rules: int = 1000
    max_nodes: int = 500
    max_pending_signals: int = 100


class IBLM:
    """
    The Individual Behavior Learning Machine.
    
    IBLM is a breakthrough context engine that learns WHO a user is,
    not just what they've said. It achieves infinite context scaling
    by compiling interactions into behavioral rules.
    
    CORE CONCEPT:
    
    Traditional approaches store raw chat history:
    - User: "Use Python"
    - AI: "Here's Python code..."
    - User: "No, use TypeScript"
    - AI: "Converting..."
    - ...repeat for 1000 messages = 100,000+ tokens
    
    IBLM compiles this into:
    - Rule: "User prefers TypeScript over Python" (weight: 0.9)
    - Profile: { expertise: ["web dev"], style: "concise" }
    - ~100 tokens total, regardless of history length
    
    USAGE PATTERN:
    
    1. OBSERVE: Feed (user_input, ai_output) pairs
       brain.observe(user_input, ai_output)
       
    2. INJECT: Get personalized context for new prompts  
       context = brain.inject(new_prompt)
       
    3. SAVE/LOAD: Persist the brain across sessions
       brain.save("brain.json")
       brain = IBLM.load("brain.json")
    
    ATTRIBUTES:
        kernel: The UserKernel (living memory)
        observer: Extracts signals from interactions
        compiler: Compiles signals into rules
        injector: Injects context into prompts
        config: Configuration settings
    
    PRODUCTION FEATURES:
        - Context manager support (with IBLM() as brain:)
        - Input validation and sanitization
        - Thread-safe operations
        - Resource limits
        - Health checks
    """
    
    def __init__(
        self, 
        config: Optional[IBLMConfig] = None,
        kernel: Optional[UserKernel] = None
    ):
        """
        Initialize IBLM.
        
        Args:
            config: Optional configuration
            kernel: Optional pre-existing kernel to use
        """
        self.config = config or IBLMConfig()
        self.id = str(uuid.uuid4())[:8]
        self._closed = False
        
        # Initialize embedding engine
        embedding_config = EmbeddingConfig(
            vector_size=self.config.embedding_size,
            cache_embeddings=self.config.cache_embeddings,
        )
        embedding_engine = EmbeddingEngine(embedding_config)
        
        # Resource limits for kernel
        resource_limits = {
            "max_rules": self.config.max_rules,
            "max_nodes": self.config.max_nodes,
            "max_pending_signals": self.config.max_pending_signals,
        }
        
        # Initialize or use provided kernel
        self.kernel = kernel or UserKernel(
            embedding_engine,
            enable_thread_safety=self.config.enable_thread_safety,
            resource_limits=resource_limits
        )
        
        # Initialize components
        self.observer = InteractionObserver()
        self.compiler = LogicCompiler(self.kernel)
        
        injection_config = InjectionConfig(
            format=self.config.injection_format,
            max_header_tokens=self.config.max_context_tokens,
        )
        self.injector = ContextInjector(self.kernel, injection_config)
        
        # Interaction counter for GC
        self._interaction_count = 0
        
        # Statistics
        self._total_observations = 0
        self._total_evolutions = 0
        self._validation_errors = 0
    
    # ===========================
    # CONTEXT MANAGER
    # ===========================
    
    def __enter__(self) -> "IBLM":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with cleanup."""
        self.close()
    
    def close(self) -> None:
        """
        Clean up resources and optionally save.
        
        Call this when done with the brain, or use context manager.
        """
        if self._closed:
            return
        
        # Clear working memory
        self.kernel.clear_working_memory()
        
        # Auto-save if configured
        if self.config.auto_save and self.config.save_path:
            self.save(self.config.save_path)
        
        self._closed = True
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check and return status.
        
        Returns:
            Dict with health status and metrics
        """
        return {
            "status": "healthy" if not self._closed else "closed",
            "id": self.id,
            "rules_count": len(self.kernel.rules),
            "nodes_count": len(self.kernel.nodes),
            "observations": self._total_observations,
            "evolutions": self._total_evolutions,
            "validation_errors": self._validation_errors,
            "profile_confidence": self.kernel.profile.profile_confidence,
            "kernel_metrics": self.kernel.get_metrics(),
        }
    
    def _validate_input(self, text: str, field_name: str = "input") -> str:
        """Validate and sanitize input text."""
        if not self.config.enable_validation:
            return text
        
        try:
            from .validators import InputValidator
        except ImportError:
            from validators import InputValidator
        
        result = InputValidator.validate_user_input(text, strict=False)
        if not result.valid:
            self._validation_errors += 1
        return result.sanitized_value
    
    # ===========================
    # CORE API
    # ===========================
    
    def observe(
        self, 
        user_input: str, 
        ai_output: str,
        evolve: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Observe a user-AI interaction and learn from it.
        
        This is the primary learning method. Feed it (user_input, ai_output)
        pairs and IBLM will extract signals and optionally evolve.
        
        Args:
            user_input: What the user said
            ai_output: What the AI responded
            evolve: Override auto_evolve setting
            
        Returns:
            Dict with observation results
            
        Raises:
            ValidationError: If validation enabled and input is malicious
        """
        # Validate and sanitize inputs
        user_input = self._validate_input(user_input, "user_input")
        ai_output = self._validate_input(ai_output, "ai_output")
        
        # Log the interaction
        log_id = self.kernel.log_interaction(user_input, ai_output)
        
        if log_id is None:
            return {"status": "skipped", "reason": "duplicate"}
        
        # Extract signals
        result = self.observer.observe(user_input, ai_output)
        
        # Add signals to kernel
        for signal in result.signals:
            self.kernel.add_signal(signal)
        
        self._interaction_count += 1
        self._total_observations += 1
        
        # Evolve if configured
        should_evolve = evolve if evolve is not None else self.config.auto_evolve
        evolution_report = None
        
        if should_evolve:
            evolution_report = self.evolve()
        
        # Auto garbage collection
        if self.config.auto_gc and self._interaction_count >= self.config.gc_threshold:
            self.garbage_collect()
        
        # Auto-save
        if self.config.auto_save and self.config.save_path:
            self.save(self.config.save_path)
        
        return {
            "status": "observed",
            "log_id": log_id,
            "signals_extracted": len(result.signals),
            "confidence": result.confidence_score,
            "evolution": str(evolution_report) if evolution_report else None,
        }
    
    def evolve(self) -> EvolutionReport:
        """
        Trigger evolution of the kernel.
        
        This compiles pending signals into rules, updates weights,
        and performs garbage collection if needed.
        
        Returns:
            EvolutionReport with statistics
        """
        signals = self.kernel.get_pending_signals()
        report = self.compiler.evolve(signals)
        self._total_evolutions += 1
        return report
    
    def inject(
        self, 
        prompt: str,
        enhance_prompt: bool = False
    ) -> InjectionResult:
        """
        Get personalized context for a prompt.
        
        This queries the kernel for relevant rules, nodes, and profile
        information and builds a system header for the LLM.
        
        Args:
            prompt: The user's prompt
            enhance_prompt: Whether to enhance the prompt with context
            
        Returns:
            InjectionResult with system_header and metadata
        """
        result = self.injector.inject(prompt)
        
        if enhance_prompt:
            enhanced = self.injector.enhance_prompt(prompt)
            # Store enhanced version in result
            result.enhanced_prompt = enhanced
        
        return result
    
    def correct(
        self, 
        original_response: str, 
        correction: str
    ) -> EvolutionReport:
        """
        Process an explicit user correction.
        
        Use this when the user explicitly corrects AI behavior.
        Corrections are high-priority learning events.
        
        Args:
            original_response: What the AI said that was wrong
            correction: What the user wants instead
            
        Returns:
            EvolutionReport
        """
        return self.compiler.process_correction(original_response, correction)
    
    def teach(
        self,
        instruction: str,
        category: str = "preference"
    ) -> str:
        """
        Directly teach IBLM a rule.
        
        Use this for explicit user instructions like:
        - "Always use TypeScript"
        - "I'm an expert in machine learning"
        - "Call me by my first name"
        
        Args:
            instruction: The rule to teach
            category: Type of instruction
            
        Returns:
            Rule ID
        """
        category_map = {
            "preference": RuleCategory.TECHNICAL_PREFERENCE,
            "style": RuleCategory.COMMUNICATION_STYLE,
            "expertise": RuleCategory.DOMAIN_EXPERTISE,
            "workflow": RuleCategory.WORKFLOW_PATTERN,
            "personality": RuleCategory.PERSONALITY_TRAIT,
        }
        
        rule_category = category_map.get(category, RuleCategory.BEHAVIORAL_PATTERN)
        
        return self.compiler.force_rule(
            condition="Always apply",
            action=instruction,
            category=rule_category,
            weight=0.9  # High weight for explicit teaching
        )
    
    # ===========================
    # PROJECT CONTEXT
    # ===========================
    
    def set_project(self, project_name: str, context: str = "") -> str:
        """
        Set the active project context.
        
        Args:
            project_name: Name of the project
            context: Optional description
            
        Returns:
            Node ID for the project
        """
        # Set active project in kernel
        self.kernel.set_active_project(project_name)
        
        # Create or update project node
        existing = self.kernel.find_node_by_name(project_name)
        
        if existing:
            if context:
                existing.context = context
            existing.reference()
            return existing.node_id
        else:
            node = KernelNode(
                node_id=str(uuid.uuid4()),
                node_type="project",
                name=project_name,
                context=context or f"User's {project_name} project",
                weight=0.8,  # Projects start with high weight
            )
            return self.kernel.add_node(node)
    
    def add_project_note(self, note: str) -> None:
        """Add a note to working memory for current session."""
        self.kernel.set_working_memory(
            f"note_{datetime.now().strftime('%H%M%S')}",
            note
        )
    
    def clear_session(self) -> None:
        """Clear working memory (end of session)."""
        self.kernel.clear_working_memory()
    
    # ===========================
    # GARBAGE COLLECTION
    # ===========================
    
    def garbage_collect(self) -> Dict[str, int]:
        """
        Trigger garbage collection.
        
        This:
        - Deletes processed interaction logs
        - Prunes low-weight rules
        - Consolidates similar rules
        
        BREAKTHROUGH: This is how we achieve infinite scaling.
        Once knowledge is compiled into rules, the source is deleted.
        
        Returns:
            Statistics about what was cleaned
        """
        result = self.kernel.garbage_collect()
        self._interaction_count = 0  # Reset counter
        return result
    
    # ===========================
    # PERSISTENCE
    # ===========================
    
    def save(self, path: str) -> None:
        """
        Save the IBLM brain to a file.
        
        The brain is saved as a compressed JSON file containing:
        - All rules
        - All nodes
        - User profile
        - Style vector
        - Configuration
        
        Args:
            path: File path (will add .json.gz if not present)
        """
        path = Path(path)
        if path.suffix == '':
            path = path.with_suffix('.json.gz')
        
        data = self.export()
        
        if path.suffix == '.gz' or path.name.endswith('.json.gz'):
            with gzip.open(path, 'wt', encoding='utf-8') as f:
                json.dump(data, f)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, path: str, config: Optional[IBLMConfig] = None) -> "IBLM":
        """
        Load an IBLM brain from a file.
        
        Args:
            path: Path to saved brain file
            config: Optional config override
            
        Returns:
            IBLM instance with loaded brain
        """
        path = Path(path)
        
        if path.suffix == '.gz' or path.name.endswith('.json.gz'):
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        return cls.from_dict(data, config)
    
    def export(self) -> Dict[str, Any]:
        """
        Export the brain to a dictionary.
        
        Returns:
            Complete brain state as dict
        """
        kernel_data = self.kernel.export()
        
        return {
            "version": "1.0.0",
            "id": self.id,
            "created_at": datetime.now().isoformat(),
            "stats": {
                "total_observations": self._total_observations,
                "total_evolutions": self._total_evolutions,
            },
            "config": {
                "auto_evolve": self.config.auto_evolve,
                "auto_gc": self.config.auto_gc,
                "gc_threshold": self.config.gc_threshold,
                "injection_format": self.config.injection_format,
                "max_context_tokens": self.config.max_context_tokens,
            },
            "kernel": kernel_data,
        }
    
    @classmethod
    def from_dict(
        cls, 
        data: Dict[str, Any],
        config: Optional[IBLMConfig] = None
    ) -> "IBLM":
        """
        Create IBLM from exported dictionary.
        
        Args:
            data: Exported brain data
            config: Optional config override
            
        Returns:
            Restored IBLM instance
        """
        # Load kernel
        kernel = UserKernel.load(data.get("kernel", {}))
        
        # Create config from data or use provided
        if config is None:
            config_data = data.get("config", {})
            config = IBLMConfig(
                auto_evolve=config_data.get("auto_evolve", True),
                auto_gc=config_data.get("auto_gc", True),
                gc_threshold=config_data.get("gc_threshold", 20),
                injection_format=config_data.get("injection_format", "natural"),
                max_context_tokens=config_data.get("max_context_tokens", 500),
            )
        
        # Create IBLM with loaded kernel
        iblm = cls(config=config, kernel=kernel)
        iblm.id = data.get("id", iblm.id)
        
        # Restore stats
        stats = data.get("stats", {})
        iblm._total_observations = stats.get("total_observations", 0)
        iblm._total_evolutions = stats.get("total_evolutions", 0)
        
        return iblm
    
    def save_encrypted(self, path: str, password: str) -> None:
        """
        Save the brain with encryption.
        
        SECURITY: Uses AES-256 equivalent encryption with PBKDF2 key derivation.
        
        Args:
            path: File path for encrypted brain
            password: Encryption password (min 8 characters)
        """
        try:
            from .security import encrypt_data
        except ImportError:
            from security import encrypt_data
        
        data = self.export()
        json_str = json.dumps(data)
        encrypted = encrypt_data(json_str, password)
        
        path = Path(path)
        if path.suffix == '':
            path = path.with_suffix('.iblm.enc')
        
        with open(path, 'wb') as f:
            f.write(encrypted)
    
    @classmethod
    def load_encrypted(
        cls, 
        path: str, 
        password: str,
        config: Optional[IBLMConfig] = None
    ) -> "IBLM":
        """
        Load an encrypted brain file.
        
        Args:
            path: Path to encrypted brain file
            password: Decryption password
            config: Optional config override
            
        Returns:
            IBLM instance with loaded brain
            
        Raises:
            IntegrityError: If decryption fails (wrong password or tampered data)
        """
        try:
            from .security import decrypt_data
        except ImportError:
            from security import decrypt_data
        
        with open(path, 'rb') as f:
            encrypted = f.read()
        
        json_str = decrypt_data(encrypted, password)
        data = json.loads(json_str)
        
        return cls.from_dict(data, config)
    
    # ===========================
    # UTILITIES
    # ===========================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        kernel_stats = self.kernel.get_stats()
        
        return {
            "iblm_id": self.id,
            "total_observations": self._total_observations,
            "total_evolutions": self._total_evolutions,
            **kernel_stats,
        }
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the brain."""
        return self.injector.get_context_summary()
    
    def get_user_persona(self) -> str:
        """Get the compiled user persona."""
        return self.kernel.profile.generate_persona_prompt()
    
    def get_reflection_prompt(self) -> str:
        """
        Get a prompt that makes the LLM embody the user.
        
        Use this for planning, review, or generating user-like responses.
        """
        return self.injector.generate_reflection_prompt()
    
    def __repr__(self) -> str:
        stats = self.kernel.get_stats()
        return (
            f"IBLM(id={self.id}, "
            f"rules={stats['total_rules']}, "
            f"nodes={stats['total_nodes']}, "
            f"confidence={self.kernel.profile.profile_confidence:.1%})"
        )


# ===========================
# CONVENIENCE FUNCTIONS
# ===========================

def create_brain(save_path: Optional[str] = None) -> IBLM:
    """Create a new IBLM brain with sensible defaults."""
    config = IBLMConfig(
        auto_save=save_path is not None,
        save_path=save_path,
    )
    return IBLM(config)


def load_brain(path: str) -> IBLM:
    """Load an existing IBLM brain."""
    return IBLM.load(path)


def quick_observe(
    brain: IBLM,
    user_inputs: List[str],
    ai_outputs: List[str]
) -> List[Dict[str, Any]]:
    """
    Quickly observe multiple interactions.
    
    Useful for bulk training.
    """
    results = []
    for user_input, ai_output in zip(user_inputs, ai_outputs):
        result = brain.observe(user_input, ai_output, evolve=False)
        results.append(result)
    
    # Single evolution at the end
    brain.evolve()
    
    return results
