"""
Call note taking module.
Records conversation transcripts, generates summaries, and extracts action items.
"""

import json
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .call_conversation import ConversationContext


@dataclass
class CallNote:
    """Complete note for a single call."""
    call_id: str
    timestamp: datetime
    caller_number: Optional[str]
    caller_name: Optional[str]
    duration_seconds: int
    transcript: str
    summary: str
    action_items: List[str]
    blocked_requests: List[str]
    sentiment: str = "neutral"
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'call_id': self.call_id,
            'timestamp': self.timestamp.isoformat(),
            'caller_number': self.caller_number,
            'caller_name': self.caller_name,
            'duration_seconds': self.duration_seconds,
            'transcript': self.transcript,
            'summary': self.summary,
            'action_items': self.action_items,
            'blocked_requests': self.blocked_requests,
            'sentiment': self.sentiment,
            'tags': self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CallNote':
        """Create CallNote from dictionary."""
        return cls(
            call_id=data['call_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            caller_number=data.get('caller_number'),
            caller_name=data.get('caller_name'),
            duration_seconds=data['duration_seconds'],
            transcript=data['transcript'],
            summary=data['summary'],
            action_items=data.get('action_items', []),
            blocked_requests=data.get('blocked_requests', []),
            sentiment=data.get('sentiment', 'neutral'),
            tags=data.get('tags', []),
        )


class CallNotes:
    """
    Manages call note taking and storage.
    
    Features:
    - Record conversation transcripts
    - Generate call summaries
    - Extract action items
    - Store caller information
    - Export to JSON
    """
    
    def __init__(self, notes_dir: str = "data/call_notes"):
        """
        Initialize CallNotes.
        
        Args:
            notes_dir: Directory to store call notes
        """
        self.notes_dir = Path(notes_dir)
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        
        self.calls_db: Dict[str, CallNote] = {}
        self._load_existing_notes()
        
        logger.info(f"CallNotes initialized. Directory: {self.notes_dir}")
    
    def _load_existing_notes(self):
        """Load existing call notes from disk."""
        try:
            for file_path in self.notes_dir.glob("call_*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    note = CallNote.from_dict(data)
                    self.calls_db[note.call_id] = note
            
            logger.info(f"Loaded {len(self.calls_db)} existing call notes")
        except Exception as e:
            logger.error(f"Error loading notes: {e}")
    
    def _generate_call_id(self, caller_number: Optional[str]) -> str:
        """Generate unique call ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        number_suffix = caller_number[-4:] if caller_number and len(caller_number) >= 4 else "unknown"
        return f"{timestamp}_{number_suffix}"
    
    def _generate_summary(self, transcript: str) -> str:
        """
        Generate a summary of the conversation.
        
        Args:
            transcript: Full conversation transcript
            
        Returns:
            Generated summary
        """
        # Simple rule-based summary
        lines = transcript.strip().split('\n')
        
        if not lines or len(lines) < 2:
            return "Brief call with no substantial conversation."
        
        # Count messages
        caller_msgs = [l for l in lines if l.startswith('caller:')]
        assistant_msgs = [l for l in lines if l.startswith('assistant:')]
        
        summary_parts = []
        
        if len(caller_msgs) == 0:
            summary_parts.append("Caller did not speak.")
        elif len(caller_msgs) == 1:
            summary_parts.append("Brief exchange with caller.")
        else:
            summary_parts.append(f"Conversation with {len(caller_msgs)} exchanges.")
        
        # Check for specific patterns
        transcript_lower = transcript.lower()
        
        if 'message' in transcript_lower:
            summary_parts.append("Caller left a message.")
        
        if any(word in transcript_lower for word in ['call back', 'callback', 'call later']):
            summary_parts.append("Suggested callback.")
        
        if 'blocked' in transcript_lower or 'confidential' in transcript_lower:
            summary_parts.append("Confidential information was requested but not shared.")
        
        return " ".join(summary_parts)
    
    def _extract_action_items(self, transcript: str) -> List[str]:
        """
        Extract action items from conversation.
        
        Args:
            transcript: Full conversation transcript
            
        Returns:
            List of action items
        """
        action_items = []
        transcript_lower = transcript.lower()
        
        # Pattern matching for common action items
        patterns = [
            (r'call (?:him|her|them|back)', "Call back"),
            (r'(?:will|should) call', "Call back"),
            (r'(?:message|text) (?:him|her|them)', "Send message"),
            (r'urgent|important|asap', "Follow up (marked urgent)"),
            (r'email|mail', "Check for email"),
            (r'tomorrow|later|soon', "Schedule follow-up"),
        ]
        
        for pattern, action in patterns:
            import re
            if re.search(pattern, transcript_lower):
                if action not in action_items:
                    action_items.append(action)
        
        return action_items
    
    def _determine_sentiment(self, transcript: str) -> str:
        """
        Determine call sentiment from transcript.
        
        Args:
            transcript: Full conversation transcript
            
        Returns:
            Sentiment string: 'positive', 'negative', 'neutral', 'urgent'
        """
        transcript_lower = transcript.lower()
        
        # Urgent keywords
        urgent_words = ['urgent', 'emergency', 'immediately', 'asap', 'critical', 'important']
        if any(word in transcript_lower for word in urgent_words):
            return "urgent"
        
        # Negative keywords
        negative_words = ['angry', 'frustrated', 'bad', 'terrible', 'awful', 'wrong', 'problem', 'issue']
        negative_count = sum(1 for word in negative_words if word in transcript_lower)
        
        # Positive keywords
        positive_words = ['good', 'great', 'excellent', 'thank', 'thanks', 'appreciate', 'helpful']
        positive_count = sum(1 for word in positive_words if word in transcript_lower)
        
        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        
        return "neutral"
    
    def save_call(
        self,
        context: ConversationContext,
        duration_seconds: int = 0
    ) -> CallNote:
        """
        Save a completed call to notes.
        
        Args:
            context: Conversation context
            duration_seconds: Call duration in seconds
            
        Returns:
            Created CallNote
        """
        call_id = self._generate_call_id(context.caller_number)
        transcript = context.get_transcript()
        
        note = CallNote(
            call_id=call_id,
            timestamp=datetime.now(),
            caller_number=context.caller_number,
            caller_name=context.caller_name,
            duration_seconds=duration_seconds,
            transcript=transcript,
            summary=self._generate_summary(transcript),
            action_items=self._extract_action_items(transcript),
            blocked_requests=context.blocked_attempts,
            sentiment=self._determine_sentiment(transcript),
            tags=[]
        )
        
        # Add tags based on content
        if context.blocked_attempts:
            note.tags.append("confidential-request")
        if note.sentiment == "urgent":
            note.tags.append("urgent")
        if note.action_items:
            note.tags.append("has-actions")
        
        # Save to file
        file_path = self.notes_dir / f"call_{call_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(note.to_dict(), f, indent=2, ensure_ascii=False)
        
        # Add to memory
        self.calls_db[call_id] = note
        
        logger.info(f"Call note saved: {call_id}")
        return note
    
    def get_call(self, call_id: str) -> Optional[CallNote]:
        """Get a specific call note by ID."""
        return self.calls_db.get(call_id)
    
    def get_calls_by_number(self, phone_number: str) -> List[CallNote]:
        """Get all calls from a specific number."""
        return [
            note for note in self.calls_db.values()
            if note.caller_number == phone_number
        ]
    
    def get_recent_calls(self, limit: int = 10) -> List[CallNote]:
        """Get most recent calls."""
        sorted_calls = sorted(
            self.calls_db.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )
        return sorted_calls[:limit]
    
    def export_all(self, output_file: str = "all_calls.json") -> str:
        """
        Export all calls to a single JSON file.
        
        Args:
            output_file: Output file path
            
        Returns:
            Path to exported file
        """
        output_path = self.notes_dir / output_file
        
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_calls': len(self.calls_db),
            'calls': [note.to_dict() for note in self.calls_db.values()]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(self.calls_db)} calls to {output_path}")
        return str(output_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored calls."""
        if not self.calls_db:
            return {'total_calls': 0}
        
        total_duration = sum(n.duration_seconds for n in self.calls_db.values())
        
        return {
            'total_calls': len(self.calls_db),
            'total_duration_minutes': round(total_duration / 60, 2),
            'avg_duration_seconds': round(total_duration / len(self.calls_db), 2),
            'urgent_calls': sum(1 for n in self.calls_db.values() if n.sentiment == 'urgent'),
            'blocked_requests': sum(len(n.blocked_requests) for n in self.calls_db.values()),
        }


if __name__ == "__main__":
    # Test
    notes = CallNotes()
    
    # Create mock context
    from .call_conversation import ConversationContext
    
    ctx = ConversationContext(
        caller_number="+1234567890",
        caller_name="Test Caller"
    )
    ctx.add_turn("assistant", "Hello, this is the assistant speaking.")
    ctx.add_turn("caller", "Hi, can you tell me where you are?")
    ctx.add_turn("assistant", "I cannot share location information.")
    ctx.blocked_attempts.append("location request")
    
    note = notes.save_call(ctx, duration_seconds=45)
    print(f"Saved call: {note.call_id}")
    print(f"Summary: {note.summary}")
    print(f"Action items: {note.action_items}")
    print(f"Sentiment: {note.sentiment}")
