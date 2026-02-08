"""
IBLM Core - Context Injector
=============================

Intercepts user prompts and injects personalized context.

BREAKTHROUGH CONCEPT:
The ContextInjector is the OUTPUT layer of IBLM. It takes the compiled
knowledge in the UserKernel and transforms it into a system header
that gives the LLM "telepathic" understanding of the user.

Key Innovations:
1. RELEVANCE SCORING: Only inject context relevant to the current query
2. TOKEN EFFICIENCY: Compress context to minimize token usage
3. PERSONA INJECTION: The LLM receives a "user persona" description
4. DYNAMIC CONTEXT: Context changes based on active project, recent work

Traditional RAG: "Here's everything the user ever said"
IBLM: "Here's a compiled profile of WHO this user is and what they need"

The difference is O(n) vs O(log n) context growth.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

try:
    from .models import Rule, KernelNode, StyleVector, UserProfile
    from .kernel import UserKernel
except ImportError:
    from models import Rule, KernelNode, StyleVector, UserProfile
    from kernel import UserKernel


@dataclass
class InjectionConfig:
    """Configuration for context injection."""
    max_rules: int = 5              # Maximum rules to include
    max_nodes: int = 3              # Maximum nodes to include
    min_relevance: float = 0.3     # Minimum relevance score
    include_style: bool = True      # Include style description
    include_profile: bool = True    # Include user profile
    include_working_memory: bool = True
    max_header_tokens: int = 500    # Approximate token limit
    format: str = "natural"         # "natural" or "structured"


@dataclass
class InjectionResult:
    """Result of context injection."""
    system_header: str
    rules_injected: int
    nodes_injected: int
    estimated_tokens: int
    relevance_scores: Dict[str, float]


class ContextInjector:
    """
    Injects personalized context into LLM prompts.
    
    BREAKTHROUGH: This is how we achieve "telepathic" AI.
    
    The ContextInjector takes the user's prompt and enriches the
    LLM's system message with:
    
    1. USER PERSONA: "This user is a Python expert who prefers concise,
       technical responses..."
       
    2. RELEVANT RULES: Compiled behavioral rules that apply to this query
    
    3. ACTIVE CONTEXT: Current project, recent work, working memory
    
    4. STYLE GUIDANCE: How to communicate with this specific user
    
    The result is that the LLM responds as if it has known the user
    for years, even in a brand new conversation.
    
    USAGE:
        injector = ContextInjector(kernel)
        header = injector.inject("How do I implement authentication?")
        
        # Use header as system message for LLM
        response = llm.chat(
            system=header.system_header,
            user="How do I implement authentication?"
        )
    """
    
    def __init__(
        self, 
        kernel: UserKernel,
        config: Optional[InjectionConfig] = None
    ):
        self.kernel = kernel
        self.config = config or InjectionConfig()
    
    def inject(
        self, 
        user_prompt: str,
        override_context: Optional[Dict] = None
    ) -> InjectionResult:
        """
        Inject personalized context for a user prompt.
        
        Args:
            user_prompt: The user's current prompt
            override_context: Optional context overrides
            
        Returns:
            InjectionResult with system header and metadata
        """
        # Get active context from kernel
        context = self.kernel.get_active_context(user_prompt)
        
        # Apply overrides
        if override_context:
            context.update(override_context)
        
        # Build system header based on format
        if self.config.format == "structured":
            header = self._build_structured_header(context, user_prompt)
        else:
            header = self._build_natural_header(context, user_prompt)
        
        # Calculate relevance scores
        relevance_scores = self._calculate_relevance(context)
        
        # Estimate token count (rough: 1 token ≈ 4 chars)
        estimated_tokens = len(header) // 4
        
        return InjectionResult(
            system_header=header,
            rules_injected=len(context.get("relevant_rules", [])),
            nodes_injected=len(context.get("relevant_nodes", [])),
            estimated_tokens=estimated_tokens,
            relevance_scores=relevance_scores,
        )
    
    def _build_natural_header(
        self, 
        context: Dict[str, Any],
        user_prompt: str
    ) -> str:
        """
        Build a natural language system header.
        
        This format reads like a briefing about the user.
        """
        parts = []
        
        # User persona (the "Individual" in IBLM)
        if self.config.include_profile and context.get("user_profile"):
            persona = context["user_profile"]
            if persona:
                parts.append(f"USER CONTEXT: {persona}")
        
        # Communication style
        if self.config.include_style and context.get("style"):
            style = context["style"]
            if style and style != "style still being learned":
                parts.append(f"COMMUNICATION STYLE: {style}")
        
        # Relevant behavioral rules
        rules = context.get("relevant_rules", [])
        if rules:
            rule_strs = []
            for rule in rules[:self.config.max_rules]:
                if rule["weight"] >= self.config.min_relevance:
                    rule_strs.append(f"- {rule['action']}")
            
            if rule_strs:
                parts.append("PREFERENCES:\n" + "\n".join(rule_strs))
        
        # Active project context
        project = context.get("active_project")
        if project:
            proj_desc = f"ACTIVE PROJECT: {project['name']}"
            if project.get("context"):
                proj_desc += f" - {project['context']}"
            parts.append(proj_desc)
            
            # Connected concepts
            if project.get("connected"):
                connected = [n["name"] for n in project["connected"][:3]]
                if connected:
                    parts.append(f"RELATED: {', '.join(connected)}")
        
        # Relevant knowledge nodes
        nodes = context.get("relevant_nodes", [])
        if nodes:
            node_strs = []
            for node in nodes[:self.config.max_nodes]:
                node_strs.append(f"- {node['name']}: {node['context']}")
            
            if node_strs:
                parts.append("CONTEXT:\n" + "\n".join(node_strs))
        
        # Working memory (current session context)
        if self.config.include_working_memory:
            wm = context.get("working_memory", {})
            if wm:
                wm_strs = [f"- {k}: {v}" for k, v in list(wm.items())[:3]]
                parts.append("RECENT:\n" + "\n".join(wm_strs))
        
        # Combine into header
        header = "\n\n".join(parts)
        
        # Add instruction
        if header:
            header = (
                "You have context about this user from previous interactions. "
                "Apply this knowledge to provide personalized responses.\n\n"
                + header
            )
        
        return header
    
    def _build_structured_header(
        self, 
        context: Dict[str, Any],
        user_prompt: str
    ) -> str:
        """
        Build a structured (JSON-like) system header.
        
        This format is more precise but less natural.
        """
        import json
        
        structured = {
            "user_context": {}
        }
        
        # User profile
        if self.config.include_profile and context.get("user_profile"):
            structured["user_context"]["persona"] = context["user_profile"]
        
        # Style
        if self.config.include_style and context.get("style"):
            structured["user_context"]["style"] = context["style"]
        
        # Rules
        rules = context.get("relevant_rules", [])
        if rules:
            structured["user_context"]["preferences"] = [
                r["action"] for r in rules[:self.config.max_rules]
                if r["weight"] >= self.config.min_relevance
            ]
        
        # Project
        if context.get("active_project"):
            structured["user_context"]["active_project"] = context["active_project"]["name"]
        
        # Format as instructions
        header = (
            "USER CONTEXT (apply to responses):\n"
            + json.dumps(structured["user_context"], indent=2)
        )
        
        return header
    
    def _calculate_relevance(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Calculate relevance scores for debugging."""
        scores = {}
        
        for i, rule in enumerate(context.get("relevant_rules", [])):
            scores[f"rule_{i}"] = rule.get("weight", 0.0)
        
        for i, node in enumerate(context.get("relevant_nodes", [])):
            scores[f"node_{i}"] = 0.5  # Nodes don't have explicit relevance
        
        return scores
    
    def enhance_prompt(
        self, 
        user_prompt: str
    ) -> str:
        """
        Enhance a user prompt with contextual information.
        
        BREAKTHROUGH: This is "prompt enhancement as user reflection."
        
        Instead of just adding context, we reformulate the prompt
        as if the LLM already knows the user. This makes the prompt
        more specific and targeted.
        
        Example:
        Original: "How do I implement auth?"
        Enhanced: "How should I implement authentication in FastAPI 
                   for my Project Alpha, keeping in mind I prefer 
                   JWT tokens and have experience with OAuth2?"
        """
        context = self.kernel.get_active_context(user_prompt)
        
        enhancements = []
        
        # Add project context
        if self.kernel.active_project:
            enhancements.append(f"for my {self.kernel.active_project} project")
        
        # Add relevant preferences
        rules = context.get("relevant_rules", [])
        prefs = [r["action"] for r in rules[:2] if r["weight"] > 0.5]
        if prefs:
            enhancements.append(f"keeping in mind that I {', '.join(prefs).lower()}")
        
        # Add expertise context
        profile = self.kernel.profile
        if profile.expertise_domains:
            top_domain = max(
                profile.expertise_levels.items(),
                key=lambda x: x[1],
                default=(None, 0)
            )
            if top_domain[0]:
                enhancements.append(f"(I'm experienced with {top_domain[0]})")
        
        # Combine
        if enhancements:
            enhanced = f"{user_prompt} {' '.join(enhancements)}"
            return enhanced
        
        return user_prompt
    
    def generate_reflection_prompt(self) -> str:
        """
        Generate a prompt that represents the user's reflection.
        
        BREAKTHROUGH: The LLM can act "as the user" for planning/reflection.
        
        This generates a system prompt that makes the LLM embody
        the user's perspective, useful for:
        - Planning what the user might want next
        - Reviewing work from user's perspective
        - Generating user-like responses
        """
        profile = self.kernel.profile
        style = self.kernel.style_vector
        
        parts = []
        
        # Identity
        if profile.role:
            parts.append(f"I am a {profile.role}")
            if profile.industry:
                parts.append(f"in the {profile.industry} industry")
        
        # Expertise
        if profile.expertise_domains:
            high_exp = [d for d, l in profile.expertise_levels.items() if l > 0.7]
            if high_exp:
                parts.append(f"I'm an expert in {', '.join(high_exp)}")
        
        # Preferences
        if profile.preferred_languages:
            parts.append(f"I prefer working with {', '.join(profile.preferred_languages[:2])}")
        
        if profile.avoided_technologies:
            parts.append(f"I avoid {', '.join(profile.avoided_technologies[:2])}")
        
        # Style
        style_desc = style.describe()
        if style_desc != "style still being learned":
            parts.append(f"My communication style: {style_desc}")
        
        # Goals
        if profile.active_goals:
            parts.append(f"I'm currently focused on: {profile.active_goals[0]}")
        
        # Combine
        reflection = ". ".join(parts) + "." if parts else ""
        
        if reflection:
            return (
                "You are embodying the perspective of the following user. "
                "Respond as if you ARE this person:\n\n"
                f"{reflection}"
            )
        
        return ""
    
    def get_context_summary(self) -> str:
        """Get a human-readable summary of current context."""
        stats = self.kernel.get_stats()
        profile = self.kernel.profile
        
        lines = [
            f"Profile Confidence: {profile.profile_confidence:.1%}",
            f"Total Interactions: {stats['total_interactions_processed']}",
            f"Active Rules: {stats['total_rules']}",
            f"Knowledge Nodes: {stats['total_nodes']}",
        ]
        
        if profile.expertise_domains:
            lines.append(f"Expertise: {', '.join(profile.expertise_domains[:3])}")
        
        if profile.preferred_languages:
            lines.append(f"Languages: {', '.join(profile.preferred_languages[:3])}")
        
        if self.kernel.active_project:
            lines.append(f"Active Project: {self.kernel.active_project}")
        
        return "\n".join(lines)


class ConversationEnhancer:
    """
    Enhanced conversation management with IBLM.
    
    This class wraps an LLM interaction to automatically:
    1. Inject context before each query
    2. Observe each interaction after response
    3. Evolve the kernel based on signals
    
    USAGE:
        enhancer = ConversationEnhancer(iblm)
        
        # User asks a question
        response = enhancer.chat(llm, "How do I implement auth?")
        
        # The enhancer automatically:
        # - Injects personalized context
        # - Observes the interaction
        # - Updates the kernel
    """
    
    def __init__(
        self, 
        kernel: UserKernel,
        injector: Optional[ContextInjector] = None
    ):
        self.kernel = kernel
        self.injector = injector or ContextInjector(kernel)
        
        # Import here to avoid circular imports
        try:
            from .observer import InteractionObserver
            from .compiler import LogicCompiler
        except ImportError:
            from observer import InteractionObserver
            from compiler import LogicCompiler
        
        self.observer = InteractionObserver()
        self.compiler = LogicCompiler(kernel)
    
    def prepare_prompt(self, user_input: str) -> Tuple[str, str]:
        """
        Prepare a prompt with injected context.
        
        Returns (system_message, enhanced_user_input).
        """
        # Get context injection
        injection = self.injector.inject(user_input)
        
        # Optionally enhance the prompt
        enhanced_input = self.injector.enhance_prompt(user_input)
        
        return injection.system_header, enhanced_input
    
    def process_response(
        self, 
        user_input: str, 
        ai_response: str
    ) -> Dict[str, Any]:
        """
        Process an AI response: observe and evolve.
        
        Returns evolution report.
        """
        # Log the interaction
        self.kernel.log_interaction(user_input, ai_response)
        
        # Extract signals
        result = self.observer.observe(user_input, ai_response)
        
        # Add signals to kernel
        for signal in result.signals:
            self.kernel.add_signal(signal)
        
        # Evolve the kernel
        report = self.compiler.evolve(result.signals)
        
        return {
            "signals_extracted": len(result.signals),
            "confidence": result.confidence_score,
            "evolution": str(report),
        }
    
    def chat_wrapper(
        self, 
        llm_call: callable,
        user_input: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Wrapper for LLM calls that automatically handles context.
        
        Args:
            llm_call: A function that takes (system, user) and returns response
            user_input: The user's input
            
        Returns:
            (ai_response, processing_info)
        """
        # Prepare prompt with context
        system_msg, enhanced_input = self.prepare_prompt(user_input)
        
        # Call LLM
        response = llm_call(system_msg, enhanced_input)
        
        # Process the response
        info = self.process_response(user_input, response)
        
        return response, info


# =============================================================================
# v3.0 SCIENTIFIC MEMORY: UNIVERSAL INJECTION
# =============================================================================

def generate_system_prompt(kernel: "ScopedKernel", user_query: str) -> str:
    """
    v3.0 UNIVERSAL INJECTION: Generate a system prompt with ESTABLISHED rules.
    
    This is the key output layer of Scientific Memory:
    1. Detect Scope of user_query
    2. Retrieve only ESTABLISHED rules for that Scope + Global
    3. Format as a compact "Persona Block"
    
    Args:
        kernel: The ScopedKernel
        user_query: The user's current query
        
    Returns:
        A system prompt string with injected persona
    """
    try:
        from .models import RuleState
        from .compiler import ScopedCompiler
    except ImportError:
        from models import RuleState
        from compiler import ScopedCompiler
    
    # Detect scope from query
    compiler = ScopedCompiler(kernel)
    scope_path, _ = compiler._detect_scope(
        type("Signal", (), {"content": user_query, "metadata": {}})()
    )
    
    # Collect ESTABLISHED rules for this scope + Global
    established_rules = []
    
    for rule in kernel.scoped_rules.values():
        # Only ESTABLISHED rules get injected
        if rule.state != RuleState.ESTABLISHED:
            continue
        
        # Check if rule applies to current scope or is global
        if not rule.scope_path or rule.matches_context(scope_path):
            established_rules.append(rule)
    
    # Sort by confidence/weight
    established_rules.sort(key=lambda r: r.confidence * r.weight, reverse=True)
    
    # === v3.1 GOAL-CONSTRAINED INJECTION ===
    
    # Get active goals (Constraints)
    goals = []
    if hasattr(kernel, 'get_active_goals'):
        goals = kernel.get_active_goals(scope_path)
    
    # Get facts not conflicting with goals
    facts = []
    if hasattr(kernel, 'get_facts_not_conflicting'):
        facts = kernel.get_facts_not_conflicting(scope_path)
    
    # Build Persona Block
    lines = ["# MISSION BRIEFING", "You are the user's Semantic Twin.", ""]
    
    # Goals (High Priority)
    if goals:
        lines.append("## CORE DIRECTIVES (Laws - MUST FOLLOW)")
        for goal in goals[:5]:
            scope_str = " > ".join(goal.scope_path) if goal.scope_path else "Global"
            lines.append(f"- [{scope_str}] {goal.content} (Priority: {goal.priority})")
        lines.append("")
    
    # Facts (Lower Priority, filtered)
    if facts:
        lines.append("## PREFERENCES (Follow unless conflicts with Laws)")
        for fact in facts[:5]:
            scope_str = " > ".join(fact.scope_path) if fact.scope_path else "Global"
            lines.append(f"- [{scope_str}] {fact.content}")
        lines.append("")
    
    # Established Rules (Legacy v3.0)
    if established_rules:
        lines.append("## VERIFIED BEHAVIORS")
        for rule in established_rules[:5]:
            scope_str = " > ".join(rule.scope_path) if rule.scope_path else "Global"
            lines.append(f"- [{scope_str}] {rule.content}")
    
    return "\n".join(lines)

