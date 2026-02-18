#!/usr/bin/env python3
"""
Smart Learning Engine for Closed Claw
Makes assistant learn, adapt, and evolve over time
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class LearnedPattern:
    """A learned user pattern"""
    pattern_type: str
    key: str
    value: Any
    confidence: float
    first_seen: datetime
    last_updated: datetime
    occurrence_count: int
    context: Dict[str, Any]


class SmartLearningEngine:
    """
    Central learning engine - makes assistant smart!
    Learns from user behavior, adapts, evolves
    """
    
    def __init__(self, data_dir: str = "~/.closed-claw/learning"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.patterns: Dict[str, LearnedPattern] = {}
        self.contact_priorities: Dict[str, float] = {}
        self.user_preferences: Dict[str, Any] = {}
        
        self._load_all_data()
        logger.info(f"🧠 Learning Engine: {len(self.patterns)} patterns loaded")
    
    def _load_all_data(self):
        """Load all learned data"""
        self._load_patterns()
        self._load_contact_priorities()
        self._load_preferences()
    
    def _load_patterns(self):
        """Load learned patterns"""
        patterns_file = self.data_dir / "patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    for key, val in data.items():
                        val['first_seen'] = datetime.fromisoformat(val['first_seen'])
                        val['last_updated'] = datetime.fromisoformat(val['last_updated'])
                        self.patterns[key] = LearnedPattern(**val)
            except Exception as e:
                logger.error(f"Error loading patterns: {e}")
    
    def _save_patterns(self):
        """Save learned patterns"""
        patterns_file = self.data_dir / "patterns.json"
        data = {}
        for key, pattern in self.patterns.items():
            val = asdict(pattern)
            val['first_seen'] = val['first_seen'].isoformat()
            val['last_updated'] = val['last_updated'].isoformat()
            data[key] = val
        
        with open(patterns_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # ==================== INTENT LEARNING ====================
    
    def learn_intent(self, user_input: str, actual_intent: str, context: Dict[str, Any] = None):
        """Learn that user_input maps to actual_intent"""
        normalized = user_input.lower().strip()
        key = f"intent:{normalized}"
        
        if key in self.patterns:
            pattern = self.patterns[key]
            if pattern.value == actual_intent:
                pattern.confidence = min(1.0, pattern.confidence + 0.1)
                pattern.occurrence_count += 1
                pattern.last_updated = datetime.now()
            else:
                pattern.confidence *= 0.8
        else:
            self.patterns[key] = LearnedPattern(
                pattern_type='intent',
                key=normalized,
                value=actual_intent,
                confidence=0.5,
                first_seen=datetime.now(),
                last_updated=datetime.now(),
                occurrence_count=1,
                context=context or {}
            )
            logger.info(f"🧠 Learned: '{user_input}' → {actual_intent}")
        
        self._save_patterns()
    
    def predict_intent(self, user_input: str) -> Optional[str]:
        """Predict intent based on learned patterns"""
        normalized = user_input.lower().strip()
        key = f"intent:{normalized}"
        
        if key in self.patterns:
            pattern = self.patterns[key]
            if pattern.confidence > 0.7:
                return pattern.value
        
        # Fuzzy match
        best_match = None
        best_score = 0.0
        
        for key, pattern in self.patterns.items():
            if pattern.pattern_type == 'intent':
                similarity = self._text_similarity(normalized, pattern.key)
                score = similarity * pattern.confidence
                if score > best_score and score > 0.6:
                    best_score = score
                    best_match = pattern.value
        
        return best_match
    
    # ==================== CONTACT PRIORITY ====================
    
    def learn_contact_interaction(self, contact: str, interaction_type: str, user_response: str, delay: float = 0):
        """Learn contact priority from user behavior"""
        if contact not in self.contact_priorities:
            self.contact_priorities[contact] = 0.5
        
        current = self.contact_priorities[contact]
        
        if interaction_type == 'call':
            if user_response == 'picked_up':
                if delay < 5:
                    new_priority = min(1.0, current + 0.2)
                elif delay < 15:
                    new_priority = min(1.0, current + 0.1)
                else:
                    new_priority = current
            elif user_response == 'ignored':
                new_priority = max(0.0, current - 0.1)
            elif user_response == 'rejected':
                new_priority = max(0.0, current - 0.2)
            else:
                new_priority = current
            
            self.contact_priorities[contact] = new_priority
            self._save_contact_priorities()
    
    def get_contact_priority(self, contact: str) -> float:
        """Get learned priority for contact"""
        return self.contact_priorities.get(contact, 0.5)
    
    def get_smart_call_delay(self, contact: str) -> int:
        """Get smart call delay (not hardcoded 20!)"""
        priority = self.get_contact_priority(contact)
        
        if priority > 0.8:
            return 10
        elif priority > 0.6:
            return 15
        elif priority > 0.4:
            return 20
        else:
            return 30
    
    # ==================== HELPER METHODS ====================
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)
    
    def _load_contact_priorities(self):
        file = self.data_dir / "contact_priorities.json"
        if file.exists():
            with open(file, 'r') as f:
                self.contact_priorities = json.load(f)
    
    def _load_preferences(self):
        file = self.data_dir / "preferences.json"
        if file.exists():
            with open(file, 'r') as f:
                self.user_preferences = json.load(f)
    
    def _save_contact_priorities(self):
        file = self.data_dir / "contact_priorities.json"
        with open(file, 'w') as f:
            json.dump(self.contact_priorities, f, indent=2)


_learning_engine = None

def get_learning_engine() -> SmartLearningEngine:
    """Get global learning engine"""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = SmartLearningEngine()
    return _learning_engine
