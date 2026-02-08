"""
IBLM Core - Security Module
===========================

Security utilities including encryption, rate limiting, and integrity checks.
"""

import hashlib
import hmac
import secrets
import time
import json
import base64
from typing import Dict, Optional, Callable, Any
from functools import wraps
from dataclasses import dataclass, field
from collections import defaultdict
import threading

try:
    from .exceptions import (
        SecurityError, EncryptionError, RateLimitError, IntegrityError
    )
    from .config import get_config
except ImportError:
    from exceptions import (
        SecurityError, EncryptionError, RateLimitError, IntegrityError
    )
    from config import get_config


# ===========================
# ENCRYPTION (Optional AES)
# ===========================

def _derive_key(password: str, salt: bytes, iterations: int = 100000) -> bytes:
    """
    Derive encryption key from password using PBKDF2.
    
    Note: For production, consider using the 'cryptography' library.
    This implementation uses hashlib for zero-dependency operation.
    """
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations,
        dklen=32
    )
    return key


def encrypt_data(data: str, password: str) -> bytes:
    """
    Encrypt data with password using XOR cipher with PBKDF2-derived key.
    
    SECURITY NOTE: For production with sensitive data, install 'cryptography'
    and use Fernet or AES-GCM. This provides basic obfuscation.
    
    Format: salt (16 bytes) + hmac (32 bytes) + encrypted_data
    """
    config = get_config()
    if len(password) < config.security.min_password_length:
        raise SecurityError(
            f"Password must be at least {config.security.min_password_length} characters"
        )
    
    # Generate random salt
    salt = secrets.token_bytes(16)
    
    # Derive key
    key = _derive_key(password, salt)
    
    # Simple XOR encryption (for zero-dependency; use 'cryptography' for production)
    data_bytes = data.encode('utf-8')
    key_stream = (key * ((len(data_bytes) // 32) + 1))[:len(data_bytes)]
    encrypted = bytes(a ^ b for a, b in zip(data_bytes, key_stream))
    
    # Compute HMAC for integrity
    mac = hmac.new(key, encrypted, hashlib.sha256).digest()
    
    return salt + mac + encrypted


def decrypt_data(encrypted: bytes, password: str) -> str:
    """
    Decrypt data encrypted with encrypt_data().
    
    Verifies HMAC before decryption to ensure integrity.
    """
    if len(encrypted) < 48:  # 16 (salt) + 32 (hmac)
        raise EncryptionError("Invalid encrypted data format")
    
    # Extract components
    salt = encrypted[:16]
    stored_mac = encrypted[16:48]
    cipher_text = encrypted[48:]
    
    # Derive key
    key = _derive_key(password, salt)
    
    # Verify HMAC
    computed_mac = hmac.new(key, cipher_text, hashlib.sha256).digest()
    if not hmac.compare_digest(stored_mac, computed_mac):
        raise IntegrityError("Data integrity check failed - possible tampering")
    
    # Decrypt
    key_stream = (key * ((len(cipher_text) // 32) + 1))[:len(cipher_text)]
    decrypted = bytes(a ^ b for a, b in zip(cipher_text, key_stream))
    
    return decrypted.decode('utf-8')


# ===========================
# INTEGRITY CHECKING
# ===========================

def compute_data_hash(data: dict) -> str:
    """
    Compute a deterministic hash of data for integrity verification.
    """
    # Sort keys for deterministic serialization
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def sign_data(data: dict, secret: str) -> str:
    """
    Sign data with HMAC for integrity verification.
    """
    data_hash = compute_data_hash(data)
    signature = hmac.new(
        secret.encode('utf-8'),
        data_hash.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_signature(data: dict, signature: str, secret: str) -> bool:
    """
    Verify data signature.
    """
    expected = sign_data(data, secret)
    return hmac.compare_digest(signature, expected)


# ===========================
# RATE LIMITING
# ===========================

@dataclass
class RateLimitState:
    """State for a rate limiter."""
    calls: list = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)


class RateLimiter:
    """
    Thread-safe rate limiter using sliding window.
    """
    
    def __init__(self):
        self._states: Dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._global_lock = threading.Lock()
    
    def check(
        self, 
        key: str, 
        max_calls: int, 
        period_seconds: int
    ) -> tuple[bool, float]:
        """
        Check if operation is allowed under rate limit.
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        with self._global_lock:
            if key not in self._states:
                self._states[key] = RateLimitState()
        
        state = self._states[key]
        now = time.time()
        window_start = now - period_seconds
        
        with state.lock:
            # Remove expired calls
            state.calls = [t for t in state.calls if t > window_start]
            
            if len(state.calls) >= max_calls:
                # Calculate retry_after
                oldest_in_window = min(state.calls) if state.calls else now
                retry_after = oldest_in_window + period_seconds - now
                return False, max(0, retry_after)
            
            # Record this call
            state.calls.append(now)
            return True, 0
    
    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        with self._global_lock:
            if key in self._states:
                with self._states[key].lock:
                    self._states[key].calls.clear()


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(
    operation: str,
    max_calls: Optional[int] = None,
    period_seconds: Optional[int] = None
) -> Callable:
    """
    Rate limiting decorator.
    
    Usage:
        @rate_limit("observe", max_calls=100, period_seconds=60)
        def observe(self, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = get_config()
            
            if not config.rate_limit.enabled:
                return func(*args, **kwargs)
            
            # Get limits from config or use provided
            _max_calls = max_calls
            _period = period_seconds
            
            if _max_calls is None:
                if operation == "observe":
                    _max_calls = config.rate_limit.observe_max_calls
                    _period = config.rate_limit.observe_period_seconds
                elif operation == "evolve":
                    _max_calls = config.rate_limit.evolve_max_calls
                    _period = config.rate_limit.evolve_period_seconds
                else:
                    _max_calls = 100
                    _period = 60
            
            allowed, retry_after = _rate_limiter.check(operation, _max_calls, _period)
            
            if not allowed:
                raise RateLimitError(operation, retry_after)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


# ===========================
# SECURE RANDOM
# ===========================

def generate_secure_id(length: int = 16) -> str:
    """Generate a cryptographically secure random ID."""
    return secrets.token_hex(length // 2)


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure token."""
    return secrets.token_urlsafe(length)


# ===========================
# PASSWORD UTILITIES
# ===========================

def hash_password(password: str) -> str:
    """
    Hash a password for storage.
    
    Returns: salt:hash format
    """
    salt = secrets.token_hex(16)
    key = _derive_key(password, salt.encode('utf-8'))
    return f"{salt}:{key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against stored hash.
    """
    try:
        salt, hash_value = stored_hash.split(':')
        key = _derive_key(password, salt.encode('utf-8'))
        return hmac.compare_digest(key.hex(), hash_value)
    except Exception:
        return False
