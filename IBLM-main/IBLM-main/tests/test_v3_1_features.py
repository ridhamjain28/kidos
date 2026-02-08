#!/usr/bin/env python
"""
IBLM v3.1 - Socratic & Optimization Tests
=========================================
"""

import sys
import os

iblm_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, iblm_dir)

from models import ScopedRule, RuleState, Signal, SignalType, CollaborationRequest
from kernel import ScopedKernel
from compiler import ScopedCompiler
from validators import TerminalFilter

def test_socratic_conflict_resolution():
    """Test that contradictions of ESTABLISHED rules trigger CollaborationRequest."""
    print("Testing Socratic Conflict Resolution...")
    
    kernel = ScopedKernel(enable_thread_safety=False)
    compiler = ScopedCompiler(kernel)
    
    # 1. Establish a rule
    rule = ScopedRule(
        rule_id="established_rule",
        content="Prefers Python for backend",
        scope_path=["Backend"],
        confidence=0.9,
        state=RuleState.ESTABLISHED
    )
    # Manually adding rule to kernel
    kernel.scoped_rules["established_rule"] = rule
    
    # 2. Simulate new conflicting signal
    # "Prefers Node.js for backend"
    signal = Signal(
        signal_type=SignalType.PREFERENCE,
        content="Prefers Node.js for backend",
        confidence=0.8,
        source_hash="h_new"
    )
    
    # Hack: Force embedding match to ensure _find_rule_in_scope returns the rule
    # In production, embeddings would be similar (same topic), but content different.
    signal_embedding = compiler.embedding_engine.embed(signal.content)
    rule.embedding = signal_embedding 
    
    # 3. Evolve
    stats = compiler.scientific_evolve([signal])
    
    # 4. Assert Request Generated
    requests = stats.get("collaboration_requests", [])
    
    if not requests:
        print("  ! No requests found. Stats:", stats)
        # Debugging info
        detected_scope, _ = compiler._detect_scope(signal)
        print("  Detected scope:", detected_scope)
        print("  Rule scope:", rule.scope_path)
        found = compiler._find_rule_in_scope(signal.content, detected_scope)
        print("  Found rule:", found)
        
    assert len(requests) == 1, "Should have generated 1 collaboration request"
    
    req = requests[0]
    assert isinstance(req, CollaborationRequest)
    assert req.conflicting_rule.rule_id == rule.rule_id
    assert "differs from established rule" in req.reason
    
    print("  ✓ Socratic Conflict Resolution passed")

def test_terminal_filter():
    """Test filtering of CLI noise."""
    print("Testing TerminalFilter...")
    
    clean_lines = [
        "User: How do I init?",
        "AI: git init"
    ]
    
    noisy_lines = [
        "ls -la",
        "drwxr-xr-x 2 user user 4096 Jan 1 12:00 .",
        "npm install",
        "[=================] 100/100",
        "downloading...",
        "User: How do I init?",
        "AI: git init",
        "cd /tmp",
         ""
    ]
    
    text = "\n".join(noisy_lines)
    filtered = TerminalFilter.filter_cli_output(text)
    
    # Should keep the conversation parts
    assert "User: How do I init?" in filtered
    assert "AI: git init" in filtered
    
    # Should remove noise
    assert "ls -la" not in filtered
    assert "npm install" not in filtered
    assert "downloading" not in filtered
    
    print("  ✓ TerminalFilter passed")

def run_tests():
    try:
        test_socratic_conflict_resolution()
        test_terminal_filter()
        print("\nAll v3.1 tests passed!")
        return True
    except Exception as e:
        print(f"\nFailed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if not run_tests():
        sys.exit(1)
