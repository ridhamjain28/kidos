# IBLM Core - Individual Behavior Learning Machine
# A Breakthrough Recursive Context Compiler
# 
# v3 COGNITIVE BREAKTHROUGH:
# - Scoped Probabilistic Kernel (no context collapse!)
# - Hypothesis Engine (validated learning)
# - Cold Storage Protocol (archive, don't delete!)

__version__ = "3.0.0"
__author__ = "IBLM Research"

# Core models (v2 compatible)
from .models import (
    SignalType,
    Signal,
    Rule,
    RuleCategory,
    KernelNode,
    StyleVector,
    UserProfile,
    InteractionLog,
)

# v3 Scoped Models
from .models import (
    ContextNode,
    ContextType,
    ScopedRule,
    RelationType,
    Hypothesis,
    HypothesisState,
)

# Core components (v2)
from .kernel import UserKernel
from .observer import InteractionObserver
from .compiler import LogicCompiler, EvolutionReport
from .injector import ContextInjector, InjectionConfig, InjectionResult
from .embeddings import EmbeddingEngine, EmbeddingConfig

# v3 Scoped Components
from .kernel import ScopedKernel
from .compiler import ScopedCompiler, ScopedEvolutionReport
from .cold_storage import ColdStorage, RecompileReport

# Main API
from .iblm import IBLM, IBLMConfig

# Production features
from .exceptions import (
    IBLMError,
    ValidationError,
    SecurityError,
    ResourceLimitError,
    IntegrityError,
    EncryptionError,
    RateLimitError,
)
from .config import (
    IBLMProductionConfig,
    ResourceLimits,
    RateLimitConfig,
    SecurityConfig,
    get_config,
    set_config,
)
from .validators import InputValidator, KernelDataValidator
from .security import (
    encrypt_data,
    decrypt_data,
    rate_limit,
    compute_data_hash,
    sign_data,
    verify_signature,
)

__all__ = [
    # Main API
    "IBLM",
    "IBLMConfig",
    
    # v2 Core components
    "UserKernel",
    "InteractionObserver",
    "LogicCompiler",
    "EvolutionReport",
    "ContextInjector",
    "InjectionConfig",
    "InjectionResult",
    "EmbeddingEngine",
    "EmbeddingConfig",
    
    # v3 Scoped components (BREAKTHROUGH!)
    "ScopedKernel",
    "ScopedCompiler",
    "ScopedEvolutionReport",
    "ColdStorage",
    "RecompileReport",
    
    # v2 Models
    "SignalType",
    "Signal",
    "Rule",
    "RuleCategory",
    "KernelNode",
    "StyleVector",
    "UserProfile",
    "InteractionLog",
    
    # v3 Scoped Models
    "ContextNode",
    "ContextType",
    "ScopedRule",
    "RelationType",
    "Hypothesis",
    "HypothesisState",
    
    # Production configuration
    "IBLMProductionConfig",
    "ResourceLimits",
    "RateLimitConfig",
    "SecurityConfig",
    "get_config",
    "set_config",
    
    # Validation
    "InputValidator",
    "KernelDataValidator",
    
    # Security
    "encrypt_data",
    "decrypt_data",
    "rate_limit",
    "compute_data_hash",
    "sign_data",
    "verify_signature",
    
    # Exceptions
    "IBLMError",
    "ValidationError",
    "SecurityError",
    "ResourceLimitError",
    "IntegrityError",
    "EncryptionError",
    "RateLimitError",
]


def create_brain(config: IBLMConfig = None) -> IBLM:
    """
    Convenience function to create an IBLM brain.
    
    Args:
        config: Optional configuration
        
    Returns:
        New IBLM instance
    """
    return IBLM(config=config)


def create_production_brain() -> IBLM:
    """
    Create a production-ready IBLM brain with all security features enabled.
    
    Returns:
        IBLM instance with production settings
    """
    config = IBLMConfig(
        enable_validation=True,
        enable_thread_safety=True,
        enable_rate_limiting=True,
        auto_evolve=True,
        auto_gc=True,
    )
    return IBLM(config=config)


def create_scoped_brain(cold_storage_path: str = None) -> ScopedKernel:
    """
    Create a v3 Scoped Kernel with full capabilities.
    
    Args:
        cold_storage_path: Optional path for cold storage archive
        
    Returns:
        New ScopedKernel instance
    """
    return ScopedKernel(
        enable_thread_safety=True,
        cold_storage_path=cold_storage_path,
    )

