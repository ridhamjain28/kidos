#!/usr/bin/env python
"""
IBLM Core - Example Usage
=========================

This example demonstrates the complete IBLM workflow:
1. Creating a brain
2. Teaching it about the user
3. Observing interactions
4. Injecting personalized context
5. Handling corrections
6. Saving and loading

Run this file to see IBLM in action!
"""

import sys
import os

# Add IBLM directory to path
iblm_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, iblm_dir)

from iblm import IBLM, create_brain


def main():
    print("=" * 70)
    print("IBLM Core - Individual Behavior Learning Machine")
    print("=" * 70)
    print()
    
    # ===========================
    # Step 1: Create a Brain
    # ===========================
    print("📦 Creating IBLM brain...")
    brain = create_brain()
    print(f"   Brain ID: {brain.id}")
    print()
    
    # ===========================
    # Step 2: Teach the Brain
    # ===========================
    print("🎓 Teaching the brain about the user...")
    
    brain.teach("I'm a senior Python developer", category="expertise")
    print("   ✓ Taught: Python expertise")
    
    brain.teach("I prefer TypeScript for frontend", category="preference")
    print("   ✓ Taught: TypeScript preference")
    
    brain.teach("Always include type hints", category="workflow")
    print("   ✓ Taught: Type hints workflow")
    
    brain.teach("I prefer concise, technical responses", category="style")
    print("   ✓ Taught: Communication style")
    
    print()
    
    # ===========================
    # Step 3: Set Project Context  
    # ===========================
    print("📁 Setting up project context...")
    brain.set_project("FastAPI Backend", "REST API for e-commerce platform")
    print("   ✓ Active project: FastAPI Backend")
    print()
    
    # ===========================
    # Step 4: Observe Interactions
    # ===========================
    print("👀 Observing user-AI interactions...")
    
    interactions = [
        ("How do I structure my FastAPI project?", 
         "Here's a recommended structure with routers, services, and models..."),
        
        ("I prefer keeping endpoints in separate files",
         "Got it! I'll organize endpoints by domain..."),
        
        ("No, actually group them by feature, not domain",
         "Understood! Switching to feature-based organization..."),
        
        ("Add authentication to the user endpoint",
         "Here's JWT authentication implementation..."),
        
        ("Make it more concise",
         "Here's the shortened version with just the essentials...")
    ]
    
    for i, (user_input, ai_output) in enumerate(interactions, 1):
        result = brain.observe(user_input, ai_output)
        print(f"   {i}. Observed: \"{user_input[:40]}...\"")
        print(f"      Signals extracted: {result['signals_extracted']}")
    
    print()
    
    # ===========================
    # Step 5: Check Evolution
    # ===========================
    print("🧬 Checking brain evolution...")
    stats = brain.get_stats()
    print(f"   Total rules: {stats['total_rules']}")
    print(f"   Total nodes: {stats['total_nodes']}")
    print(f"   Profile confidence: {stats['profile_confidence']:.1%}")
    print(f"   Interactions processed: {stats['total_interactions_processed']}")
    print()
    
    # ===========================
    # Step 6: Get User Persona
    # ===========================
    print("👤 Generated User Persona:")
    persona = brain.get_user_persona()
    if persona:
        print(f"   {persona}")
    else:
        print("   (Persona still being learned)")
    print()
    
    # ===========================
    # Step 7: Inject Context
    # ===========================
    print("💉 Injecting context for new prompt...")
    new_prompt = "How should I implement rate limiting?"
    injection = brain.inject(new_prompt)
    
    print(f"   Prompt: \"{new_prompt}\"")
    print(f"   Rules injected: {injection.rules_injected}")
    print(f"   Nodes injected: {injection.nodes_injected}")
    print(f"   Estimated tokens: {injection.estimated_tokens}")
    print()
    print("   System Header Preview:")
    print("   " + "-" * 50)
    # Show first 500 chars of header
    header_preview = injection.system_header[:500]
    for line in header_preview.split('\n'):
        print(f"   {line}")
    if len(injection.system_header) > 500:
        print("   ...")
    print("   " + "-" * 50)
    print()
    
    # ===========================
    # Step 8: Enhance Prompt
    # ===========================
    print("✨ Enhancing user prompt with context...")
    enhanced = brain.injector.enhance_prompt(new_prompt)
    print(f"   Original: \"{new_prompt}\"")
    print(f"   Enhanced: \"{enhanced}\"")
    print()
    
    # ===========================
    # Step 9: Get Reflection Prompt
    # ===========================
    print("🪞 Generating reflection prompt (AI as user)...")
    reflection = brain.get_reflection_prompt()
    if reflection:
        print(f"   {reflection[:200]}...")
    else:
        print("   (Not enough data yet)")
    print()
    
    # ===========================
    # Step 10: Save the Brain
    # ===========================
    print("💾 Saving brain to file...")
    save_path = "example_brain.json.gz"
    brain.save(save_path)
    print(f"   ✓ Saved to: {save_path}")
    
    # Check file size
    import os
    file_size = os.path.getsize(save_path)
    print(f"   File size: {file_size / 1024:.1f} KB")
    print()
    
    # ===========================
    # Step 11: Load and Verify
    # ===========================
    print("📂 Loading brain from file...")
    loaded_brain = IBLM.load(save_path)
    print(f"   ✓ Loaded brain: {loaded_brain.id}")
    
    loaded_stats = loaded_brain.get_stats()
    print(f"   Rules preserved: {loaded_stats['total_rules']}")
    print(f"   Nodes preserved: {loaded_stats['total_nodes']}")
    print()
    
    # ===========================
    # Cleanup
    # ===========================
    os.remove(save_path)
    print("🗑️  Cleaned up example file")
    print()
    
    # ===========================
    # Summary
    # ===========================
    print("=" * 70)
    print("IBLM Demo Complete!")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("1. IBLM learns WHO you are, not just what you said")
    print("2. Corrections are high-priority learning events")
    print("3. Context is compiled into rules, not stored as text")
    print("4. The entire brain fits in a small, portable file")
    print("5. Context injection gives LLMs 'telepathic' understanding")
    print()
    print("Next steps:")
    print("- Integrate with your LLM of choice")
    print("- Build a persistent brain that grows over time")
    print("- Experiment with the reflection prompt for AI-as-user")
    print()


if __name__ == "__main__":
    main()
