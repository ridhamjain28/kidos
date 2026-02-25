#!/usr/bin/env python
"""
IBLM v3.0 - Scientific Memory Verification Tests
=================================================
"""

import sys
import os

iblm_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, iblm_dir)

from models import ScopedRule, RuleState, Signal, SignalType
from kernel import ScopedKernel
from compiler import ScopedCompiler
from injector import generate_system_prompt


def test_rule_lifecycle():
    """Test that rules progress: HYPOTHESIS → SHADOW → VALIDATING → ESTABLISHED."""
    print("Testing rule lifecycle...")
    
    rule = ScopedRule(
        rule_id="test_rule",
        content="Prefers concise code",
        scope_path=["Python"],
        confidence=0.2  # Starts as HYPOTHESIS
    )
    
    assert rule.state == RuleState.HYPOTHESIS
    assert rule.is_hypothesis()
    
    # v4.0 thresholds: HYPOTHESIS < 0.4, SHADOW 0.4-0.6, VALIDATING 0.6-0.8, ESTABLISHED >= 0.8
    rule.validate()  # 0.35 -> HYPOTHESIS
    assert rule.state == RuleState.HYPOTHESIS
    
    rule.validate()  # 0.50 -> SHADOW (v4.0)
    assert rule.state == RuleState.SHADOW
    
    rule.validate()  # 0.65 -> VALIDATING
    assert rule.state == RuleState.VALIDATING
    
    rule.validate()  # 0.80 -> ESTABLISHED
    assert rule.state == RuleState.ESTABLISHED
    assert rule.is_established()
    
    print("  ✓ Rule lifecycle passed")


def test_scope_isolation():
    """Test that different scopes never conflict."""
    print("Testing scope isolation...")
    
    kernel = ScopedKernel(enable_thread_safety=False)
    compiler = ScopedCompiler(kernel)
    
    # Create signals for different scopes
    python_signal = Signal(
        signal_type=SignalType.PREFERENCE,
        content="I prefer async/await in Python",
        confidence=0.8,
        source_hash="h1"
    )
    
    js_signal = Signal(
        signal_type=SignalType.PREFERENCE,
        content="I prefer promises in JavaScript",
        confidence=0.8,
        source_hash="h2"
    )
    
    # Evolve with both signals
    stats = compiler.scientific_evolve([python_signal, js_signal])
    
    # Both should create new rules
    assert stats["rules_created"] == 2
    assert len(kernel.scoped_rules) == 2
    
    # They should have different scopes
    scopes = [r.scope_path for r in kernel.scoped_rules.values()]
    assert ["Python"] in scopes
    assert ["JavaScript"] in scopes
    
    print("  ✓ Scope isolation passed")


def test_scientific_evolve_validation():
    """Test that repeated signals boost confidence."""
    print("Testing scientific_evolve validation...")
    
    kernel = ScopedKernel(enable_thread_safety=False)
    compiler = ScopedCompiler(kernel)
    
    # Same signal repeated
    signal = Signal(
        signal_type=SignalType.PREFERENCE,
        content="I prefer TypeScript",
        confidence=0.8,
        source_hash="h1"
    )
    
    # First time: creates rule
    stats1 = compiler.scientific_evolve([signal])
    assert stats1["rules_created"] == 1
    
    # Second time: validates existing
    stats2 = compiler.scientific_evolve([signal])
    assert stats2["rules_validated"] == 1
    
    # Check rule confidence increased
    rule = list(kernel.scoped_rules.values())[0]
    assert rule.confidence > 0.2  # Should have increased
    
    print("  ✓ Scientific evolve validation passed")


def test_generate_system_prompt():
    """Test that only ESTABLISHED rules are injected."""
    print("Testing generate_system_prompt...")
    
    kernel = ScopedKernel(enable_thread_safety=False)
    
    # Add hypothesis rule
    hypo_rule = ScopedRule(
        rule_id="hypo",
        content="Prefers spaces",
        scope_path=["Python"],
        confidence=0.3,
    )
    kernel.scoped_rules["hypo"] = hypo_rule
    
    # Add established rule
    estab_rule = ScopedRule(
        rule_id="estab",
        content="Uses async/await",
        scope_path=["Python"],
        confidence=0.85,
    )
    estab_rule.state = RuleState.ESTABLISHED
    kernel.scoped_rules["estab"] = estab_rule
    
    # Generate prompt for Python query
    prompt = generate_system_prompt(kernel, "Write a Python function")
    
    # Should include ESTABLISHED rule
    assert "async/await" in prompt
    
    # Should NOT include HYPOTHESIS rule
    assert "spaces" not in prompt
    
    print("  ✓ Generate system prompt passed")


def run_all_tests():
    print("\n" + "="*60)
    print("IBLM v3.0 - Scientific Memory Tests")
    print("="*60 + "\n")
    
    tests = [
        test_rule_lifecycle,
        test_scope_isolation,
        test_scientific_evolve_validation,
        test_generate_system_prompt,
    ]
    
    passed = failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
