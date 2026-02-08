"""
IBLM Core - Configuration
=========================

Centralized configuration with environment variable support.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResourceLimits:
    """Resource limits to prevent DoS and memory issues."""
    max_rules: int = 1000
    max_nodes: int = 500
    max_pending_signals: int = 100
    max_working_memory_items: int = 20
    max_interaction_logs: int = 1000
    max_export_size_bytes: int = 10_000_000  # 10MB
    max_user_input_length: int = 50_000
    max_ai_output_length: int = 100_000
    max_rule_content_length: int = 1000
    max_node_context_length: int = 5000


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    enabled: bool = True
    observe_max_calls: int = 100
    observe_period_seconds: int = 60
    evolve_max_calls: int = 20
    evolve_period_seconds: int = 60


@dataclass
class SecurityConfig:
    """Security-related configuration."""
    enable_input_validation: bool = True
    enable_content_sanitization: bool = True
    enable_integrity_checks: bool = True
    encryption_algorithm: str = "AES-256-GCM"
    hash_algorithm: str = "SHA-256"
    min_password_length: int = 8


@dataclass
class EvolutionConfig:
    """Configuration for the evolve() algorithm."""
    correction_weight_boost: float = 0.3
    reinforcement_boost: float = 0.1
    contradiction_penalty: float = 0.5
    min_signals_for_rule: int = 2
    min_confidence_for_rule: float = 0.5
    similarity_threshold: float = 0.75
    decay_rate: float = 0.01
    min_weight_threshold: float = 0.1
    max_evolution_cycles: int = 100  # Prevent infinite loops


@dataclass
class EmbeddingConfig:
    """Configuration for the embedding engine."""
    vector_size: int = 128
    cache_embeddings: bool = True
    max_cache_size: int = 10000


@dataclass
class IBLMProductionConfig:
    """
    Complete production configuration for IBLM.
    
    Loads from environment variables with sensible defaults.
    """
    # Resource limits
    limits: ResourceLimits = field(default_factory=ResourceLimits)
    
    # Rate limiting
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    
    # Security
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Evolution algorithm
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    
    # Embedding engine
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    
    # Behavior settings
    auto_evolve: bool = True
    auto_gc: bool = True
    gc_threshold: int = 20
    injection_format: str = "natural"
    max_context_tokens: int = 500
    auto_save: bool = False
    save_path: Optional[str] = None
    
    # Thread safety
    enable_thread_safety: bool = True
    
    # Logging
    enable_metrics: bool = True
    log_level: str = "INFO"
    
    # Schema version for migrations
    schema_version: str = "2.0.0"
    
    @classmethod
    def from_env(cls) -> "IBLMProductionConfig":
        """Load configuration from environment variables."""
        config = cls()
        
        # Override from environment
        if os.getenv("IBLM_MAX_RULES"):
            config.limits.max_rules = int(os.getenv("IBLM_MAX_RULES"))
        if os.getenv("IBLM_MAX_NODES"):
            config.limits.max_nodes = int(os.getenv("IBLM_MAX_NODES"))
        if os.getenv("IBLM_RATE_LIMIT_ENABLED"):
            config.rate_limit.enabled = os.getenv("IBLM_RATE_LIMIT_ENABLED").lower() == "true"
        if os.getenv("IBLM_THREAD_SAFETY"):
            config.enable_thread_safety = os.getenv("IBLM_THREAD_SAFETY").lower() == "true"
        if os.getenv("IBLM_AUTO_EVOLVE"):
            config.auto_evolve = os.getenv("IBLM_AUTO_EVOLVE").lower() == "true"
        if os.getenv("IBLM_LOG_LEVEL"):
            config.log_level = os.getenv("IBLM_LOG_LEVEL")
        
        return config
    
    @classmethod
    def development(cls) -> "IBLMProductionConfig":
        """Get development configuration (relaxed limits)."""
        config = cls()
        config.rate_limit.enabled = False
        config.enable_metrics = True
        config.log_level = "DEBUG"
        return config
    
    @classmethod
    def production(cls) -> "IBLMProductionConfig":
        """Get production configuration (strict limits)."""
        config = cls()
        config.rate_limit.enabled = True
        config.security.enable_input_validation = True
        config.security.enable_integrity_checks = True
        config.enable_thread_safety = True
        config.log_level = "WARNING"
        return config
    
    def validate(self) -> None:
        """Validate configuration values."""
        from .exceptions import ValidationError
        
        if self.limits.max_rules < 1:
            raise ValidationError("max_rules must be at least 1")
        if self.limits.max_nodes < 1:
            raise ValidationError("max_nodes must be at least 1")
        if not 0 < self.evolution.min_confidence_for_rule <= 1.0:
            raise ValidationError("min_confidence_for_rule must be between 0 and 1")
        if self.security.min_password_length < 4:
            raise ValidationError("min_password_length must be at least 4")


# Default configuration instance
DEFAULT_CONFIG = IBLMProductionConfig()


def get_config() -> IBLMProductionConfig:
    """Get the current configuration."""
    return DEFAULT_CONFIG


def set_config(config: IBLMProductionConfig) -> None:
    """Set the global configuration."""
    global DEFAULT_CONFIG
    config.validate()
    DEFAULT_CONFIG = config
