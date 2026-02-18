"""
Closed Claw Assistant - Brain Module
AI Intelligence Layer with Sarvam-1 2B and Voice Capabilities
"""

from .sarvam_brain import SarvamBrain, LLMError
from .voice_system import VoiceSystem, VoiceError
from .intent_parser import IntentParser, Intent
from .context_manager import ContextManager, Session

__all__ = [
    'SarvamBrain',
    'LLMError',
    'VoiceSystem',
    'VoiceError',
    'IntentParser',
    'Intent',
    'ContextManager',
    'Session',
]

__version__ = '1.0.0'
