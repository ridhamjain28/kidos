#!/usr/bin/env python
"""
IBLM Core - Production Features Demo
=====================================

This example demonstrates the production-ready features:
1. Input validation and sanitization
2. Thread-safe operations
3. Resource limits
4. Encrypted save/load
5. Health checks
6. Context manager usage
"""

import sys
import os
import threading
import time

# Add IBLM directory to path
iblm_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, iblm_dir)

from iblm import IBLM, IBLMConfig


def print_header(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


def demo_context_manager():
    """Demonstrate context manager usage."""
    print_header("Context Manager Usage")
    
    with IBLM() as brain:
        brain.teach("Always use async/await in Python")
        print(f"✓ Brain ID: {brain.id}")
        print(f"✓ Rules: {len(brain.kernel.rules)}")
    
    print("✓ Brain automatically cleaned up on exit")


def demo_input_validation():
    """Demonstrate input validation."""
    print_header("Input Validation")
    
    config = IBLMConfig(enable_validation=True)
    brain = IBLM(config)
    
    # Normal input
    result = brain.observe(
        "I prefer using TypeScript for frontend",
        "Got it! I'll use TypeScript for your frontend code."
    )
    print(f"✓ Normal input: {result['status']}")
    
    # Test with potentially dangerous input (will be sanitized)
    dangerous_input = "Use this <script>alert('xss')</script> code"
    result = brain.observe(
        dangerous_input,
        "I'll help with that code."
    )
    print(f"✓ Sanitized input: {result['status']}")
    print(f"  Validation errors caught: {brain._validation_errors}")


def demo_health_check():
    """Demonstrate health check."""
    print_header("Health Check")
    
    brain = IBLM()
    brain.teach("I'm a Python expert")
    brain.teach("I prefer FastAPI for APIs")
    
    health = brain.health_check()
    print(f"Status: {health['status']}")
    print(f"Brain ID: {health['id']}")
    print(f"Rules: {health['rules_count']}")
    print(f"Profile Confidence: {health['profile_confidence']:.1%}")
    print(f"Kernel Metrics: {health['kernel_metrics']}")


def demo_encrypted_save():
    """Demonstrate encrypted save/load."""
    print_header("Encrypted Save/Load")
    
    brain = IBLM()
    brain.teach("I work on financial applications")
    brain.teach("Security is my top priority")
    
    encrypted_path = "secure_brain.iblm.enc"
    password = "my_secure_password_123"
    
    # Save encrypted
    brain.save_encrypted(encrypted_path, password)
    print(f"✓ Saved encrypted brain to: {encrypted_path}")
    
    # Check file size
    file_size = os.path.getsize(encrypted_path)
    print(f"  File size: {file_size} bytes (encrypted)")
    
    # Load encrypted
    loaded_brain = IBLM.load_encrypted(encrypted_path, password)
    print(f"✓ Loaded encrypted brain: {loaded_brain.id}")
    print(f"  Rules preserved: {len(loaded_brain.kernel.rules)}")
    
    # Try wrong password
    try:
        IBLM.load_encrypted(encrypted_path, "wrong_password")
    except Exception as e:
        print(f"✓ Wrong password correctly rejected: {type(e).__name__}")
    
    # Cleanup
    os.remove(encrypted_path)
    print(f"✓ Cleaned up encrypted file")


def demo_resource_limits():
    """Demonstrate resource limits."""
    print_header("Resource Limits")
    
    # Create brain with strict limits
    config = IBLMConfig(
        max_rules=5,
        max_nodes=3,
    )
    brain = IBLM(config)
    
    print(f"Max rules limit: {config.max_rules}")
    print(f"Max nodes limit: {config.max_nodes}")
    
    # Add rules up to limit
    for i in range(6):
        try:
            brain.teach(f"Rule number {i+1}")
            print(f"  Rule {i+1}: ✓ Added")
        except Exception as e:
            print(f"  Rule {i+1}: ✗ Blocked ({type(e).__name__})")


def demo_thread_safety():
    """Demonstrate thread-safe operations."""
    print_header("Thread Safety")
    
    brain = IBLM(IBLMConfig(enable_thread_safety=True))
    errors = []
    
    def worker(worker_id: int):
        try:
            for i in range(10):
                brain.observe(
                    f"Worker {worker_id} message {i}",
                    f"Response to worker {worker_id}"
                )
        except Exception as e:
            errors.append(e)
    
    # Create multiple threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    if not errors:
        print(f"✓ 5 threads completed {5 * 10} operations safely")
        print(f"  Total observations: {brain._total_observations}")
    else:
        print(f"✗ Errors occurred: {errors}")


def demo_production_config():
    """Demonstrate production configuration."""
    print_header("Production Configuration")
    
    # Create production-ready config
    config = IBLMConfig(
        enable_validation=True,
        enable_thread_safety=True,
        enable_rate_limiting=True,
        auto_evolve=True,
        auto_gc=True,
    )
    brain = IBLM(config)
    
    print("Production brain features:")
    print(f"  Validation: {brain.config.enable_validation}")
    print(f"  Thread Safety: {brain.config.enable_thread_safety}")
    print(f"  Rate Limiting: {brain.config.enable_rate_limiting}")
    print(f"  Auto Evolve: {brain.config.auto_evolve}")
    print(f"  Auto GC: {brain.config.auto_gc}")


def main():
    print("\n" + "🔒 "*20)
    print("IBLM Core - Production Features Demo")
    print("🔒 "*20)
    
    demo_context_manager()
    demo_input_validation()
    demo_health_check()
    demo_encrypted_save()
    demo_resource_limits()
    demo_thread_safety()
    demo_production_config()
    
    print_header("Demo Complete!")
    print("""
Key Production Features:
1. ✓ Context manager for automatic cleanup
2. ✓ Input validation and XSS prevention
3. ✓ Health checks for monitoring
4. ✓ Encrypted brain persistence
5. ✓ Resource limits to prevent DoS
6. ✓ Thread-safe operations
7. ✓ Production-ready configuration
""")


if __name__ == "__main__":
    main()
