"""
Closed Claw Assistant - Agent Module
Core agent functionality for the AI assistant.
"""

from .daemon import AgentDaemon
from .state_manager import StateManager, AgentState
from .memory_manager import MemoryManager
from .event_loop import EventLoop

__all__ = [
    "AgentDaemon",
    "StateManager",
    "AgentState",
    "MemoryManager",
    "EventLoop",
]
