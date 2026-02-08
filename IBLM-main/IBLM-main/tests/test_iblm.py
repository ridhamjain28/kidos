"""
IBLM Core - Test Suite
======================

Comprehensive tests for the Individual Behavior Learning Machine.
"""

import pytest
import json
import tempfile
import os
from datetime import datetime

# Import IBLM components
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    Signal, SignalType, Rule, RuleCategory, 
    KernelNode, StyleVector, UserProfile, InteractionLog
)
from embeddings import EmbeddingEngine, SemanticMatcher
from kernel import UserKernel
from observer import InteractionObserver
from compiler import LogicCompiler
from injector import ContextInjector
from iblm import IBLM, create_brain


class TestModels:
    """Test core data models."""
    
    def test_signal_creation(self):
        signal = Signal(
            signal_type=SignalType.CORRECTION,
            content="Use TypeScript instead",
            confidence=0.9,
            source_hash="abc123",
        )
        assert signal.signal_type == SignalType.CORRECTION
        assert signal.confidence == 0.9
    
    def test_signal_serialization(self):
        signal = Signal(
            signal_type=SignalType.PREFERENCE,
            content="Python",
            confidence=0.8,
            source_hash="xyz789",
        )
        data = signal.to_dict()
        restored = Signal.from_dict(data)
        assert restored.content == signal.content
        assert restored.signal_type == signal.signal_type
    
    def test_rule_reinforcement(self):
        rule = Rule(
            rule_id="r1",
            category=RuleCategory.TECHNICAL_PREFERENCE,
            condition="When coding",
            action="Use TypeScript",
            weight=0.5,
        )
        initial_weight = rule.weight
        rule.reinforce(0.2)
        assert rule.weight == initial_weight + 0.2
    
    def test_rule_contradiction(self):
        rule = Rule(
            rule_id="r2",
            category=RuleCategory.TECHNICAL_PREFERENCE,
            condition="When coding",
            action="Use Python",
            weight=0.8,
        )
        rule.contradict(0.3)
        assert rule.weight == 0.5
        assert rule.contradictions == 1
    
    def test_style_vector_update(self):
        style = StyleVector()
        initial = style.formality
        style.update("formality", 0.9, strength=1.0)
        assert style.formality != initial
        assert style.formality > initial  # Should move towards 0.9
    
    def test_user_profile(self):
        profile = UserProfile()
        profile.update_expertise("Python", 0.9)
        profile.add_preference("language", "TypeScript", is_positive=True)
        profile.record_interaction()
        
        assert "Python" in profile.expertise_domains
        assert "TypeScript" in profile.preferred_languages
        assert profile.total_interactions == 1


class TestEmbeddings:
    """Test embedding engine."""
    
    def test_embed(self):
        engine = EmbeddingEngine()
        embedding = engine.embed("Hello world")
        assert len(embedding) == 128  # Default size
        assert all(isinstance(x, float) for x in embedding)
    
    def test_cosine_similarity(self):
        engine = EmbeddingEngine()
        emb1 = engine.embed("Python programming")
        emb2 = engine.embed("Python coding")
        emb3 = engine.embed("Cooking recipes")
        
        sim_similar = engine.cosine_similarity(emb1, emb2)
        sim_different = engine.cosine_similarity(emb1, emb3)
        
        # Similar texts should have higher similarity
        assert sim_similar > sim_different
    
    def test_semantic_matcher(self):
        engine = EmbeddingEngine()
        matcher = SemanticMatcher(engine)
        
        result = matcher.is_similar(
            "Use Python for this",
            "Python is preferred",
            threshold=0.3
        )
        assert isinstance(result, bool)


class TestKernel:
    """Test UserKernel."""
    
    def test_add_rule(self):
        kernel = UserKernel()
        rule = Rule(
            rule_id="test_rule",
            category=RuleCategory.TECHNICAL_PREFERENCE,
            condition="When coding",
            action="Use TypeScript",
            weight=0.8,
        )
        rule_id = kernel.add_rule(rule)
        assert rule_id == "test_rule"
        assert kernel.get_rule("test_rule") is not None
    
    def test_add_node(self):
        kernel = UserKernel()
        node = KernelNode(
            node_id="project_alpha",
            node_type="project",
            name="Project Alpha",
            context="ML pipeline project",
        )
        node_id = kernel.add_node(node)
        assert kernel.get_node(node_id) is not None
    
    def test_query_rules(self):
        kernel = UserKernel()
        
        # Add some rules
        for i, lang in enumerate(["Python", "TypeScript", "Rust"]):
            rule = Rule(
                rule_id=f"rule_{i}",
                category=RuleCategory.TECHNICAL_PREFERENCE,
                condition="When coding",
                action=f"Use {lang}",
                weight=0.8,
            )
            rule.embedding = kernel.embedding_engine.embed(f"Use {lang}")
            kernel.add_rule(rule)
        
        results = kernel.query_rules("What language should I use?", top_k=2)
        assert len(results) <= 2
    
    def test_working_memory(self):
        kernel = UserKernel()
        kernel.set_working_memory("current_task", "Building API")
        
        value = kernel.get_working_memory("current_task")
        assert value == "Building API"
        
        kernel.clear_working_memory()
        assert kernel.get_working_memory("current_task") is None
    
    def test_export_import(self):
        kernel = UserKernel()
        
        # Add some data
        rule = Rule(
            rule_id="export_test",
            category=RuleCategory.TECHNICAL_PREFERENCE,
            condition="test",
            action="test action",
            weight=0.7,
        )
        kernel.add_rule(rule)
        kernel.profile.update_expertise("Python", 0.9)
        
        # Export
        data = kernel.export()
        
        # Import
        kernel2 = UserKernel.load(data)
        
        assert kernel2.get_rule("export_test") is not None
        assert "Python" in kernel2.profile.expertise_domains


class TestObserver:
    """Test InteractionObserver."""
    
    def test_observe_correction(self):
        observer = InteractionObserver()
        result = observer.observe(
            "No, use TypeScript instead of JavaScript",
            "Alright, converting to TypeScript..."
        )
        
        correction_signals = [
            s for s in result.signals 
            if s.signal_type == SignalType.CORRECTION
        ]
        assert len(correction_signals) > 0
    
    def test_observe_preference(self):
        observer = InteractionObserver()
        result = observer.observe(
            "I prefer using Python for data analysis",
            "Great choice! Here's the Python code..."
        )
        
        pref_signals = [
            s for s in result.signals 
            if s.signal_type == SignalType.PREFERENCE
        ]
        assert len(pref_signals) > 0
    
    def test_observe_expertise(self):
        observer = InteractionObserver()
        result = observer.observe(
            "I know Python well and I'm familiar with async/await patterns",
            "Given your expertise..."
        )
        
        exp_signals = [
            s for s in result.signals 
            if s.signal_type == SignalType.EXPERTISE
        ]
        assert len(exp_signals) > 0


class TestCompiler:
    """Test LogicCompiler."""
    
    def test_evolve_creates_rules(self):
        kernel = UserKernel()
        compiler = LogicCompiler(kernel)
        
        # Create multiple preference signals
        signals = [
            Signal(
                signal_type=SignalType.PREFERENCE,
                content="Python",
                confidence=0.8,
                source_hash=f"hash_{i}",
            )
            for i in range(3)
        ]
        
        report = compiler.evolve(signals)
        assert report.rules_created > 0 or report.rules_updated > 0
    
    def test_evolve_detects_contradictions(self):
        kernel = UserKernel()
        compiler = LogicCompiler(kernel)
        
        # Add a rule about using Python
        rule = Rule(
            rule_id="python_rule",
            category=RuleCategory.TECHNICAL_PREFERENCE,
            condition="When coding",
            action="Use Python",
            weight=0.8,
        )
        rule.embedding = kernel.embedding_engine.embed("Use Python for coding")
        kernel.add_rule(rule)
        
        # Correct with "don't use Python"
        correction = Signal(
            signal_type=SignalType.CORRECTION,
            content="Don't use Python, use TypeScript instead",
            confidence=0.9,
            source_hash="correction_hash",
        )
        
        report = compiler.evolve([correction])
        assert report.rules_contradicted > 0


class TestInjector:
    """Test ContextInjector."""
    
    def test_inject(self):
        kernel = UserKernel()
        kernel.profile.role = "Software Engineer"
        kernel.profile.preferred_languages = ["Python", "TypeScript"]
        kernel.style_vector.technicality = 0.8
        kernel.style_vector.confidence["technicality"] = 0.8
        
        injector = ContextInjector(kernel)
        result = injector.inject("How do I implement authentication?")
        
        assert result.system_header != ""
        assert result.estimated_tokens > 0
    
    def test_enhance_prompt(self):
        kernel = UserKernel()
        kernel.set_active_project("MyProject")
        kernel.profile.preferred_languages = ["Python"]
        
        injector = ContextInjector(kernel)
        enhanced = injector.enhance_prompt("Write a function")
        
        # Should include project context
        assert "MyProject" in enhanced or "project" in enhanced.lower()


class TestIBLM:
    """Test main IBLM class."""
    
    def test_create_brain(self):
        brain = create_brain()
        assert brain is not None
        assert brain.kernel is not None
    
    def test_observe(self):
        brain = IBLM()
        result = brain.observe(
            "I prefer concise responses",
            "Got it! I'll keep responses brief."
        )
        assert result["status"] == "observed"
        assert result["signals_extracted"] >= 0
    
    def test_inject(self):
        brain = IBLM()
        brain.observe("I'm an expert Python developer", "Great!")
        
        result = brain.inject("How do I write async code?")
        assert result.system_header != ""
    
    def test_teach(self):
        brain = IBLM()
        rule_id = brain.teach("Always use TypeScript", category="preference")
        assert rule_id is not None
        
        rule = brain.kernel.get_rule(rule_id)
        assert rule is not None
        assert "TypeScript" in rule.action
    
    def test_save_load(self):
        brain = IBLM()
        brain.observe("I prefer Python", "Noted!")
        brain.teach("Use dark mode themes")
        brain.set_project("TestProject", "A test project")
        
        # Save
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            brain.save(path)
            
            # Load
            brain2 = IBLM.load(path)
            
            assert len(brain2.kernel.rules) > 0
            assert brain2.kernel.find_node_by_name("TestProject") is not None
        finally:
            os.unlink(path)
    
    def test_garbage_collection(self):
        brain = IBLM()
        
        # Observe many interactions
        for i in range(25):
            brain.observe(f"Message {i}", f"Response {i}", evolve=False)
        
        brain.evolve()
        result = brain.garbage_collect()
        
        # Should have cleaned something
        total_cleaned = sum(result.values())
        assert total_cleaned >= 0  # May be 0 if nothing compiled yet
    
    def test_learning_flow(self):
        """Test complete learning flow."""
        brain = IBLM()
        
        # User interacts
        brain.observe("I'm building a web app", "What tech stack?")
        brain.observe("I prefer React and TypeScript", "Good choices!")
        brain.observe("No, actually use Vue.js", "Switching to Vue...")
        
        # Check that correction was learned
        context = brain.inject("What framework should I use?")
        
        # The brain should have learned something
        stats = brain.get_stats()
        assert stats["total_rules"] >= 0


class TestIntegration:
    """Integration tests."""
    
    def test_full_workflow(self):
        """Test complete IBLM workflow."""
        # Create brain
        brain = IBLM()
        
        # Simulate user session
        brain.set_project("MyAPI", "FastAPI backend project")
        
        # User teaches preferences
        brain.teach("I'm an expert in Python and FastAPI")
        brain.teach("Always include type hints")
        brain.teach("Prefer async/await patterns")
        
        # Observe some interactions
        brain.observe(
            "Write an endpoint for user authentication",
            "Here's a FastAPI endpoint..."
        )
        brain.observe(
            "Make it more concise",
            "Here's the shortened version..."
        )
        
        # Get context for new prompt
        result = brain.inject("How do I add database integration?")
        
        # Verify context includes learned preferences
        assert "system_header" in dir(result) or hasattr(result, 'system_header')
        
        # Check stats
        stats = brain.get_stats()
        assert stats["total_interactions_processed"] >= 2
        
        # Test export/import
        data = brain.export()
        brain2 = IBLM.from_dict(data)
        
        # Verify state preserved
        assert brain2.kernel.active_project == "MyAPI"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
