"""
Call handling and conversation tools for the Closed Claw Assistant.

This package provides tools for:
- Call detection and control
- Voice conversation handling
- Call note taking
- Greeting generation
"""

from .call_handler import CallHandler, CallState
from .call_conversation import CallConversation
from .call_notes import CallNotes
from .call_greeting import GreetingGenerator

__all__ = [
    'CallHandler',
    'CallState',
    'CallConversation',
    'CallNotes',
    'GreetingGenerator',
]
