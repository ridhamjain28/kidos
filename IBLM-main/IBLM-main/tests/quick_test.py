#!/usr/bin/env python
"""
IBLM Core - Quick Verification Tests
====================================

Simple tests that don't require pytest.
"""

import sys
import os
import tempfile
import json

# Add IBLM directory to path
iblm_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, iblm_dir)

from iblm import IBLM, IBLMConfig


def test_basic_operations():
    """Test basic IBLM operations."""
    print("Testing basic operations...")
    
    brain = IBLM()
    assert brain is not None
    
    # Test teach
    rule_id = brain.teach("I'm a Python expert")
    assert rule_id is not None
    
    # Test observe
    result = brain.observe(
        "Write me a function to sort a list",
        "Here's a Python function..."
    )
    assert result["status"] == "observed"
    
    # Test inject
    injection = brain.inject("How do I add error handling?")
    assert injection.system_header != ""
    
    print("  ✓ Basic operations passed")


def test_context_manager():
    """Test context manager."""
    print("Testing context manager...")
    
    with IBLM() as brain:
        brain.teach("Use TypeScript")
        assert len(brain.kernel.rules) >= 1
    
    print("  ✓ Context manager passed")


def test_save_load():
    """Test save and load."""
    print("Testing save/load...")
    
    brain = IBLM()
    brain.teach("Always use async/await")
    brain.set_project("TestProject", "Test description")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.json.gz', delete=False) as f:
        path = f.name
    
    try:
        brain.save(path)
        
        # Load
        loaded = IBLM.load(path)
        assert len(loaded.kernel.rules) >= 1
        assert loaded.kernel.active_project == "TestProject"
        
        print("  ✓ Save/load passed")
    finally:
        os.unlink(path)


def test_encrypted_save_load():
    """Test encrypted save and load."""
    print("Testing encrypted save/load...")
    
    brain = IBLM()
    brain.teach("Security is important")
    
    path = "test_encrypted.iblm.enc"
    password = "test_password_123"
    
    try:
        brain.save_encrypted(path, password)
        
        # Load with correct password
        loaded = IBLM.load_encrypted(path, password)
        assert len(loaded.kernel.rules) >= 1
        
        # Try wrong password
        try:
            IBLM.load_encrypted(path, "wrong_password")
            assert False, "Should have raised IntegrityError"
        except Exception as e:
            assert "integrity" in str(e).lower() or "IntegrityError" in str(type(e).__name__)
        
        print("  ✓ Encrypted save/load passed")
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_input_validation():
    """Test input validation."""
    print("Testing input validation...")
    
    config = IBLMConfig(enable_validation=True)
    brain = IBLM(config)
    
    # Normal input
    result = brain.observe("Hello", "Hi there!")
    assert result["status"] == "observed"
    
    # Input with HTML (should be sanitized)
    result = brain.observe(
        "<script>alert('xss')</script>",
        "Sanitized!"
    )
    assert result["status"] in ["observed", "skipped"]
    
    print("  ✓ Input validation passed")


def test_health_check():
    """Test health check."""
    print("Testing health check...")
    
    brain = IBLM()
    brain.teach("Test rule")
    
    health = brain.health_check()
    
    assert health["status"] == "healthy"
    assert health["rules_count"] >= 1
    assert "kernel_metrics" in health
    
    print("  ✓ Health check passed")


def test_thread_safety():
    """Test thread safety."""
    print("Testing thread safety...")
    
    import threading
    
    config = IBLMConfig(enable_thread_safety=True)
    brain = IBLM(config)
    
    errors = []
    
    def worker(worker_id):
        try:
            for i in range(5):
                brain.observe(
                    f"Worker {worker_id} msg {i}",
                    f"Response {i}"
                )
        except Exception as e:
            errors.append(e)
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert len(errors) == 0, f"Thread errors: {errors}"
    
    print("  ✓ Thread safety passed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("IBLM Core - Quick Verification Tests")
    print("="*60 + "\n")
    
    tests = [
        test_basic_operations,
        test_context_manager,
        test_save_load,
        test_encrypted_save_load,
        test_input_validation,
        test_health_check,
        test_thread_safety,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__} FAILED: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
