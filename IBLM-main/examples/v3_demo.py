#!/usr/bin/env python
"""
IBLM v3 - Cognitive Breakthrough Demo
======================================

This demo showcases the v3 Scoped Probabilistic Kernel:

1. SCOPED RULES - Rules attached to context nodes (no context collapse!)
2. HYPOTHESIS ENGINE - Signals → Hypotheses → Rules (3 validations needed)
3. COLD STORAGE - Archive to disk, recover with recompile_brain()

Run: python examples/v3_demo.py
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
from compiler import ScopedCompiler, ScopedEvolutionReport
from cold_storage import ColdStorage


def print_header(title: str):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f" 🧠 {title}")
    print('='*70)


def demo_scoped_rules():
    """
    DEMO 1: Scoped Rules - No Context Collapse!
    
    In v2, "prefer async" and "prefer promises" would conflict.
    In v3, they are scoped to different contexts.
    """
    print_header("DEMO 1: Scoped Rules - No Context Collapse")
    
    kernel = ScopedKernel()
    
    # Create context nodes for different languages
    python_node = ContextNode(
        node_id="lang_python",
        context_type=ContextType.LANGUAGE,
        name="Python",
        description="Python programming language"
    )
    
    js_node = ContextNode(
        node_id="lang_javascript",
        context_type=ContextType.LANGUAGE,
        name="JavaScript",
        description="JavaScript programming language"
    )
    
    kernel.add_context_node(python_node)
    kernel.add_context_node(js_node)
    
    print(f"✓ Created context nodes: Python, JavaScript")
    
    # Add scoped rules that would conflict in v2
    python_rule = ScopedRule(
        rule_id="rule_async_python",
        source_node="user",
        target_node="lang_python",
        relation=RelationType.PREFERS,
        content="Use async/await for concurrency",
        weight=0.9,
        scope_path=["Python"]
    )
    
    js_rule = ScopedRule(
        rule_id="rule_promises_js",
        source_node="user",
        target_node="lang_javascript",
        relation=RelationType.PREFERS,
        content="Use Promises for async operations",
        weight=0.9,
        scope_path=["JavaScript"]
    )
    
    kernel.add_scoped_rule(python_rule)
    kernel.add_scoped_rule(js_rule)
    
    print(f"✓ Added scoped rules:")
    print(f"   • Python: 'Use async/await for concurrency'")
    print(f"   • JavaScript: 'Use Promises for async operations'")
    
    # Query with Python context
    print(f"\n📜 Query: 'How to handle async?' with context=['Python']")
    python_rules = kernel.query_scoped_rules(["Python"], "async")
    print(f"   Rules returned: {len(python_rules)}")
    for rule in python_rules:
        print(f"   → {rule.content} (scope: {rule.scope_path})")
    
    # Query with JavaScript context
    print(f"\n📜 Query: 'How to handle async?' with context=['JavaScript']")
    js_rules = kernel.query_scoped_rules(["JavaScript"], "async")
    print(f"   Rules returned: {len(js_rules)}")
    for rule in js_rules:
        print(f"   → {rule.content} (scope: {rule.scope_path})")
    
    print(f"\n✨ BREAKTHROUGH: Same query, different contexts, different answers!")
    print(f"   No contradiction - rules are SCOPED!")


def demo_hypothesis_engine():
    """
    DEMO 2: Hypothesis Engine - Validated Learning
    
    In v2, a single signal creates a rule immediately.
    In v3, signals create hypotheses that need 3 validations to become rules.
    """
    print_header("DEMO 2: Hypothesis Engine - Validated Learning")
    
    kernel = ScopedKernel()
    compiler = ScopedCompiler(kernel)
    
    print("New signal detected: 'I prefer using TypeScript'")
    print("In v2: Immediately creates a Rule (might be wrong!)")
    print("In v3: Creates a Hypothesis (needs validation)")
    
    # Create a preference signal
    signal1 = Signal(
        signal_type=SignalType.PREFERENCE,
        content="I prefer using TypeScript for frontend",
        confidence=0.7,
        source_hash="hash_001"
    )
    
    report = compiler.evolve_scoped([signal1])
    print(f"\n📊 Evolution Report:")
    print(f"   Signals processed: {report.signals_processed}")
    print(f"   Hypotheses created: {report.hypotheses_created}")
    print(f"   Rules promoted: {report.rules_promoted}")
    
    # Check hypothesis state
    print(f"\n🔬 Pending hypotheses: {len(kernel.hypotheses)}")
    for h in kernel.hypotheses.values():
        print(f"   • {h.proposed_content[:40]}...")
        print(f"     State: {h.state.name}, Validations: {h.validations}/{h.VALIDATION_THRESHOLD}")
    
    # Simulate 3 validating signals
    print(f"\n🔄 Simulating 3 validation signals...")
    for i in range(3):
        val_signal = Signal(
            signal_type=SignalType.PREFERENCE,
            content="TypeScript is great for frontend type safety",
            confidence=0.8,
            source_hash=f"hash_val_{i}"
        )
        report = compiler.evolve_scoped([val_signal])
        print(f"   Signal {i+1}: +{report.hypotheses_validated} validated, "
              f"+{report.rules_promoted} promoted")
    
    # Check final state
    print(f"\n✅ Final State:")
    print(f"   Scoped Rules: {len(kernel.scoped_rules)}")
    print(f"   Pending Hypotheses: {len(kernel.hypotheses)}")
    
    if kernel.scoped_rules:
        print(f"\n🎉 Hypothesis PROMOTED to Rule:")
        for rule in kernel.scoped_rules.values():
            print(f"   • {rule.content}")
            print(f"     Confidence: {rule.confidence:.1%}, Validations: {rule.source_count}")


def demo_cold_storage():
    """
    DEMO 3: Cold Storage - Archive, Don't Delete!
    
    In v2, garbage collection permanently deletes data.
    In v3, data is archived to disk and can be recovered.
    """
    print_header("DEMO 3: Cold Storage - Archive & Recovery")
    
    archive_path = "demo_archive.jsonl.gz"
    
    # Create kernel with cold storage
    kernel = ScopedKernel(cold_storage_path=archive_path)
    
    print(f"✓ Created kernel with cold storage: {archive_path}")
    
    # Add some rules
    for i, (lang, pattern) in enumerate([
        ("Python", "async/await"),
        ("JavaScript", "promises"), 
        ("Rust", "ownership"),
    ]):
        rule = ScopedRule(
            rule_id=f"rule_{i}",
            source_node="user",
            target_node=f"lang_{lang.lower()}",
            relation=RelationType.PREFERS,
            content=f"Use {pattern} pattern in {lang}",
            weight=0.8,
            scope_path=[lang]
        )
        kernel.add_scoped_rule(rule)
    
    print(f"✓ Added {len(kernel.scoped_rules)} scoped rules")
    
    # Archive a rule
    print(f"\n📦 Archiving a rule to cold storage...")
    rule_to_archive = list(kernel.scoped_rules.values())[0]
    kernel.cold_storage.archive_rule(rule_to_archive, "demo_archive")
    print(f"   Archived: {rule_to_archive.content}")
    
    # Check archive stats
    stats = kernel.cold_storage.get_stats()
    print(f"\n📊 Archive Stats:")
    print(f"   Path: {stats.get('path', archive_path)}")
    print(f"   Total entries: {stats.get('total_entries', 0)}")
    print(f"   Size: {stats.get('size_mb', 0)} MB")
    
    # Simulate corruption recovery
    print(f"\n💥 Simulating kernel corruption...")
    original_count = len(kernel.scoped_rules)
    kernel.scoped_rules.clear()
    print(f"   Rules before: {original_count}")
    print(f"   Rules after corruption: {len(kernel.scoped_rules)}")
    
    print(f"\n🔧 Recovery would use: kernel.recompile_brain()")
    print(f"   (Skipping actual recovery in demo to avoid side effects)")
    
    # Cleanup
    if os.path.exists(archive_path):
        os.remove(archive_path)
        print(f"\n🗑️  Cleaned up demo archive")


def demo_full_workflow():
    """
    DEMO 4: Full v3 Workflow
    
    End-to-end demonstration of the cognitive breakthrough.
    """
    print_header("DEMO 4: Full v3 Workflow")
    
    # Create v3 kernel
    kernel = ScopedKernel()
    compiler = ScopedCompiler(kernel)
    
    print("Simulating user session with scoped learning...")
    
    # User works on Python project
    print("\n📍 User context: Python + FastAPI project")
    
    signals = [
        Signal(SignalType.PREFERENCE, "I prefer async/await in Python", 0.8, "h1"),
        Signal(SignalType.EXPERTISE, "I'm an expert in FastAPI", 0.9, "h2"),
        Signal(SignalType.WORKFLOW, "Always use type hints", 0.7, "h3"),
    ]
    
    for signal in signals:
        report = compiler.evolve_scoped([signal])
        print(f"   Signal: '{signal.content[:35]}...'")
        print(f"   → Hypothesis created: {report.hypotheses_created > 0}")
    
    # User switches to JavaScript
    print("\n📍 User context: JavaScript + React project")
    
    js_signals = [
        Signal(SignalType.PREFERENCE, "Use promises in JavaScript", 0.8, "h4"),
        Signal(SignalType.WORKFLOW, "React hooks for state", 0.75, "h5"),
    ]
    
    for signal in js_signals:
        report = compiler.evolve_scoped([signal])
        print(f"   Signal: '{signal.content[:35]}...'")
        print(f"   → Hypothesis created: {report.hypotheses_created > 0}")
    
    # Query by context
    print("\n📜 Querying rules by context:")
    
    print("\n   Context: ['Python']")
    py_rules = kernel.query_scoped_rules(["Python"])
    print(f"   Rules: {len(py_rules)}")
    
    print("\n   Context: ['JavaScript']")
    js_rules = kernel.query_scoped_rules(["JavaScript"])
    print(f"   Rules: {len(js_rules)}")
    
    # Show stats
    print(f"\n📊 Kernel Statistics:")
    stats = kernel.get_stats()
    print(f"   Context Nodes: {stats['context_nodes']}")
    print(f"   Scoped Rules: {stats['scoped_rules']}")
    print(f"   Pending Hypotheses: {stats['hypotheses_pending']}")
    print(f"   Metrics: {stats['metrics']}")


def main():
    print("\n" + "🧠 "*20)
    print("IBLM v3 - COGNITIVE BREAKTHROUGH DEMO")
    print("🧠 "*20)
    
    demo_scoped_rules()
    demo_hypothesis_engine()
    demo_cold_storage()
    demo_full_workflow()
    
    print_header("IBLM v3 - Summary")
    print("""
🎯 KEY BREAKTHROUGHS:

1. SCOPED RULES
   • Rules attached to ContextNodes (Python, JS, etc.)
   • "prefer async" in Python ≠ "prefer promises" in JavaScript
   • Query by context → no contradictions!

2. HYPOTHESIS ENGINE  
   • Signals create Hypotheses (confidence: 0.1)
   • 3 validations → Promoted to Rule (confidence: 0.8)
   • 2 rejections → Deleted
   • Much more accurate learning!

3. COLD STORAGE
   • Archive to disk, don't delete
   • Full recovery with recompile_brain()
   • Never lose learned knowledge!

🚀 IBLM v3 is truly a COGNITIVE BREAKTHROUGH.
""")


if __name__ == "__main__":
    main()
