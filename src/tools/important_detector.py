"""
Important Message Detector
Detects urgent/important messages, prioritizes known contacts, filters spam
Local processing only, privacy-focused
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ContactPriority:
    """Contact priority configuration"""
    name: str
    phone: str
    priority: int  # 1-5, higher = more important
    groups: List[str]


class ImportantDetector:
    """
    Detect important messages based on keywords, sender priority, and patterns
    Read-only analysis, local processing
    """
    
    # Urgency keywords (case-insensitive)
    URGENT_KEYWORDS = [
        'urgent', 'emergency', 'asap', 'immediately', 'critical',
        'important', 'priority', 'alert', 'warning', 'attention',
        'call me', 'call now', 'need help', 'help me', 'trouble',
        'accident', 'hospital', 'police', 'fire', 'danger',
        'deadline', 'expired', 'overdue', 'late', 'missed',
        'meeting now', 'meeting started', 'join now', 'starting now',
        'otp', 'verification', 'code', 'password', 'login',
        'payment', 'transaction', 'bank', 'money', 'transfer'
    ]
    
    # Spam indicators
    SPAM_KEYWORDS = [
        'winner', 'congratulations', 'you won', 'prize', 'lottery',
        'free', 'click here', 'limited time', 'act now', 'urgent offer',
        'congrats', 'selected', 'claim now', 'claim your', 'cash prize',
        'million', 'billion', 'inheritance', 'lottery winner',
        'nigerian prince', 'investment opportunity', 'make money fast',
        'work from home', 'earn extra', 'double your', 'guaranteed'
    ]
    
    # Time-sensitive patterns
    TIME_PATTERNS = [
        r'\b(?:in|within)\s+\d+\s*(?:min|minute|hour|hr)s?\b',
        r'\btoday\b',
        r'\btomorrow\b',
        r'\b(?:by|before)\s+(?:tomorrow|today|\d{1,2}[\s:]?(?:am|pm))',
        r'\b(?:morning|afternoon|evening|night)\b'
    ]
    
    def __init__(self, 
                 known_contacts: Optional[List[ContactPriority]] = None,
                 custom_urgent_keywords: Optional[List[str]] = None,
                 spam_threshold: float = 0.3):
        self.known_contacts: Dict[str, ContactPriority] = {}
        self.custom_keywords = custom_urgent_keywords or []
        self.spam_threshold = spam_threshold
        
        # Load known contacts
        if known_contacts:
            for contact in known_contacts:
                self.known_contacts[contact.phone] = contact
        
        # Compile regex patterns
        self.time_patterns = [re.compile(p, re.IGNORECASE) for p in self.TIME_PATTERNS]
        
        # Message history for context
        self.message_history: List[Dict] = []
        self.max_history = 50
        
        # Tracking for rate limiting
        self.sender_message_counts: Dict[str, List[datetime]] = {}
        self.rate_limit_window = timedelta(minutes=5)
        self.rate_limit_count = 10
    
    def add_contact(self, contact: ContactPriority):
        """Add a known contact with priority"""
        self.known_contacts[contact.phone] = contact
        logger.info(f"Added contact: {contact.name} (priority {contact.priority})")
    
    def remove_contact(self, phone: str):
        """Remove a contact"""
        if phone in self.known_contacts:
            del self.known_contacts[phone]
    
    def analyze(self, message: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """
        Analyze a message to determine if it's important
        
        Args:
            message: Parsed message dict with sender, content, etc.
            
        Returns:
            Tuple of (is_important, confidence_score, reasons)
        """
        reasons = []
        score = 0.0
        
        # Check for spam first
        spam_score = self._calculate_spam_score(message)
        if spam_score > self.spam_threshold:
            logger.debug(f"Message from {message.get('sender')} flagged as spam")
            return False, 0.0, ["spam_detected"]
        
        # Check sender priority
        sender_priority = self._get_sender_priority(message)
        if sender_priority > 3:
            score += 0.3
            reasons.append("high_priority_contact")
        elif sender_priority > 0:
            score += 0.1
            reasons.append("known_contact")
        
        # Check for urgent keywords
        keyword_matches = self._check_urgent_keywords(message)
        if keyword_matches:
            score += min(0.4, len(keyword_matches) * 0.15)
            reasons.extend([f"keyword:{kw}" for kw in keyword_matches[:3]])
        
        # Check for time sensitivity
        if self._is_time_sensitive(message):
            score += 0.2
            reasons.append("time_sensitive")
        
        # Check for actionable content
        actionable_score = self._check_actionable_content(message)
        if actionable_score > 0:
            score += actionable_score
            reasons.append("actionable")
        
        # Check rate limiting (too many messages from same sender)
        if self._is_rate_limited(message):
            score -= 0.2
            reasons.append("rate_limited")
        
        # Final decision
        is_important = score >= 0.5
        
        # Store in history
        self._add_to_history(message, is_important, score, reasons)
        
        return is_important, min(1.0, score), reasons
    
    def _calculate_spam_score(self, message: Dict) -> float:
        """Calculate probability that message is spam"""
        content = message.get('content', '').lower()
        if not content:
            return 0.0
        
        spam_count = sum(1 for keyword in self.SPAM_KEYWORDS if keyword in content)
        return min(1.0, spam_count / 5.0)  # Normalize to 0-1
    
    def _get_sender_priority(self, message: Dict) -> int:
        """Get priority level of sender (0-5)"""
        sender = message.get('sender', '')
        sender_name = message.get('sender_name', '')
        
        # Check by phone number
        if sender in self.known_contacts:
            return self.known_contacts[sender].priority
        
        # Check by name
        for contact in self.known_contacts.values():
            if contact.name.lower() in sender_name.lower():
                return contact.priority
        
        # Check if group message
        if message.get('is_group'):
            return 1  # Slightly higher priority for groups
        
        return 0  # Unknown sender
    
    def _check_urgent_keywords(self, message: Dict) -> List[str]:
        """Check for urgent keywords in message"""
        content = message.get('content', '').lower()
        if not content:
            return []
        
        matches = []
        all_keywords = self.URGENT_KEYWORDS + self.custom_keywords
        
        for keyword in all_keywords:
            if keyword in content:
                matches.append(keyword)
        
        return matches
    
    def _is_time_sensitive(self, message: Dict) -> bool:
        """Check if message contains time-sensitive language"""
        content = message.get('content', '')
        if not content:
            return False
        
        for pattern in self.time_patterns:
            if pattern.search(content):
                return True
        
        return False
    
    def _check_actionable_content(self, message: Dict) -> float:
        """Check if message contains actionable content"""
        score = 0.0
        extracted = message.get('extracted_info', {})
        
        # Contains URL
        if extracted.get('urls'):
            score += 0.1
        
        # Contains phone number
        if extracted.get('phone_numbers'):
            score += 0.1
        
        # Contains verification code
        if extracted.get('codes'):
            score += 0.2
        
        # Contains question mark (asking something)
        content = message.get('content', '')
        if '?' in content:
            score += 0.1
        
        return score
    
    def _is_rate_limited(self, message: Dict) -> bool:
        """Check if sender is sending too many messages"""
        sender = message.get('sender', '')
        now = datetime.now()
        
        if sender not in self.sender_message_counts:
            self.sender_message_counts[sender] = []
        
        # Clean old entries
        self.sender_message_counts[sender] = [
            ts for ts in self.sender_message_counts[sender]
            if now - ts < self.rate_limit_window
        ]
        
        # Check count
        if len(self.sender_message_counts[sender]) >= self.rate_limit_count:
            return True
        
        # Add current message
        self.sender_message_counts[sender].append(now)
        return False
    
    def _add_to_history(self, message: Dict, is_important: bool, score: float, reasons: List[str]):
        """Add message analysis to history"""
        entry = {
            'message': message,
            'is_important': is_important,
            'score': score,
            'reasons': reasons,
            'timestamp': datetime.now()
        }
        
        self.message_history.append(entry)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)
    
    def get_important_messages(self, limit: int = 20) -> List[Dict]:
        """Get recent messages marked as important"""
        important = [
            entry for entry in self.message_history
            if entry['is_important']
        ]
        return important[-limit:]
    
    def should_forward_to_telegram(self, message: Dict) -> Tuple[bool, str]:
        """
        Determine if message should be forwarded to Telegram
        
        Returns:
            Tuple of (should_forward, reason)
        """
        is_important, score, reasons = self.analyze(message)
        
        if not is_important:
            return False, "not_important"
        
        # High confidence important messages
        if score > 0.8:
            return True, f"high_priority ({', '.join(reasons[:2])})"
        
        # Medium confidence from known contacts
        if score > 0.6 and self._get_sender_priority(message) > 0:
            return True, f"medium_priority_known ({', '.join(reasons[:2])})"
        
        # Verification codes always forwarded
        if 'keyword:otp' in reasons or 'keyword:code' in reasons or 'keyword:verification' in reasons:
            return True, "verification_code"
        
        # Emergency keywords always forwarded
        emergency_keywords = ['emergency', 'hospital', 'police', 'accident', 'danger']
        if any(kw in str(reasons).lower() for kw in emergency_keywords):
            return True, "emergency"
        
        return False, "threshold_not_met"
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of recent analysis"""
        total = len(self.message_history)
        important = sum(1 for e in self.message_history if e['is_important'])
        
        return {
            'total_analyzed': total,
            'important_count': important,
            'important_rate': important / total if total > 0 else 0,
            'known_contacts': len(self.known_contacts),
            'top_reasons': self._get_top_reasons()
        }
    
    def _get_top_reasons(self, limit: int = 5) -> List[Tuple[str, int]]:
        """Get most common reasons for importance"""
        from collections import Counter
        
        all_reasons = []
        for entry in self.message_history:
            if entry['is_important']:
                all_reasons.extend(entry['reasons'])
        
        return Counter(all_reasons).most_common(limit)
    
    def clear_history(self):
        """Clear message history"""
        self.message_history.clear()
        self.sender_message_counts.clear()
        logger.info("Message history cleared")


# Convenience functions
def create_detector(known_contacts: Optional[List[Dict]] = None) -> ImportantDetector:
    """Create an important message detector"""
    contacts = None
    if known_contacts:
        contacts = [
            ContactPriority(
                name=c.get('name', ''),
                phone=c.get('phone', ''),
                priority=c.get('priority', 3),
                groups=c.get('groups', [])
            )
            for c in known_contacts
        ]
    
    return ImportantDetector(known_contacts=contacts)


# Example usage
if __name__ == "__main__":
    # Test detector
    detector = ImportantDetector()
    
    # Add test contacts
    detector.add_contact(ContactPriority(
        name="John Doe",
        phone="1234567890@s.whatsapp.net",
        priority=5,
        groups=[]
    ))
    
    # Test messages
    test_messages = [
        {
            'sender': '1234567890@s.whatsapp.net',
            'sender_name': 'John Doe',
            'content': 'Urgent: Call me immediately!',
            'is_group': False,
            'extracted_info': {}
        },
        {
            'sender': '9999999999@s.whatsapp.net',
            'sender_name': 'Unknown',
            'content': 'Congratulations! You won a prize!',
            'is_group': False,
            'extracted_info': {}
        },
        {
            'sender': '1234567890@s.whatsapp.net',
            'sender_name': 'John Doe',
            'content': 'Your OTP is 123456',
            'is_group': False,
            'extracted_info': {'codes': ['123456']}
        }
    ]
    
    for msg in test_messages:
        is_important, score, reasons = detector.analyze(msg)
        should_forward, forward_reason = detector.should_forward_to_telegram(msg)
        
        print(f"\nMessage: {msg['content'][:50]}...")
        print(f"  Important: {is_important} (score: {score:.2f})")
        print(f"  Reasons: {reasons}")
        print(f"  Forward to Telegram: {should_forward} ({forward_reason})")
    
    print(f"\nSummary: {detector.get_summary()}")
