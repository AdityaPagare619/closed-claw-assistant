#!/usr/bin/env python3
"""
Human-Like Conversation Engine
Makes AI indistinguishable from human on phone calls
"""

import asyncio
import random
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    caller_number: str
    caller_name: Optional[str]
    start_time: datetime
    message_history: List[Dict]
    context: Dict


class HumanLikeConversationEngine:
    """
    Creates human-like phone conversations using Sarvam
    Natural speech patterns, emotional intelligence, context awareness
    """
    
    def __init__(self, brain, voice_system, learning_engine):
        self.brain = brain
        self.voice = voice_system
        self.learning = learning_engine
        
        # Human conversation elements
        self.fillers = {
            'hi': ['umm...', 'acha...', 'dekho...'],
            'mr': ['hmm...', 'bagha...'],
            'en': ['um...', 'so...', 'well...']
        }
        
        self.acknowledgments = {
            'hi': ['haan ji', 'theek hai', 'sahi'],
            'mr': ['ho', 'barobar'],
            'en': ['I see', 'right', 'understood']
        }
        
        logger.info("🎭 Human Conversation Engine initialized")
    
    async def start_conversation(self, caller_number: str, 
                                 caller_name: Optional[str] = None) -> str:
        """Start natural, human-like conversation"""
        state = ConversationState(
            caller_number=caller_number,
            caller_name=caller_name,
            start_time=datetime.now(),
            message_history=[],
            context={'language': 'hi'}
        )
        
        # Generate natural greeting
        greeting = await self._generate_natural_greeting(state)
        natural_greeting = self._add_human_elements(greeting, 'hi')
        
        # Speak with Sarvam voice
        await self.voice.speak(
            natural_greeting, 
            language='hi-IN',
            emotion='friendly'
        )
        
        return state
    
    async def respond_to_caller(self, state: ConversationState, 
                                caller_message: str) -> str:
        """Generate human-like response"""
        lang = state.context.get('language', 'hi')
        
        # Check for confidential requests
        if self._is_confidential_request(caller_message):
            response = await self._handle_confidential_request(state)
        else:
            # Generate intelligent response
            prompt = self._build_conversation_prompt(state, caller_message)
            response = await self.brain.generate(prompt, max_tokens=100)
        
        # Make it sound human
        natural_response = self._add_human_elements(response, lang)
        
        # Speak with emotion
        await self.voice.speak(
            natural_response,
            language=self._map_language(lang),
            emotion='neutral'
        )
        
        return response
    
    async def _generate_natural_greeting(self, state: ConversationState) -> str:
        """Generate natural greeting (not robotic)"""
        caller_name = state.caller_name
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            time_greeting = "good morning"
        elif 12 <= hour < 17:
            time_greeting = "good afternoon"
        elif 17 <= hour < 21:
            time_greeting = "good evening"
        else:
            time_greeting = "hello"
        
        if caller_name:
            return f"Namaste {caller_name}, {time_greeting}. Main user ke behalf pe bol raha hoon. Woh abhi busy hain. Main aapki kya madad kar sakta hoon?"
        else:
            return f"Namaste, {time_greeting}. Main user ka assistant hoon. Woh abhi available nahi hain. Kya main message le sakta hoon?"
    
    def _add_human_elements(self, text: str, lang: str) -> str:
        """Add human-like pauses and fillers"""
        # Add filler at beginning
        if random.random() < 0.3:
            filler = random.choice(self.fillers.get(lang, self.fillers['en']))
            text = f"{filler} {text}"
        
        # Add natural pauses
        if random.random() < 0.3:
            text = text.replace(', ', ', ... ', 1)
        
        return text
    
    def _is_confidential_request(self, message: str) -> bool:
        """Check if asking for confidential info"""
        patterns = ['where is', 'location', 'address', 'phone number', 
                   'email', 'when will', 'schedule', 'busy', 'password']
        return any(p in message.lower() for p in patterns)
    
    async def _handle_confidential_request(self, state: ConversationState) -> str:
        """Handle confidential requests gracefully"""
        return "Main yeh information share nahi kar sakta. User jaldi aapko call karenge. Koi aur message?"
    
    def _build_conversation_prompt(self, state: ConversationState, 
                                  caller_message: str) -> str:
        """Build prompt for Sarvam brain"""
        history = state.message_history[-3:]
        context_str = "\n".join([
            f"{'Caller' if m['role'] == 'caller' else 'Assistant'}: {m['content']}"
            for m in history
        ])
        
        return f"""You are a helpful assistant answering a phone call. Be natural, not robotic.

Conversation:
{context_str}

Caller: "{caller_message}"

Respond briefly and naturally:"""
    
    def _map_language(self, lang_code: str) -> str:
        mapping = {'hi': 'hi-IN', 'mr': 'mr-IN', 'en': 'en-IN'}
        return mapping.get(lang_code, 'hi-IN')
    
    async def end_conversation(self, state: ConversationState) -> str:
        """End conversation naturally"""
        lang = state.context.get('language', 'hi')
        
        closing = "Theek hai, main sab note kar liya hai. User jaldi call karenge. Dhanyawad! Namaste!"
        
        await self.voice.speak(
            closing,
            language='hi-IN',
            emotion='friendly'
        )
        
        return closing
