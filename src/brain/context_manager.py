"""
Context Manager Module
Manages conversation history, context window, and session persistence
"""

import os
import json
import time
import logging
import pickle
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UserPreferences:
    """User preferences and settings"""
    name: str = "User"
    language: str = "en"
    voice_enabled: bool = True
    notification_enabled: bool = True
    auto_read_messages: bool = False
    preferred_contacts: List[str] = field(default_factory=list)
    custom_shortcuts: Dict[str, str] = field(default_factory=dict)
    quiet_hours_start: Optional[int] = None  # 24h format
    quiet_hours_end: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserPreferences':
        return cls(**data)


@dataclass
class ConversationEntry:
    """Single conversation entry"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: float = field(default_factory=time.time)
    intent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp,
            'intent': self.intent,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationEntry':
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=data.get('timestamp', time.time()),
            intent=data.get('intent'),
            metadata=data.get('metadata', {})
        )
    
    def estimate_tokens(self) -> int:
        """Rough token estimation (4 chars ~= 1 token)"""
        return len(self.content) // 4 + 10  # +10 for overhead


@dataclass
class Session:
    """Conversation session"""
    session_id: str
    created_at: float
    last_active: float
    entries: List[ConversationEntry] = field(default_factory=list)
    context_summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'created_at': self.created_at,
            'last_active': self.last_active,
            'entries': [e.to_dict() for e in self.entries],
            'context_summary': self.context_summary,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        return cls(
            session_id=data['session_id'],
            created_at=data['created_at'],
            last_active=data['last_active'],
            entries=[ConversationEntry.from_dict(e) for e in data.get('entries', [])],
            context_summary=data.get('context_summary', ''),
            metadata=data.get('metadata', {})
        )
    
    def get_duration(self) -> float:
        """Get session duration in seconds"""
        return self.last_active - self.created_at
    
    def get_entry_count(self) -> int:
        """Get number of conversation entries"""
        return len(self.entries)


class ContextManager:
    """
    Context Manager for conversation memory
    Handles history, summarization, and session persistence
    """
    
    DEFAULT_CONFIG = {
        'max_context_tokens': 4096,
        'max_history_entries': 50,
        'summary_threshold': 20,  # Entries before summarization
        'session_timeout': 1800,  # 30 minutes
        'storage_dir': '~/.local/share/closed-claw/sessions',
        'auto_save': True,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.storage_dir = Path(os.path.expanduser(self.config['storage_dir']))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._current_session: Optional[Session] = None
        self._preferences: UserPreferences = UserPreferences()
        self._sessions_cache: Dict[str, Session] = {}
        
        # Load preferences
        self._load_preferences()
        
        # Load or create session
        self._load_or_create_session()
    
    def _get_session_file(self, session_id: str) -> Path:
        """Get path to session file"""
        return self.storage_dir / f"{session_id}.json"
    
    def _get_preferences_file(self) -> Path:
        """Get path to preferences file"""
        return self.storage_dir / 'preferences.json'
    
    def _load_preferences(self):
        """Load user preferences from disk"""
        prefs_file = self._get_preferences_file()
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._preferences = UserPreferences.from_dict(data)
                logger.info("Preferences loaded")
            except Exception as e:
                logger.error(f"Failed to load preferences: {e}")
    
    def _save_preferences(self):
        """Save user preferences to disk"""
        try:
            with open(self._get_preferences_file(), 'w', encoding='utf-8') as f:
                json.dump(self._preferences.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
    
    def _load_or_create_session(self):
        """Load most recent session or create new one"""
        # Find most recent session
        sessions = list(self.storage_dir.glob('session_*.json'))
        
        if sessions:
            # Sort by modification time
            sessions.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            for session_file in sessions:
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        session = Session.from_dict(data)
                        
                        # Check if session is still valid
                        if time.time() - session.last_active < self.config['session_timeout']:
                            self._current_session = session
                            self._sessions_cache[session.session_id] = session
                            logger.info(f"Loaded session: {session.session_id}")
                            return
                        break
                except Exception as e:
                    logger.error(f"Failed to load session: {e}")
        
        # Create new session
        self._create_new_session()
    
    def _create_new_session(self):
        """Create a new session"""
        session_id = f"session_{int(time.time())}_{os.urandom(4).hex()}"
        now = time.time()
        
        self._current_session = Session(
            session_id=session_id,
            created_at=now,
            last_active=now,
            entries=[]
        )
        self._sessions_cache[session_id] = self._current_session
        logger.info(f"Created new session: {session_id}")
    
    def _save_session(self, session: Session):
        """Save session to disk"""
        if not self.config['auto_save']:
            return
        
        try:
            session_file = self._get_session_file(session.session_id)
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def add_entry(self, role: str, content: str, intent: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Add entry to current conversation
        
        Args:
            role: 'user', 'assistant', or 'system'
            content: Message content
            intent: Optional intent classification
            metadata: Optional additional data
        """
        if not self._current_session:
            self._create_new_session()
        
        entry = ConversationEntry(
            role=role,
            content=content,
            timestamp=time.time(),
            intent=intent,
            metadata=metadata or {}
        )
        
        self._current_session.entries.append(entry)
        self._current_session.last_active = time.time()
        
        # Manage context window
        self._manage_context_window()
        
        # Auto-save
        self._save_session(self._current_session)
    
    def _manage_context_window(self):
        """Manage context window size"""
        if not self._current_session:
            return
        
        entries = self._current_session.entries
        
        # Check if summarization needed
        if len(entries) > self.config['summary_threshold']:
            self._summarize_old_entries()
        
        # Check token limit
        total_tokens = sum(e.estimate_tokens() for e in entries)
        while total_tokens > self.config['max_context_tokens'] and len(entries) > 2:
            # Remove oldest non-system entry
            for i, entry in enumerate(entries):
                if entry.role != 'system':
                    removed = entries.pop(i)
                    total_tokens -= removed.estimate_tokens()
                    break
            else:
                break
        
        # Check entry limit
        while len(entries) > self.config['max_history_entries']:
            for i, entry in enumerate(entries):
                if entry.role != 'system':
                    entries.pop(i)
                    break
    
    def _summarize_old_entries(self):
        """Summarize old conversation entries"""
        if not self._current_session or len(self._current_session.entries) < 10:
            return
        
        # Keep last 5 entries, summarize the rest
        entries = self._current_session.entries
        to_summarize = entries[:-5]
        
        # Simple extractive summary (keep key sentences)
        summary_parts = []
        for entry in to_summarize:
            if entry.role == 'user':
                # Extract first sentence or key phrase
                content = entry.content.strip()
                if content:
                    first_sentence = content.split('.')[0][:100]
                    summary_parts.append(f"User asked: {first_sentence}")
            elif entry.role == 'assistant':
                # Note actions taken
                if entry.intent:
                    summary_parts.append(f"Assistant performed: {entry.intent}")
        
        if summary_parts:
            self._current_session.context_summary = "; ".join(summary_parts[-5:])
        
        # Remove summarized entries
        self._current_session.entries = entries[-5:]
        
        # Add summary as system context
        if self._current_session.context_summary:
            summary_entry = ConversationEntry(
                role='system',
                content=f"Previous conversation summary: {self._current_session.context_summary}",
                metadata={'type': 'summary'}
            )
            self._current_session.entries.insert(0, summary_entry)
    
    def get_context(self, max_entries: Optional[int] = None) -> List[Dict]:
        """
        Get conversation context as list of entries
        
        Args:
            max_entries: Maximum number of recent entries to return
            
        Returns:
            List of conversation entries as dicts
        """
        if not self._current_session:
            return []
        
        entries = self._current_session.entries
        if max_entries:
            entries = entries[-max_entries:]
        
        return [e.to_dict() for e in entries]
    
    def get_formatted_context(self) -> str:
        """Get context formatted for LLM prompt"""
        if not self._current_session:
            return ""
        
        parts = []
        for entry in self._current_session.entries:
            if entry.role == 'user':
                parts.append(f"Human: {entry.content}")
            elif entry.role == 'assistant':
                parts.append(f"Assistant: {entry.content}")
            elif entry.role == 'system':
                parts.append(f"System: {entry.content}")
        
        return '\n'.join(parts)
    
    def clear_context(self):
        """Clear current conversation context"""
        if self._current_session:
            # Keep system messages, remove conversation
            self._current_session.entries = [
                e for e in self._current_session.entries 
                if e.role == 'system'
            ]
            self._current_session.context_summary = ""
            self._save_session(self._current_session)
            logger.info("Context cleared")
    
    def new_session(self):
        """Start a new session"""
        if self._current_session:
            self._save_session(self._current_session)
        self._create_new_session()
    
    def switch_session(self, session_id: str) -> bool:
        """Switch to a different session"""
        if session_id in self._sessions_cache:
            self._current_session = self._sessions_cache[session_id]
            return True
        
        # Try to load from disk
        session_file = self._get_session_file(session_id)
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    session = Session.from_dict(data)
                    self._sessions_cache[session_id] = session
                    self._current_session = session
                    return True
            except Exception as e:
                logger.error(f"Failed to load session: {e}")
        
        return False
    
    def list_sessions(self) -> List[Dict]:
        """List all available sessions"""
        sessions = []
        for session_file in self.storage_dir.glob('session_*.json'):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    session = Session.from_dict(data)
                    sessions.append({
                        'session_id': session.session_id,
                        'created_at': session.created_at,
                        'last_active': session.last_active,
                        'entry_count': len(session.entries),
                        'duration': session.get_duration()
                    })
            except Exception as e:
                logger.error(f"Failed to read session: {e}")
        
        # Sort by last active
        sessions.sort(key=lambda s: s['last_active'], reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        session_file = self._get_session_file(session_id)
        if session_file.exists():
            try:
                session_file.unlink()
                if session_id in self._sessions_cache:
                    del self._sessions_cache[session_id]
                
                # If deleting current session, create new one
                if self._current_session and self._current_session.session_id == session_id:
                    self._create_new_session()
                
                return True
            except Exception as e:
                logger.error(f"Failed to delete session: {e}")
        
        return False
    
    def get_preferences(self) -> UserPreferences:
        """Get user preferences"""
        return self._preferences
    
    def update_preferences(self, **kwargs):
        """Update user preferences"""
        for key, value in kwargs.items():
            if hasattr(self._preferences, key):
                setattr(self._preferences, key, value)
        
        self._save_preferences()
        logger.info("Preferences updated")
    
    def get_stats(self) -> Dict:
        """Get context manager statistics"""
        total_sessions = len(list(self.storage_dir.glob('session_*.json')))
        
        current_entries = 0
        current_tokens = 0
        if self._current_session:
            current_entries = len(self._current_session.entries)
            current_tokens = sum(e.estimate_tokens() for e in self._current_session.entries)
        
        return {
            'total_sessions': total_sessions,
            'current_session_id': self._current_session.session_id if self._current_session else None,
            'current_entries': current_entries,
            'current_tokens': current_tokens,
            'max_tokens': self.config['max_context_tokens'],
            'storage_dir': str(self.storage_dir)
        }
    
    def export_session(self, session_id: Optional[str] = None) -> Optional[Dict]:
        """Export session data"""
        session_id = session_id or (self._current_session.session_id if self._current_session else None)
        if not session_id:
            return None
        
        if session_id in self._sessions_cache:
            return self._sessions_cache[session_id].to_dict()
        
        session_file = self._get_session_file(session_id)
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to export session: {e}")
        
        return None
    
    def import_session(self, data: Dict) -> Optional[str]:
        """Import session data"""
        try:
            session = Session.from_dict(data)
            self._sessions_cache[session.session_id] = session
            self._save_session(session)
            return session.session_id
        except Exception as e:
            logger.error(f"Failed to import session: {e}")
            return None
