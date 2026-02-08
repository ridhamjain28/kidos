#!/usr/bin/env python
"""
IBLM v3.1 - Goal-Constrained Kernel Tests
==========================================
"""

import sys
import os

iblm_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, iblm_dir)

from models import UserGoal, UserFact, ScopedRule, RuleState
from kernel import ScopedKernel
from observer import UnifiedObserver, StreamType
from injector import generate_system_prompt


def test_goal_fact_hierarchy():
    """Test that Goals override Facts."""
    print("Testing Goal/Fact Hierarchy...")
    
    kernel = ScopedKernel(enable_thread_safety=False)
    
    # Add a Goal (High Priority)
    goal = UserGoal(
        goal_id="goal_1",
        content="Write clean, maintainable code",
        scope_path=["Coding"],
        priority=10
    )
    kernel.add_goal(goal)
    
    # Add a Fact (Low Priority)
    fact = UserFact(
        fact_id="fact_1",
        content="User types fast",
        scope_path=["Coding"],
        priority=5
    )
    kernel.add_fact(fact)
    
    # Verify Goals are retrieved
    goals = kernel.get_active_goals(["Coding"])
    assert len(goals) == 1
    assert goals[0].priority == 10
    
    # Verify Facts are retrieved (not conflicting)
    facts = kernel.get_facts_not_conflicting(["Coding"])
    assert len(facts) == 1
    
    print("  ✓ Goal/Fact Hierarchy passed")


def test_unified_observer():
    """Test the UnifiedObserver with multiple streams."""
    print("Testing UnifiedObserver...")
    
    observer = UnifiedObserver()
    
    # Browser stream
    browser_result = observer.observe_browser("Use Python", "Here's Python code")
    assert all(s.metadata.get("stream") == StreamType.BROWSER for s in browser_result.signals)
    
    # IDE stream
    ide_result = observer.observe_ide("main.py", "def hello(): pass")
    assert len(ide_result.signals) == 1
    assert ide_result.signals[0].metadata.get("language") == "Python"
    
    # Terminal stream (with error)
    terminal_result = observer.observe_terminal("Traceback (most recent call last):\n  Error: Something failed")
    assert len(terminal_result.signals) == 1
    assert terminal_result.signals[0].signal_type.name == "CORRECTION"
    
    print("  ✓ UnifiedObserver passed")


def test_goal_constrained_prompt():
    """Test that the injector respects Goal hierarchy."""
    print("Testing Goal-Constrained Prompt...")
    
    kernel = ScopedKernel(enable_thread_safety=False)
    
    # Add Goal
    goal = UserGoal(
        goal_id="g1",
        content="Be concise in all responses",
        scope_path=[],
        priority=10
    )
    kernel.add_goal(goal)
    
    # Add Fact
    fact = UserFact(
        fact_id="f1",
        content="User likes humor",
        scope_path=[],
        priority=5
    )
    kernel.add_fact(fact)
    
    # Add Established Rule
    rule = ScopedRule(
        rule_id="r1",
        content="Prefers Python",
        scope_path=["Coding"],
        confidence=0.9,
        state=RuleState.ESTABLISHED
    )
    kernel.scoped_rules["r1"] = rule
    
    # Generate prompt
    prompt = generate_system_prompt(kernel, "Write code")
    
    # Verify Goal is present
    assert "CORE DIRECTIVES" in prompt
    assert "Be concise" in prompt
    
    # Verify Fact is present
    assert "PREFERENCES" in prompt
    assert "humor" in prompt
    
    print("  ✓ Goal-Constrained Prompt passed")


def run_tests():
    print("\n" + "="*60)
    print("IBLM v3.1 - Goal-Constrained Kernel Tests")
    print("="*60 + "\n")
    
    try:
        test_goal_fact_hierarchy()
        test_unified_observer()
        test_goal_constrained_prompt()
        print("\n" + "="*60)
        print("All v3.1 tests passed!")
        print("="*60)
        return True
    except Exception as e:
        print(f"\nFailed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if not run_tests():
        sys.exit(1)
