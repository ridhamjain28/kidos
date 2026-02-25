"""
IBLM Core - Custom Exceptions
=============================

Custom exception hierarchy for robust error handling.
"""


class IBLMError(Exception):
    """Base exception for all IBLM errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(IBLMError):
    """Raised when input validation fails."""
    pass


class SecurityError(IBLMError):
    """Raised for security-related issues."""
    pass


class ResourceLimitError(IBLMError):
    """Raised when a resource limit is exceeded."""
    
    def __init__(self, resource: str, current: int, limit: int):
        message = f"Resource limit exceeded: {resource} ({current}/{limit})"
        super().__init__(message, {"resource": resource, "current": current, "limit": limit})
        self.resource = resource
        self.current = current
        self.limit = limit


class IntegrityError(IBLMError):
    """Raised when data integrity check fails."""
    pass


class EncryptionError(SecurityError):
    """Raised for encryption/decryption failures."""
    pass


class RateLimitError(IBLMError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, operation: str, retry_after: float):
        message = f"Rate limit exceeded for {operation}. Retry after {retry_after:.1f}s"
        super().__init__(message, {"operation": operation, "retry_after": retry_after})
        self.operation = operation
        self.retry_after = retry_after


class KernelCorruptedError(IntegrityError):
    """Raised when kernel data is corrupted."""
    pass


class VersionMismatchError(IBLMError):
    """Raised when trying to load incompatible kernel version."""
    
    def __init__(self, expected: str, found: str):
        message = f"Version mismatch: expected {expected}, found {found}"
        super().__init__(message, {"expected": expected, "found": found})
        self.expected = expected
        self.found = found
