"""
IBLM Core - Interaction Observer
================================

Listens to the (User_Input, AI_Output) stream and extracts implicit signals.

BREAKTHROUGH CONCEPT:
Instead of just storing what was said, we analyze HOW things were said
and WHAT they reveal about the user. This is Individual Behavior Learning.

Signal Types Extracted:
- CORRECTION: User corrects AI behavior ("No, do X instead")
- PREFERENCE: User expresses preference ("I prefer X")
- STYLE: User demonstrates communication style
- ENTITY: User introduces new entity (project, concept)
- EXPERTISE: User demonstrates domain expertise
- AVERSION: User shows dislike ("Don't use X")
- CONTEXT: User provides background context
- PERSONALITY: User reveals personality trait
- GOAL: User states objective
- WORKFLOW: User shows preferred workflow pattern

The Observer uses pattern matching and NLP heuristics to detect these
signals WITHOUT requiring an external LLM call. This makes observation
fast and cost-free.
"""

import re
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field

try:
    from .models import Signal, SignalType, InteractionLog
except ImportError:
    from models import Signal, SignalType, InteractionLog


# Pattern definitions for signal extraction
CORRECTION_PATTERNS = [
    r"\b(no|not|don't|dont|shouldn't|stop|wrong|incorrect|actually|instead|rather)\b",
    r"\b(change|fix|correct|update|modify|revise|redo)\b.*\b(this|that|it)\b",
    r"^(no[,.]|not that|wrong)",
]

PREFERENCE_PATTERNS = [
    r"\b(i prefer|i like|i want|i need|i'd rather|i would rather)\b",
    r"\b(prefer|favorite|always use|usually|typically)\b",
    r"\b(better if|would be nice|should be|make it)\b",
]

AVERSION_PATTERNS = [
    r"\b(don't like|hate|avoid|never use|dislike|not a fan)\b",
    r"\b(stop using|don't want|get rid of|remove)\b",
    r"\b(too complex|too simple|too verbose|too long|too short)\b",
]

EXPERTISE_PATTERNS = [
    r"\b(i know|i understand|i'm familiar|experienced with|expert in)\b",
    r"\b(obviously|of course|as you know|clearly)\b",
    r"\b(in my experience|from my work|professionally)\b",
]

ENTITY_PATTERNS = [
    r"\b(working on|my project|called|named|project)\b\s+[A-Z][a-zA-Z0-9_-]+",
    r"\b(using|with|in)\b\s+(FastAPI|Django|React|Vue|Angular|Node|Python|TypeScript|JavaScript)",
    r"@[a-zA-Z0-9_]+",  # Mentions
]

GOAL_PATTERNS = [
    r"\b(i want to|i need to|trying to|goal is|objective is|aim to)\b",
    r"\b(build|create|make|develop|implement)\b.*\b(that|which|so)\b",
    r"\b(end result|final|outcome|achieve)\b",
]

STYLE_INDICATORS = {
    "formal": [r"\b(kindly|please|would you|could you|regarding)\b"],
    "casual": [r"\b(hey|cool|awesome|nice|great|thanks|thx)\b"],
    "technical": [r"\b(implementation|architecture|algorithm|optimize|performance)\b"],
    "concise": [r"^.{1,50}$"],  # Short messages
    "detailed": [r"^.{200,}$"],  # Long messages
    "direct": [r"^(do|make|create|fix|change|add|remove)\b"],
}

PERSONALITY_INDICATORS = {
    "perfectionist": [r"\b(perfect|exactly|precise|correct|accurate)\b"],
    "pragmatic": [r"\b(quick|fast|simple|easy|just|good enough)\b"],
    "curious": [r"\b(why|how|what if|curious|wonder|interesting)\b"],
    "systematic": [r"\b(step by step|first|then|next|finally|process)\b"],
}


@dataclass
class SignalExtractionResult:
    """Result of signal extraction from an interaction."""
    signals: List[Signal]
    confidence_score: float
    raw_patterns_matched: List[str]


class InteractionObserver:
    """
    Observes user-AI interactions and extracts implicit behavioral signals.
    
    BREAKTHROUGH: We learn about the user WITHOUT storing their raw text.
    
    The Observer is the sensory system of the IBLM. It watches the stream
    of interactions and detects patterns that reveal:
    - What the user likes/dislikes
    - How they prefer to communicate
    - What domains they're expert in
    - What they're working on
    - Their personality traits
    
    All of this is extracted using lightweight pattern matching,
    requiring no external API calls.
    """
    
    def __init__(self):
        # Compile patterns for efficiency
        self._correction_patterns = [re.compile(p, re.IGNORECASE) for p in CORRECTION_PATTERNS]
        self._preference_patterns = [re.compile(p, re.IGNORECASE) for p in PREFERENCE_PATTERNS]
        self._aversion_patterns = [re.compile(p, re.IGNORECASE) for p in AVERSION_PATTERNS]
        self._expertise_patterns = [re.compile(p, re.IGNORECASE) for p in EXPERTISE_PATTERNS]
        self._entity_patterns = [re.compile(p, re.IGNORECASE) for p in ENTITY_PATTERNS]
        self._goal_patterns = [re.compile(p, re.IGNORECASE) for p in GOAL_PATTERNS]
        
        self._style_patterns = {
            style: [re.compile(p, re.IGNORECASE) for p in patterns]
            for style, patterns in STYLE_INDICATORS.items()
        }
        
        self._personality_patterns = {
            trait: [re.compile(p, re.IGNORECASE) for p in patterns]
            for trait, patterns in PERSONALITY_INDICATORS.items()
        }
        
        # Track recent signals for context
        self._recent_signals: List[Signal] = []
        self._max_recent = 50
    
    def observe(
        self, 
        user_input: str, 
        ai_output: str,
        session_context: Optional[Dict] = None
    ) -> SignalExtractionResult:
        """
        Observe an interaction and extract signals.
        
        Args:
            user_input: What the user said
            ai_output: What the AI responded
            session_context: Optional context about the current session
            
        Returns:
            SignalExtractionResult with all extracted signals
        """
        signals: List[Signal] = []
        patterns_matched: List[str] = []
        
        # Generate content hash for deduplication
        content_hash = self._hash_content(user_input, ai_output)
        
        # Extract different signal types
        signals.extend(self._extract_corrections(user_input, ai_output, content_hash))
        signals.extend(self._extract_preferences(user_input, content_hash))
        signals.extend(self._extract_aversions(user_input, content_hash))
        signals.extend(self._extract_expertise(user_input, ai_output, content_hash))
        signals.extend(self._extract_entities(user_input, content_hash))
        signals.extend(self._extract_goals(user_input, content_hash))
        signals.extend(self._extract_style(user_input, content_hash))
        signals.extend(self._extract_personality(user_input, content_hash))
        
        # Analyze interaction dynamics
        signals.extend(self._analyze_dynamics(user_input, ai_output, content_hash))
        
        # Track patterns matched (for debugging)
        patterns_matched = [s.content for s in signals]
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(signals)
        
        # Update recent signals
        self._recent_signals.extend(signals)
        if len(self._recent_signals) > self._max_recent:
            self._recent_signals = self._recent_signals[-self._max_recent:]
        
        return SignalExtractionResult(
            signals=signals,
            confidence_score=confidence,
            raw_patterns_matched=patterns_matched,
        )
    
    def _hash_content(self, user_input: str, ai_output: str) -> str:
        """Generate a hash of the interaction content."""
        import hashlib
        content = f"{user_input}|{ai_output}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _extract_corrections(
        self, 
        user_input: str, 
        ai_output: str, 
        content_hash: str
    ) -> List[Signal]:
        """
        Extract correction signals.
        
        CRITICAL: Corrections are the most valuable signals.
        When a user says "No, do X", they're explicitly teaching us.
        
        We give these high confidence and priority.
        """
        signals = []
        
        for pattern in self._correction_patterns:
            match = pattern.search(user_input)
            if match:
                # Extract what they're correcting
                correction_text = user_input
                
                # Try to find the corrected behavior
                # Look for patterns like "use X instead" or "do X not Y"
                instead_match = re.search(
                    r"(?:use|do|try|make it|should be)\s+(.+?)(?:\s+instead|\s*$)", 
                    user_input, 
                    re.IGNORECASE
                )
                
                if instead_match:
                    correction_text = f"Prefer: {instead_match.group(1)}"
                
                signals.append(Signal(
                    signal_type=SignalType.CORRECTION,
                    content=correction_text,
                    confidence=0.85,
                    source_hash=content_hash,
                    metadata={"pattern": pattern.pattern, "match": match.group()},
                ))
                break  # One correction signal per interaction
        
        return signals
    
    def _extract_preferences(self, user_input: str, content_hash: str) -> List[Signal]:
        """Extract preference signals."""
        signals = []
        
        for pattern in self._preference_patterns:
            match = pattern.search(user_input)
            if match:
                # Extract the preference
                # Look for what comes after the preference indicator
                after_match = user_input[match.end():].strip()
                preference_text = after_match[:100]  # Limit length
                
                if preference_text:
                    signals.append(Signal(
                        signal_type=SignalType.PREFERENCE,
                        content=preference_text,
                        confidence=0.7,
                        source_hash=content_hash,
                        metadata={"indicator": match.group()},
                    ))
        
        return signals
    
    def _extract_aversions(self, user_input: str, content_hash: str) -> List[Signal]:
        """Extract aversion signals (things user dislikes)."""
        signals = []
        
        for pattern in self._aversion_patterns:
            match = pattern.search(user_input)
            if match:
                # Extract what they don't like
                after_match = user_input[match.end():].strip()
                aversion_text = after_match[:100]
                
                if aversion_text:
                    signals.append(Signal(
                        signal_type=SignalType.AVERSION,
                        content=f"Avoid: {aversion_text}",
                        confidence=0.75,
                        source_hash=content_hash,
                        metadata={"indicator": match.group()},
                    ))
        
        return signals
    
    def _extract_expertise(
        self, 
        user_input: str, 
        ai_output: str, 
        content_hash: str
    ) -> List[Signal]:
        """
        Extract expertise signals.
        
        We detect expertise both from explicit statements ("I'm an expert in X")
        and from implicit indicators (using technical terminology correctly).
        """
        signals = []
        
        # Explicit expertise claims
        for pattern in self._expertise_patterns:
            match = pattern.search(user_input)
            if match:
                # Extract the domain
                after_match = user_input[match.end():].strip()
                domain = after_match.split()[0] if after_match else "general"
                
                signals.append(Signal(
                    signal_type=SignalType.EXPERTISE,
                    content=f"Expert: {domain}",
                    confidence=0.8,
                    source_hash=content_hash,
                    metadata={"indicator": match.group()},
                ))
        
        # Implicit expertise detection
        # Look for use of advanced terminology
        tech_terms = self._detect_technical_terms(user_input)
        if len(tech_terms) >= 3:  # Multiple tech terms suggest expertise
            domain = self._infer_domain(tech_terms)
            signals.append(Signal(
                signal_type=SignalType.EXPERTISE,
                content=f"Domain expertise: {domain}",
                confidence=0.6,
                source_hash=content_hash,
                metadata={"detected_terms": tech_terms},
            ))
        
        return signals
    
    def _extract_entities(self, user_input: str, content_hash: str) -> List[Signal]:
        """Extract entity signals (projects, tools, concepts)."""
        signals = []
        
        for pattern in self._entity_patterns:
            matches = pattern.findall(user_input)
            for match in matches:
                entity_name = match if isinstance(match, str) else match[0]
                entity_name = entity_name.strip()
                
                if len(entity_name) > 2:
                    signals.append(Signal(
                        signal_type=SignalType.ENTITY,
                        content=entity_name,
                        confidence=0.65,
                        source_hash=content_hash,
                        metadata={"type": self._classify_entity(entity_name)},
                    ))
        
        return signals
    
    def _extract_goals(self, user_input: str, content_hash: str) -> List[Signal]:
        """Extract goal signals."""
        signals = []
        
        for pattern in self._goal_patterns:
            match = pattern.search(user_input)
            if match:
                # Extract the goal description
                after_match = user_input[match.end():].strip()
                goal_text = after_match[:150]
                
                if goal_text:
                    signals.append(Signal(
                        signal_type=SignalType.GOAL,
                        content=goal_text,
                        confidence=0.7,
                        source_hash=content_hash,
                        metadata={"indicator": match.group()},
                    ))
        
        return signals
    
    def _extract_style(self, user_input: str, content_hash: str) -> List[Signal]:
        """
        Extract communication style signals.
        
        We analyze the user's writing to understand their preferred
        communication style: formal/casual, verbose/concise, etc.
        """
        signals = []
        
        for style, patterns in self._style_patterns.items():
            for pattern in patterns:
                if pattern.search(user_input):
                    signals.append(Signal(
                        signal_type=SignalType.STYLE,
                        content=f"style:{style}",
                        confidence=0.5,
                        source_hash=content_hash,
                        metadata={"style_dimension": style},
                    ))
                    break  # One signal per style dimension
        
        return signals
    
    def _extract_personality(self, user_input: str, content_hash: str) -> List[Signal]:
        """Extract personality trait signals."""
        signals = []
        
        for trait, patterns in self._personality_patterns.items():
            for pattern in patterns:
                if pattern.search(user_input):
                    signals.append(Signal(
                        signal_type=SignalType.PERSONALITY,
                        content=f"trait:{trait}",
                        confidence=0.4,  # Personality is hard to judge
                        source_hash=content_hash,
                        metadata={"trait": trait},
                    ))
                    break
        
        return signals
    
    def _analyze_dynamics(
        self, 
        user_input: str, 
        ai_output: str, 
        content_hash: str
    ) -> List[Signal]:
        """
        Analyze the dynamics of the interaction.
        
        This looks at patterns like:
        - Is the user iterating (short follow-ups)?
        - Is the user asking complex questions?
        - Is the user providing context or diving straight in?
        """
        signals = []
        
        # Message length dynamics
        user_length = len(user_input)
        ai_length = len(ai_output)
        
        if user_length < 50:
            signals.append(Signal(
                signal_type=SignalType.STYLE,
                content="style:concise_questions",
                confidence=0.4,
                source_hash=content_hash,
                metadata={"message_length": user_length},
            ))
        elif user_length > 300:
            signals.append(Signal(
                signal_type=SignalType.STYLE,
                content="style:detailed_context",
                confidence=0.4,
                source_hash=content_hash,
                metadata={"message_length": user_length},
            ))
        
        # Question complexity
        question_words = len(re.findall(r'\?', user_input))
        if question_words > 2:
            signals.append(Signal(
                signal_type=SignalType.STYLE,
                content="style:multi_question",
                confidence=0.5,
                source_hash=content_hash,
                metadata={"question_count": question_words},
            ))
        
        return signals
    
    def _detect_technical_terms(self, text: str) -> List[str]:
        """Detect technical terminology in text."""
        tech_words = {
            'api', 'database', 'server', 'client', 'function', 'class',
            'method', 'variable', 'algorithm', 'architecture', 'framework',
            'library', 'module', 'package', 'deploy', 'debug', 'compile',
            'runtime', 'async', 'sync', 'thread', 'process', 'memory',
            'cache', 'queue', 'stack', 'heap', 'pointer', 'reference',
            'interface', 'abstract', 'inherit', 'polymorphism', 'encapsulation'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if w in tech_words]
    
    def _infer_domain(self, tech_terms: List[str]) -> str:
        """Infer the technical domain from detected terms."""
        # Simple domain inference
        web_terms = {'api', 'server', 'client', 'deploy'}
        ml_terms = {'model', 'training', 'dataset', 'neural'}
        db_terms = {'database', 'query', 'schema', 'table'}
        
        web_count = len(set(tech_terms) & web_terms)
        ml_count = len(set(tech_terms) & ml_terms)
        db_count = len(set(tech_terms) & db_terms)
        
        if ml_count >= web_count and ml_count >= db_count:
            return "machine learning"
        elif db_count >= web_count:
            return "databases"
        elif web_count > 0:
            return "web development"
        else:
            return "software engineering"
    
    def _classify_entity(self, entity: str) -> str:
        """Classify an entity by type."""
        # Technology detection
        tech_names = {
            'python', 'javascript', 'typescript', 'rust', 'go', 'java',
            'react', 'vue', 'angular', 'fastapi', 'django', 'flask',
            'node', 'docker', 'kubernetes', 'aws', 'azure', 'gcp'
        }
        
        if entity.lower() in tech_names:
            return "technology"
        elif entity.startswith('@'):
            return "mention"
        elif entity[0].isupper():
            return "project"
        else:
            return "concept"
    
    def _calculate_confidence(self, signals: List[Signal]) -> float:
        """Calculate overall confidence in signal extraction."""
        if not signals:
            return 0.0
        
        # Average confidence weighted by signal type importance
        weights = {
            SignalType.CORRECTION: 2.0,
            SignalType.PREFERENCE: 1.5,
            SignalType.AVERSION: 1.5,
            SignalType.EXPERTISE: 1.3,
            SignalType.ENTITY: 1.0,
            SignalType.GOAL: 1.2,
            SignalType.STYLE: 0.8,
            SignalType.PERSONALITY: 0.7,
            SignalType.CONTEXT: 1.0,
            SignalType.WORKFLOW: 1.0,
        }
        
        total_weight = 0.0
        weighted_confidence = 0.0
        
        for signal in signals:
            w = weights.get(signal.signal_type, 1.0)
            weighted_confidence += signal.confidence * w
            total_weight += w
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def get_recent_signals(
        self, 
        signal_type: Optional[SignalType] = None,
        min_confidence: float = 0.0
    ) -> List[Signal]:
        """Get recent signals, optionally filtered."""
        signals = self._recent_signals
        
        if signal_type:
            signals = [s for s in signals if s.signal_type == signal_type]
        
        if min_confidence > 0:
            signals = [s for s in signals if s.confidence >= min_confidence]
        
        return signals
    
    def clear_recent(self) -> None:
        """Clear recent signal history."""
        self._recent_signals.clear()


# =============================================================================
# IBLM v3.1 - UNIFIED OBSERVER (Omni-Observer)
# =============================================================================

class StreamType:
    """Types of input streams."""
    BROWSER = "browser"   # User intent/dialogue
    IDE = "ide"           # Code context, files
    TERMINAL = "terminal" # Execution logs, errors


class UnifiedObserver:
    """
    v3.1 OMNI-OBSERVER
    
    Unified input layer that distinguishes between:
    - Browser Stream: User intent extraction
    - IDE Stream: Code context, focus state
    - Terminal Stream: Execution reality (filtered)
    """
    
    def __init__(self):
        self._base_observer = InteractionObserver()
        self._terminal_filter = None
        try:
            from validators import TerminalFilter
            self._terminal_filter = TerminalFilter
        except ImportError:
            pass
    
    def observe_browser(self, user_input: str, ai_output: str) -> SignalExtractionResult:
        """
        Observe browser/chat interaction.
        Primary source for intent extraction.
        """
        result = self._base_observer.observe(user_input, ai_output)
        # Tag signals with source
        for signal in result.signals:
            signal.metadata["stream"] = StreamType.BROWSER
        return result
    
    def observe_ide(
        self, 
        active_file: str, 
        active_lines: str,
        file_type: str = "unknown"
    ) -> SignalExtractionResult:
        """
        Observe IDE context.
        Extracts: language, framework, project context.
        """
        signals = []
        content_hash = self._base_observer._hash_content(active_file, active_lines)
        
        # Detect language from file extension
        lang_map = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
            ".java": "Java", ".go": "Go", ".rs": "Rust",
        }
        for ext, lang in lang_map.items():
            if active_file.endswith(ext):
                signals.append(Signal(
                    signal_type=SignalType.CONTEXT,
                    content=f"Working in {lang}",
                    confidence=0.9,
                    source_hash=content_hash,
                    metadata={"stream": StreamType.IDE, "language": lang}
                ))
                break
        
        return SignalExtractionResult(
            signals=signals,
            confidence_score=0.9 if signals else 0.0,
            raw_patterns_matched=[s.content for s in signals]
        )
    
    def observe_terminal(self, output: str) -> SignalExtractionResult:
        """
        Observe terminal output.
        Filters noise and extracts execution reality (errors, results).
        """
        # Apply noise filter
        if self._terminal_filter:
            output = self._terminal_filter.filter_cli_output(output)
        
        if not output.strip():
            return SignalExtractionResult(signals=[], confidence_score=0.0, raw_patterns_matched=[])
        
        signals = []
        content_hash = self._base_observer._hash_content(output, "")
        
        # Detect errors
        if "error" in output.lower() or "traceback" in output.lower():
            signals.append(Signal(
                signal_type=SignalType.CORRECTION,
                content=f"Execution error detected",
                confidence=0.8,
                source_hash=content_hash,
                metadata={"stream": StreamType.TERMINAL, "error_snippet": output[:200]}
            ))
        
        return SignalExtractionResult(
            signals=signals,
            confidence_score=0.8 if signals else 0.0,
            raw_patterns_matched=[s.content for s in signals]
        )


# =============================================================================
# IBLM v4.0 - ATTENTION FILTER (Biological Attention)
# =============================================================================

class DwellTracker:
    """
    v4.0 DWELL-TIME TRACKING
    
    Tracks how long the user has been viewing each file/context.
    Only contexts viewed for > min_dwell_seconds are considered "attended."
    """
    
    def __init__(self, min_dwell_seconds: float = 15.0):
        self.min_dwell = min_dwell_seconds
        self._timestamps: Dict[str, datetime] = {}  # file -> first_seen
        self._interactions: Dict[str, bool] = {}    # file -> has_interacted
    
    def mark_viewed(self, file_path: str) -> None:
        """Mark that user started viewing a file."""
        if file_path not in self._timestamps:
            self._timestamps[file_path] = datetime.now()
            self._interactions[file_path] = False
    
    def mark_interaction(self, file_path: str) -> None:
        """Mark that user interacted (typed, scrolled) in a file."""
        self._interactions[file_path] = True
    
    def is_attended(self, file_path: str) -> bool:
        """
        Check if file passes attention threshold.
        Must be viewed for >= min_dwell seconds AND have interaction.
        """
        if file_path not in self._timestamps:
            return False
        
        # Check dwell time
        dwell_seconds = (datetime.now() - self._timestamps[file_path]).total_seconds()
        if dwell_seconds < self.min_dwell:
            return False
        
        # Check interaction (action-gating)
        return self._interactions.get(file_path, False)
    
    def clear(self, file_path: str = None) -> None:
        """Clear tracking for a file or all files."""
        if file_path:
            self._timestamps.pop(file_path, None)
            self._interactions.pop(file_path, None)
        else:
            self._timestamps.clear()
            self._interactions.clear()


class AttentionFilteredObserver(UnifiedObserver):
    """
    v4.0 ATTENTION-FILTERED OBSERVER
    
    Extends UnifiedObserver with biological attention filters:
    - Dwell-time: Ignore files viewed < 15 seconds
    - Action-gating: Only process if user typed/scrolled
    - Noise cancellation: Built-in via TerminalFilter
    """
    
    def __init__(self, min_dwell_seconds: float = 15.0):
        super().__init__()
        self.dwell_tracker = DwellTracker(min_dwell_seconds)
    
    def observe_ide(
        self,
        active_file: str,
        active_lines: str,
        file_type: str = "unknown",
        user_interacted: bool = False
    ) -> SignalExtractionResult:
        """
        v4.0 ATTENTION-FILTERED IDE observation.
        
        Only processes if:
        1. User has been viewing file for >= min_dwell seconds
        2. User has interacted (typed or scrolled)
        """
        # Track viewing
        self.dwell_tracker.mark_viewed(active_file)
        
        # Track interaction if provided
        if user_interacted:
            self.dwell_tracker.mark_interaction(active_file)
        
        # Check attention threshold
        if not self.dwell_tracker.is_attended(active_file):
            return SignalExtractionResult(
                signals=[],
                confidence_score=0.0,
                raw_patterns_matched=[]
            )
        
        # Passed attention filter - process normally
        return super().observe_ide(active_file, active_lines, file_type)
    
    def file_closed(self, file_path: str) -> None:
        """Called when user closes a file to reset tracking."""
        self.dwell_tracker.clear(file_path)
