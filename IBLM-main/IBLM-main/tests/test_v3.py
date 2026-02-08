#!/usr/bin/env python
"""
IBLM v3 - Quick Verification Tests
===================================

Tests for the Scoped Probabilistic Kernel.
"""

import sys
import os

# Add IBLM directory to path
iblm_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, iblm_dir)

from models import (
    ContextNode, ContextType, ScopedRule, RelationType,
    Hypothesis, HypothesisState, Signal, SignalType
)
from kernel import ScopedKernel
from compiler import ScopedCompiler


def test_scoped_rules_no_conflict():
    """Test that scoped rules don't conflict across contexts."""
    print("Testing scoped rules (no conflict)...")
    
    kernel = ScopedKernel(enable_thread_safety=False)
    
    # Add rules for different contexts
    python_rule = ScopedRule(
        rule_id="rule_python",
        source_node="user",
        target_node="lang_python",
        relation=RelationType.PREFERS,
        content="Use async/await",
        weight=0.9,
        scope_path=["Python"]
    )
    
    js_rule = ScopedRule(
        rule_id="rule_js",
        source_node="user",
        target_node="lang_js",
        relation=RelationType.PREFERS,
        content="Use promises",
        weight=0.9,
        scope_path=["JavaScript"]
    )
    
    kernel.add_scoped_rule(python_rule)
    kernel.add_scoped_rule(js_rule)
    
    # Query Python context
    py_rules = kernel.query_scoped_rules(["Python"])
    assert len(py_rules) == 1
    assert "async" in py_rules[0].content
    
    # Query JavaScript context
    js_rules = kernel.query_scoped_rules(["JavaScript"])
    assert len(js_rules) == 1
    assert "promises" in js_rules[0].content
    
    # Rules don't leak across contexts
    assert "promises" not in py_rules[0].content
    assert "async" not in js_rules[0].content
    
    print("  ✓ Scoped rules passed")


def test_hypothesis_creation():
    """Test that signals create hypotheses, not rules."""
    print("Testing hypothesis creation...")
    
    kernel = ScopedKernel(enable_thread_safety=False)
    compiler = ScopedCompiler(kernel)
    
    # Create a signal
    signal = Signal(
        signal_type=SignalType.PREFERENCE,
        content="I prefer Python for backend",
        confidence=0.8,
        source_hash="test_hash"
    )
    
    # Evolve
    report = compiler.evolve_scoped([signal])
    
    # Should create hypothesis, not rule
    assert report.hypotheses_created >= 1
    assert len(kernel.scoped_rules) == 0  # No rules yet
    assert len(kernel.hypotheses) >= 1    # Hypothesis created
    
    print("  ✓ Hypothesis creation passed")


def test_hypothesis_promotion():
    """Test that hypotheses are promoted after 3 validations."""
    print("Testing hypothesis promotion...")
    
    kernel = ScopedKernel(enable_thread_safety=False)
    
    # Create a hypothesis manually
    hypothesis = Hypothesis(
        hypothesis_id="hyp_test",
        proposed_content="Use TypeScript",
        proposed_scope_path=["JavaScript"],
        proposed_relation=RelationType.PREFERS,
        proposed_target_node="lang_js",
        confidence=0.1,
        validations=0
    )
    
    # Validate 3 times
    assert not hypothesis.validate()  # 1st
    assert not hypothesis.validate()  # 2nd
    assert hypothesis.validate()      # 3rd - should promote
    
    assert hypothesis.state == HypothesisState.PROMOTED
    
    # Convert to rule
    rule = hypothesis.to_scoped_rule()
    assert rule.confidence == 0.8
    assert "TypeScript" in rule.content
    
    print("  ✓ Hypothesis promotion passed")


def test_hypothesis_rejection():
    """Test that hypotheses are rejected after 2 contradictions."""
    print("Testing hypothesis rejection...")
    
    hypothesis = Hypothesis(
        hypothesis_id="hyp_reject",
        proposed_content="Use PHP",
        proposed_scope_path=["Web"],
        proposed_relation=RelationType.PREFERS,
        proposed_target_node="domain_web",
        confidence=0.1,
        rejections=0
    )
    
    assert not hypothesis.reject()  # 1st rejection
    assert hypothesis.reject()      # 2nd rejection - should reject
    
    assert hypothesis.state == HypothesisState.REJECTED
    
    print("  ✓ Hypothesis rejection passed")


def test_context_nodes():
    """Test context node management."""
    print("Testing context nodes...")
    
    kernel = ScopedKernel(enable_thread_safety=False)
    
    # Create node
    node = ContextNode(
        node_id="lang_python",
        context_type=ContextType.LANGUAGE,
        name="Python",
        description="Python programming"
    )
    
    kernel.add_context_node(node)
    
    # Retrieve
    retrieved = kernel.get_context_node("lang_python")
    assert retrieved is not None
    assert retrieved.name == "Python"
    
    # Find by name
    found = kernel.find_context_by_name("python")  # Case insensitive
    assert found is not None
    
    print("  ✓ Context nodes passed")


def test_kernel_export_import():
    """Test ScopedKernel export/import."""
    print("Testing kernel export/import...")
    
    kernel = ScopedKernel(enable_thread_safety=False)
    
    # Add data
    node = ContextNode(
        node_id="test_node",
        context_type=ContextType.PROJECT,
        name="TestProject"
    )
    kernel.add_context_node(node)
    
    rule = ScopedRule(
        rule_id="test_rule",
        source_node="user",
        target_node="test_node",
        relation=RelationType.USES,
        content="Test content",
        scope_path=["Test"]
    )
    kernel.add_scoped_rule(rule)
    
    # Export
    data = kernel.export()
    assert data["version"] == "3.0.0"
    
    # Import
    kernel2 = ScopedKernel.load(data)
    
    assert len(kernel2.context_nodes) == 1
    assert len(kernel2.scoped_rules) == 1
    assert kernel2.scoped_rules["test_rule"].content == "Test content"
    
    print("  ✓ Kernel export/import passed")


def test_scoped_compiler():
    """Test the ScopedCompiler evolve_scoped algorithm."""
    print("Testing ScopedCompiler...")
    
    kernel = ScopedKernel(enable_thread_safety=False)
    compiler = ScopedCompiler(kernel)
    
    # Multiple signals
    signals = [
        Signal(SignalType.PREFERENCE, "I like Python", 0.7, "h1"),
        Signal(SignalType.EXPERTISE, "Expert in FastAPI", 0.8, "h2"),
    ]
    
    report = compiler.evolve_scoped(signals)
    
    assert report.signals_processed == 2
    assert report.hypotheses_created >= 1
    assert report.context_nodes_created >= 0  # May or may not create nodes
    
    print("  ✓ ScopedCompiler passed")


def run_all_tests():
    """Run all v3 tests."""
    print("\n" + "="*60)
    print("IBLM v3 - Scoped Kernel Tests")
    print("="*60 + "\n")
    
    tests = [
        test_scoped_rules_no_conflict,
        test_hypothesis_creation,
        test_hypothesis_promotion,
        test_hypothesis_rejection,
        test_context_nodes,
        test_kernel_export_import,
        test_scoped_compiler,
    ]
    
    passed = 0
    failed = 0
    
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
