"""
IBLM Core - Input Validators
============================

Input validation and sanitization for security.
"""

import re
import html
from typing import Optional, List, Tuple
from dataclasses import dataclass

try:
    from .exceptions import ValidationError
    from .config import get_config
except ImportError:
    from exceptions import ValidationError
    from config import get_config


# Dangerous patterns that could indicate injection attempts
INJECTION_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # Script tags
    r'javascript:',                 # JavaScript protocol
    r'on\w+\s*=',                   # Event handlers
    r'\{\{.*?\}\}',                # Template injection
    r'\$\{.*?\}',                  # Template literals
    r'__proto__',                  # Prototype pollution
    r'constructor\s*\(',           # Constructor access
]

# Compiled patterns for efficiency
_INJECTION_REGEXES = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in INJECTION_PATTERNS]


@dataclass
class ValidationResult:
    """Result of validation operation."""
    valid: bool
    sanitized_value: str
    warnings: List[str]
    errors: List[str]


class InputValidator:
    """
    Validates and sanitizes user inputs.
    
    SECURITY: Prevents injection attacks and ensures data integrity.
    """
    
    @classmethod
    def validate_user_input(
        cls, 
        text: str, 
        max_length: Optional[int] = None,
        allow_html: bool = False,
        strict: bool = True
    ) -> ValidationResult:
        """
        Validate and sanitize user input text.
        
        Args:
            text: The input text to validate
            max_length: Maximum allowed length (None = use config)
            allow_html: Whether to allow HTML (default: False)
            strict: Raise exception on validation failure
            
        Returns:
            ValidationResult with sanitized value
        """
        config = get_config()
        max_len = max_length or config.limits.max_user_input_length
        
        warnings = []
        errors = []
        sanitized = text
        
        # Check for None/empty
        if text is None:
            if strict:
                raise ValidationError("Input cannot be None")
            return ValidationResult(False, "", [], ["Input cannot be None"])
        
        # Length check
        if len(text) > max_len:
            if strict:
                raise ValidationError(f"Input exceeds maximum length ({len(text)} > {max_len})")
            sanitized = text[:max_len]
            warnings.append(f"Input truncated from {len(text)} to {max_len} characters")
        
        # HTML escaping
        if not allow_html:
            escaped = html.escape(sanitized)
            if escaped != sanitized:
                warnings.append("HTML entities were escaped")
                sanitized = escaped
        
        # Injection pattern detection
        for pattern in _INJECTION_REGEXES:
            if pattern.search(sanitized):
                if strict:
                    raise ValidationError("Potential injection attack detected")
                sanitized = pattern.sub("[FILTERED]", sanitized)
                warnings.append("Potentially dangerous pattern was filtered")
        
        # Null byte removal
        if '\x00' in sanitized:
            sanitized = sanitized.replace('\x00', '')
            warnings.append("Null bytes were removed")
        
        valid = len(errors) == 0
        return ValidationResult(valid, sanitized, warnings, errors)
    
    @classmethod
    def validate_rule_content(
        cls,
        condition: str,
        action: str,
        strict: bool = True
    ) -> Tuple[str, str]:
        """
        Validate rule condition and action.
        
        Returns:
            Tuple of (sanitized_condition, sanitized_action)
        """
        config = get_config()
        max_len = config.limits.max_rule_content_length
        
        # Validate condition
        cond_result = cls.validate_user_input(
            condition, 
            max_length=max_len,
            strict=strict
        )
        
        # Validate action
        action_result = cls.validate_user_input(
            action,
            max_length=max_len,
            strict=strict
        )
        
        return cond_result.sanitized_value, action_result.sanitized_value
    
    @classmethod
    def validate_node_content(
        cls,
        name: str,
        context: str,
        strict: bool = True
    ) -> Tuple[str, str]:
        """
        Validate node name and context.
        
        Returns:
            Tuple of (sanitized_name, sanitized_context)
        """
        config = get_config()
        
        # Name: shorter limit
        name_result = cls.validate_user_input(
            name,
            max_length=200,
            strict=strict
        )
        
        # Context: longer limit
        context_result = cls.validate_user_input(
            context,
            max_length=config.limits.max_node_context_length,
            strict=strict
        )
        
        return name_result.sanitized_value, context_result.sanitized_value
    
    @classmethod
    def validate_weight(cls, weight: float, strict: bool = True) -> float:
        """
        Validate and clamp weight to valid range [0.0, 1.0].
        """
        if weight < 0.0:
            if strict:
                raise ValidationError(f"Weight cannot be negative: {weight}")
            return 0.0
        if weight > 1.0:
            if strict:
                raise ValidationError(f"Weight cannot exceed 1.0: {weight}")
            return 1.0
        return weight
    
    @classmethod
    def validate_confidence(cls, confidence: float, strict: bool = True) -> float:
        """Validate confidence score (same as weight)."""
        return cls.validate_weight(confidence, strict)


class KernelDataValidator:
    """
    Validates kernel data for integrity.
    """
    
    REQUIRED_EXPORT_FIELDS = ["version", "kernel"]
    REQUIRED_KERNEL_FIELDS = ["rules", "nodes", "profile", "style_vector"]
    
    @classmethod
    def validate_export_data(cls, data: dict) -> ValidationResult:
        """
        Validate exported kernel data structure.
        """
        errors = []
        warnings = []
        
        # Check required top-level fields
        for field in cls.REQUIRED_EXPORT_FIELDS:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return ValidationResult(False, str(data), warnings, errors)
        
        # Check kernel structure
        kernel_data = data.get("kernel", {})
        for field in cls.REQUIRED_KERNEL_FIELDS:
            if field not in kernel_data:
                errors.append(f"Missing kernel field: {field}")
        
        # Validate version format
        version = data.get("version", "")
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            warnings.append(f"Invalid version format: {version}")
        
        # Validate rules
        rules = kernel_data.get("rules", {})
        if not isinstance(rules, dict):
            errors.append("Rules must be a dictionary")
        
        # Validate nodes
        nodes = kernel_data.get("nodes", {})
        if not isinstance(nodes, dict):
            errors.append("Nodes must be a dictionary")
        
        valid = len(errors) == 0
        return ValidationResult(valid, str(data), warnings, errors)
    
    @classmethod
    def validate_rule_data(cls, data: dict) -> bool:
        """Validate individual rule data structure."""
        required = ["rule_id", "category", "condition", "action", "weight"]
        return all(field in data for field in required)
    
    @classmethod
    def validate_node_data(cls, data: dict) -> bool:
        """Validate individual node data structure."""
        required = ["node_id", "node_type", "name"]
        return all(field in data for field in required)


def sanitize_for_logging(text: str, max_length: int = 200) -> str:
    """
    Sanitize text for safe logging (no PII leakage).
    """
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    # Remove potential sensitive patterns
    # Email addresses
    text = re.sub(r'\b[\w.-]+@[\w.-]+\.\w+\b', '[EMAIL]', text)
    # Phone numbers
    text = re.sub(r'\b\d{10,}\b', '[PHONE]', text)
    # API keys (common patterns)
    text = re.sub(r'\b[A-Za-z0-9]{32,}\b', '[API_KEY]', text)
    

class TerminalFilter:
    """
    v3.1 IDE EXTENSION SUPPORT: Filter irrelevant terminal noise.
    
    Filters out common shell commands, progress bars, and transient output
    that shouldn't be learned as "behavior".
    """
    
    NOISE_PATTERNS = [
        r'^(ls|cd|pwd|dir|echo|cat|mkdir|rm|cp|mv|npm|git|pip|node|python)\b',  # Basic shell commands
        r'^\s*$',                                       # Empty lines
        r'^[\.\/]+\w+',                                 # Path traversals
        r'.*(\[=*\]|\d+%).*',                           # Progress bars [====] or 50%
        r'.*(downloading|installing|fetching).*',       # Transient states
        r'^[\|\/\-\\]\s*$',                             # Spinners
        r'^doi:.*',                                     # Metadata noise
        r'.*node_modules.*',                            # Dependency paths
        r'.*__pycache__.*',                             # Cache paths
    ]
    
    COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in NOISE_PATTERNS]
    
    @classmethod
    def is_noise(cls, text: str) -> bool:
        """Check if text is terminal noise."""
        text = text.strip()
        if len(text) < 2: # Too short
            return True
            
        for pattern in cls.COMPILED_PATTERNS:
            if pattern.search(text):
                return True
        return False
        
    @classmethod
    def filter_cli_output(cls, text: str) -> str:
        """Filter out noise lines from CLI output."""
        lines = text.split('\n')
        filtered = [line for line in lines if not cls.is_noise(line)]
        return '\n'.join(filtered)
