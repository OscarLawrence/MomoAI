"""
User Input Coherence Validator for Axiom
Validates user input for logical contradictions before sending to AI
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

from .contracts import coherence_contract, ComplexityClass


class CoherenceLevel(Enum):
    """Coherence quality levels"""
    INCOHERENT = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    PERFECT = 4


@dataclass
class CoherenceResult:
    """Result of coherence validation"""
    level: CoherenceLevel
    score: float  # 0.0 to 1.0
    contradictions: List[str]
    reasoning_chain: List[str]
    confidence: float
    suggestions: List[str] = None


class UserInputValidator:
    """
    Validates user input for logical coherence before processing
    Prevents incoherent conversations from starting
    """
    
    def __init__(self):
        self.contradiction_patterns = [
            r"(?i)(not|never|no)\s+.*\s+(always|must|will)",
            r"(?i)(impossible|cannot)\s+.*\s+(will|must|always)",
            r"(?i)(all|every|always)\s+.*\s+(none|never|no)",
            r"(?i)(true|fact|certain)\s+.*\s+(false|wrong|incorrect)",
            r"(?i)O\(1\)\s+.*\s+(sort|sorting)",  # O(1) sorting is impossible
            r"(?i)(secure|encryption)\s+.*\s+O\(1\)",  # Secure operations can't be O(1)
        ]
        
        self.complexity_contradictions = [
            ("O(1)", ["sort", "sorting", "search in unsorted", "compare all"]),
            ("constant time", ["iterate", "loop", "traverse", "visit all"]),
            ("no memory", ["store", "cache", "remember", "save"]),
        ]
    
    @coherence_contract(
        input_types={"user_input": "str"},
        output_type="CoherenceResult",
        requires=["len(user_input.strip()) > 0"],
        ensures=["result.score >= 0.0", "result.score <= 1.0"],
        complexity_time=ComplexityClass.LINEAR,
        pure=True
    )
    def validate_prompt(self, user_input: str) -> CoherenceResult:
        """Validate user input for logical contradictions"""
        contradictions = self.detect_contradictions(user_input)
        suggestions = self.suggest_clarifications(contradictions, user_input)
        
        score = self._calculate_coherence_score(user_input, contradictions)
        level = self._score_to_level(score)
        confidence = self._calculate_confidence(user_input, contradictions)
        
        return CoherenceResult(
            level=level,
            score=score,
            contradictions=contradictions,
            reasoning_chain=[user_input],
            confidence=confidence,
            suggestions=suggestions
        )
    
    @coherence_contract(
        input_types={"text": "str"},
        output_type="List[str]",
        requires=["len(text.strip()) > 0"],
        complexity_time=ComplexityClass.LINEAR,
        pure=True
    )
    def detect_contradictions(self, text: str) -> List[str]:
        """Find logical contradictions in user input"""
        contradictions = []
        
        # Pattern-based contradiction detection
        for pattern in self.contradiction_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                contradictions.append(f"Logical contradiction: {match.group()}")
        
        # Complexity contradiction detection
        text_lower = text.lower()
        for complexity, impossible_ops in self.complexity_contradictions:
            if complexity.lower() in text_lower:
                for op in impossible_ops:
                    if op in text_lower:
                        contradictions.append(
                            f"Complexity contradiction: {complexity} cannot perform '{op}'"
                        )
        
        # Semantic contradiction detection
        words = text_lower.split()
        
        # Check for direct opposites
        opposites = [
            ("always", "never"), ("all", "none"), ("true", "false"),
            ("possible", "impossible"), ("can", "cannot"), ("will", "won't"),
            ("secure", "insecure"), ("fast", "slow"), ("efficient", "inefficient")
        ]
        
        for pos, neg in opposites:
            if pos in words and neg in words:
                contradictions.append(f"Direct contradiction: '{pos}' and '{neg}' in same request")
        
        # Check for algorithmic impossibilities
        if any(word in text_lower for word in ["sort", "sorting"]):
            if any(word in text_lower for word in ["o(1)", "constant time", "instant"]):
                contradictions.append("Algorithmic impossibility: Sorting requires at least O(n log n) time")
        
        if any(word in text_lower for word in ["search", "find"]):
            if "unsorted" in text_lower and any(word in text_lower for word in ["o(1)", "constant"]):
                contradictions.append("Algorithmic impossibility: Searching unsorted data requires O(n) time")
        
        return contradictions
    
    @coherence_contract(
        input_types={"contradictions": "List[str]", "original_input": "str"},
        output_type="List[str]",
        complexity_time=ComplexityClass.LINEAR,
        pure=True
    )
    def suggest_clarifications(self, contradictions: List[str], original_input: str) -> List[str]:
        """Generate clarifying questions for incoherent input"""
        suggestions = []
        
        if not contradictions:
            return suggestions
        
        text_lower = original_input.lower()
        
        # Suggestions for complexity contradictions
        if any("o(1)" in c.lower() for c in contradictions):
            if "sort" in text_lower:
                suggestions.append("Did you mean: 'efficient sorting algorithm' (O(n log n))?")
            if "search" in text_lower:
                suggestions.append("Did you mean: 'fast search in sorted data' (O(log n))?")
        
        # Suggestions for logical contradictions
        if any("always" in c and "never" in c for c in contradictions):
            suggestions.append("Please clarify: Do you mean 'usually' or 'sometimes' instead of 'always'?")
        
        if any("impossible" in c and "will" in c for c in contradictions):
            suggestions.append("Please clarify: Do you mean 'difficult' instead of 'impossible'?")
        
        # Suggestions for security contradictions
        if any("secure" in c and "o(1)" in c.lower() for c in contradictions):
            suggestions.append("Did you mean: 'efficient security algorithm' (security requires computational work)?")
        
        # Generic suggestion if no specific ones apply
        if not suggestions and contradictions:
            suggestions.append("Please rephrase your request to resolve the logical contradictions.")
        
        return suggestions
    
    def _calculate_coherence_score(self, text: str, contradictions: List[str]) -> float:
        """Calculate coherence score for user input"""
        if not text.strip():
            return 0.0
        
        base_score = 1.0
        
        # Heavy penalty for contradictions
        if contradictions:
            contradiction_penalty = len(contradictions) * 0.3
            # Extra penalty for algorithmic impossibilities
            algorithmic_contradictions = [c for c in contradictions if "impossibility" in c.lower()]
            contradiction_penalty += len(algorithmic_contradictions) * 0.2
        else:
            contradiction_penalty = 0.0
        
        # Bonus for clear, detailed requests
        word_count = len(text.split())
        if word_count >= 10:
            base_score += 0.1
        elif word_count < 3:
            base_score -= 0.2
        
        final_score = max(0.0, base_score - contradiction_penalty)
        return min(1.0, final_score)
    
    def _score_to_level(self, score: float) -> CoherenceLevel:
        """Convert numeric score to coherence level"""
        if score >= 0.9:
            return CoherenceLevel.PERFECT
        elif score >= 0.7:
            return CoherenceLevel.HIGH
        elif score >= 0.5:
            return CoherenceLevel.MEDIUM
        elif score >= 0.3:
            return CoherenceLevel.LOW
        else:
            return CoherenceLevel.INCOHERENT
    
    def _calculate_confidence(self, text: str, contradictions: List[str]) -> float:
        """Calculate confidence in the coherence assessment"""
        base_confidence = 0.8
        
        # Higher confidence with more text to analyze
        word_count = len(text.split())
        text_bonus = min(0.2, word_count * 0.01)
        
        # Lower confidence if many contradictions (might be missing context)
        contradiction_penalty = len(contradictions) * 0.05
        
        return max(0.1, min(1.0, base_confidence + text_bonus - contradiction_penalty))