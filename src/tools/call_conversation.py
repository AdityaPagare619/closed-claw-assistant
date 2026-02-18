"""
Voice conversation handler for phone calls.
Manages the flow: greeting -> listen -> respond -> speak.
"""

import asyncio
import json
import time
import re
from typing import Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .call_handler import CallHandler, CallState, CallInfo
from .call_greeting import GreetingGenerator


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""
    speaker: str  # 'assistant' or 'caller'
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: int = 0


@dataclass
class ConversationContext:
    """Context for the ongoing conversation."""
    caller_number: Optional[str] = None
    caller_name: Optional[str] = None
    start_time: Optional[datetime] = None
    turns: List[ConversationTurn] = field(default_factory=list)
    blocked_attempts: List[str] = field(default_factory=list)
    
    def add_turn(self, speaker: str, text: str, duration_ms: int = 0):
        """Add a conversation turn."""
        self.turns.append(ConversationTurn(speaker, text, duration_ms=duration_ms))
    
    def get_transcript(self) -> str:
        """Get full conversation transcript."""
        return "\n".join([
            f"{turn.speaker}: {turn.text}"
            for turn in self.turns
        ])


class CallConversation:
    """
    Manages voice conversation during an active call.
    
    Features:
    - Voice greeting on pickup
    - Speech-to-text for caller input
    - LLM response generation
    - Text-to-speech for responses
    - Hangup detection
    - Blocks confidential information sharing
    """
    
    # Patterns that indicate confidential information requests
    CONFIDENTIAL_PATTERNS = [
        r'where are you',
        r'your location',
        r'where (are you|do you live)',
        r'your address',
        r'when (are you|will you be)',
        r'your schedule',
        r'your plans',
        r'what (time|when)',
        r'are you home',
        r'are you at',
        r'personal',
        r'private',
        r'password',
        r'otp',
        r'pin',
        r'bank',
        r'account',
        r'credit card',
        r'debit card',
        r'social security',
        r'aadhar',
        r'pan',
    ]
    
    # Blocked topics to never discuss
    BLOCKED_TOPICS = [
        'location', 'address', 'whereabouts',
        'schedule', 'calendar', 'plans',
        'password', 'pin', 'otp', 'secret',
        'bank account', 'card number',
        'personal information', 'private',
    ]
    
    def __init__(
        self,
        call_handler: CallHandler,
        greeting_generator: Optional[GreetingGenerator] = None,
        llm_client=None,
        stt_engine=None,
        tts_engine=None
    ):
        """
        Initialize conversation handler.
        
        Args:
            call_handler: Active call handler instance
            greeting_generator: Greeting generator instance
            llm_client: LLM client for response generation
            stt_engine: Speech-to-text engine
            tts_engine: Text-to-speech engine
        """
        self.call_handler = call_handler
        self.greeting_generator = greeting_generator or GreetingGenerator()
        self.llm_client = llm_client
        self.stt_engine = stt_engine
        self.tts_engine = tts_engine
        
        self.context: Optional[ConversationContext] = None
        self.is_active = False
        self.max_silence_seconds = 5
        self.response_timeout = 2.0  # Target response time
        
        self._hangup_callbacks: List[Callable[[ConversationContext], None]] = []
        self._error_count = 0
        self._max_errors = 3
    
    def _check_confidential_request(self, text: str) -> tuple[bool, str]:
        """
        Check if request asks for confidential information.
        
        Returns:
            (is_confidential, safe_response)
        """
        text_lower = text.lower()
        
        for pattern in self.CONFIDENTIAL_PATTERNS:
            if re.search(pattern, text_lower):
                logger.warning(f"Confidential info request detected: {pattern}")
                return True, self._get_blocked_response()
        
        # Check for blocked topics
        for topic in self.BLOCKED_TOPICS:
            if topic in text_lower:
                logger.warning(f"Blocked topic detected: {topic}")
                return True, self._get_blocked_response()
        
        return False, ""
    
    def _get_blocked_response(self) -> str:
        """Get response for blocked confidential requests."""
        responses = [
            "I apologize, but I'm not authorized to share that information.",
            "I'm sorry, I cannot discuss personal or confidential matters over the phone.",
            "For privacy reasons, I'm unable to provide that information. Please contact directly if needed.",
        ]
        import random
        return random.choice(responses)
    
    async def _speak(self, text: str) -> bool:
        """
        Speak text using TTS engine.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.tts_engine:
                start_time = time.time()
                await self.tts_engine.speak(text)
                elapsed = (time.time() - start_time) * 1000
                logger.info(f"TTS completed in {elapsed:.0f}ms")
                return True
            else:
                # Fallback: use termux-tts-speak
                import subprocess
                subprocess.run(
                    ['termux-tts-speak', text],
                    capture_output=True,
                    timeout=30
                )
                return True
        except Exception as e:
            logger.error(f"TTS error: {e}")
            self._error_count += 1
            return False
    
    async def _listen(self, timeout: int = 10) -> Optional[str]:
        """
        Listen to caller and convert speech to text.
        
        Args:
            timeout: Maximum seconds to listen
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            if self.stt_engine:
                start_time = time.time()
                text = await self.stt_engine.listen(timeout=timeout)
                elapsed = (time.time() - start_time) * 1000
                
                if text:
                    logger.info(f"STT completed in {elapsed:.0f}ms: {text}")
                    return text
            else:
                # Fallback: use termux-speech-to-text
                import subprocess
                result = subprocess.run(
                    ['termux-speech-to-text', '-t', str(timeout)],
                    capture_output=True,
                    text=True,
                    timeout=timeout + 5
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                    
        except Exception as e:
            logger.error(f"STT error: {e}")
            self._error_count += 1
        
        return None
    
    async def _generate_response(self, caller_input: str) -> str:
        """
        Generate response using LLM.
        
        Args:
            caller_input: Text from caller
            
        Returns:
            Generated response
        """
        start_time = time.time()
        
        # Check for confidential request first
        is_confidential, blocked_response = self._check_confidential_request(caller_input)
        if is_confidential:
            if self.context:
                self.context.blocked_attempts.append(caller_input)
            return blocked_response
        
        # Use LLM if available
        if self.llm_client:
            try:
                system_prompt = """You are a helpful phone assistant. You are speaking on behalf of someone who is unavailable.
                Rules:
                - Be concise (max 2 sentences)
                - Be polite and professional
                - Do NOT share any personal, location, or schedule information
                - Do NOT share passwords, financial info, or private details
                - If unsure, ask caller to leave a message or call back later
                - Respond in the same language as the caller"""
                
                response = await self.llm_client.generate(
                    system=system_prompt,
                    prompt=caller_input,
                    max_tokens=100,
                    temperature=0.7
                )
                
                elapsed = time.time() - start_time
                logger.info(f"LLM response generated in {elapsed:.2f}s")
                
                # Verify response doesn't contain blocked info
                if self._check_confidential_request(response)[0]:
                    return "I'm not sure about that. Could you please leave a message?"
                
                return response
                
            except Exception as e:
                logger.error(f"LLM error: {e}")
                self._error_count += 1
        
        # Fallback responses
        fallback_responses = [
            "I'm currently unavailable. Please leave a message.",
            "I can't take your call right now. Please call back later.",
            "I'm assisting someone else. Can I take a message?",
        ]
        import random
        return random.choice(fallback_responses)
    
    def _check_hangup(self) -> bool:
        """Check if call has ended."""
        call_info = self.call_handler.get_call_state()
        return call_info.state == CallState.IDLE
    
    def on_hangup(self, callback: Callable[[ConversationContext], None]):
        """Register callback for when call ends."""
        self._hangup_callbacks.append(callback)
    
    def _notify_hangup(self):
        """Notify all hangup callbacks."""
        if self.context:
            for callback in self._hangup_callbacks:
                try:
                    callback(self.context)
                except Exception as e:
                    logger.error(f"Hangup callback error: {e}")
    
    async def start_conversation(self, call_info: CallInfo):
        """
        Start the conversation flow when call is answered.
        
        Args:
            call_info: Information about the current call
        """
        self.is_active = True
        self._error_count = 0
        
        # Initialize context
        self.context = ConversationContext(
            caller_number=call_info.phone_number,
            start_time=datetime.now()
        )
        
        logger.info(f"Starting conversation with {call_info.phone_number}")
        
        # Generate and speak greeting
        greeting = self.greeting_generator.generate(
            caller_number=call_info.phone_number,
            caller_name=call_info.display_name
        )
        
        if not await self._speak(greeting):
            logger.error("Failed to speak greeting - rejecting call")
            self.call_handler.reject_call()
            return
        
        self.context.add_turn("assistant", greeting)
        
        # Main conversation loop
        silence_count = 0
        
        while self.is_active and self._error_count < self._max_errors:
            # Check for hangup
            if self._check_hangup():
                logger.info("Call ended detected")
                break
            
            # Listen for caller input
            caller_input = await self._listen(timeout=10)
            
            if not caller_input:
                silence_count += 1
                if silence_count >= 2:
                    # Try closing message
                    closing = "I didn't hear anything. Please call back later. Goodbye!"
                    await self._speak(closing)
                    self.context.add_turn("assistant", closing)
                    break
                continue
            
            silence_count = 0
            self.context.add_turn("caller", caller_input)
            
            # Generate and speak response
            response = await self._generate_response(caller_input)
            
            if await self._speak(response):
                self.context.add_turn("assistant", response)
            else:
                logger.error("TTS failed - ending conversation")
                break
            
            # Brief pause before next listen
            await asyncio.sleep(0.5)
        
        # Conversation ended
        self.is_active = False
        self._notify_hangup()
        logger.info("Conversation ended")
    
    def stop(self):
        """Stop the conversation."""
        self.is_active = False
        logger.info("Conversation stopped")


async def test_conversation():
    """Test the conversation handler."""
    handler = CallHandler(pickup_delay=20)
    conversation = CallConversation(handler)
    
    # Mock call info
    call_info = CallInfo(
        phone_number="+1234567890",
        state=CallState.OFFHOOK
    )
    
    def on_hangup(ctx):
        print("\n=== Call Transcript ===")
        print(ctx.get_transcript())
    
    conversation.on_hangup(on_hangup)
    await conversation.start_conversation(call_info)


if __name__ == "__main__":
    asyncio.run(test_conversation())
