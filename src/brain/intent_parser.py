"""
Intent Parser Module
Parse user commands and map to actions
Supports code-switching: Hinglish, Manglish
"""

import re
import json
import logging
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels for actions"""
    NONE = 0
    LOW = 1      # Read-only actions
    MEDIUM = 2   # Modify data
    HIGH = 3     # System-level actions
    CRITICAL = 4 # Security-critical


class IntentType(Enum):
    """Intent types"""
    # Communication
    CALL_PICKUP = "call_pickup"
    CALL_END = "call_end"
    CALL_MUTE = "call_mute"
    CALL_SPEAKER = "call_speaker"
    
    # Messaging
    WHATSAPP_READ = "whatsapp_read"
    WHATSAPP_SEND = "whatsapp_send"
    SMS_READ = "sms_read"
    SMS_SEND = "sms_send"
    EMAIL_READ = "email_read"
    EMAIL_SEND = "email_send"
    
    # Calendar
    CALENDAR_ADD = "calendar_add"
    CALENDAR_VIEW = "calendar_view"
    CALENDAR_DELETE = "calendar_delete"
    REMINDER_SET = "reminder_set"
    ALARM_SET = "alarm_set"
    
    # Device
    WIFI_TOGGLE = "wifi_toggle"
    BLUETOOTH_TOGGLE = "bluetooth_toggle"
    TORCH_TOGGLE = "torch_toggle"
    VOLUME_SET = "volume_set"
    BRIGHTNESS_SET = "brightness_set"
    BATTERY_STATUS = "battery_status"
    
    # Apps
    APP_OPEN = "app_open"
    APP_CLOSE = "app_close"
    PLAY_MUSIC = "play_music"
    TAKE_PHOTO = "take_photo"
    
    # Information
    TIME_CHECK = "time_check"
    WEATHER_CHECK = "weather_check"
    NEWS_READ = "news_read"
    
    # Assistant
    GREETING = "greeting"
    GOODBYE = "goodbye"
    THANKS = "thanks"
    HELP = "help"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    REPEAT = "repeat"
    
    # Fallback
    UNKNOWN = "unknown"
    CONVERSATION = "conversation"


@dataclass
class Intent:
    """Parsed intent"""
    type: IntentType
    confidence: float
    params: Dict[str, Any]
    permission_level: PermissionLevel
    raw_text: str
    language: str


class IntentParser:
    """
    Intent Parser with support for code-switching
    Handles Hinglish (Hindi-English) and Manglish (Marathi-English)
    """
    
    # Permission mapping
    PERMISSION_MAP = {
        IntentType.CALL_PICKUP: PermissionLevel.HIGH,
        IntentType.CALL_END: PermissionLevel.MEDIUM,
        IntentType.CALL_MUTE: PermissionLevel.LOW,
        IntentType.CALL_SPEAKER: PermissionLevel.LOW,
        IntentType.WHATSAPP_READ: PermissionLevel.LOW,
        IntentType.WHATSAPP_SEND: PermissionLevel.MEDIUM,
        IntentType.SMS_READ: PermissionLevel.LOW,
        IntentType.SMS_SEND: PermissionLevel.MEDIUM,
        IntentType.EMAIL_READ: PermissionLevel.LOW,
        IntentType.EMAIL_SEND: PermissionLevel.MEDIUM,
        IntentType.CALENDAR_ADD: PermissionLevel.MEDIUM,
        IntentType.CALENDAR_VIEW: PermissionLevel.LOW,
        IntentType.CALENDAR_DELETE: PermissionLevel.MEDIUM,
        IntentType.REMINDER_SET: PermissionLevel.MEDIUM,
        IntentType.ALARM_SET: PermissionLevel.MEDIUM,
        IntentType.WIFI_TOGGLE: PermissionLevel.MEDIUM,
        IntentType.BLUETOOTH_TOGGLE: PermissionLevel.MEDIUM,
        IntentType.TORCH_TOGGLE: PermissionLevel.LOW,
        IntentType.VOLUME_SET: PermissionLevel.LOW,
        IntentType.BRIGHTNESS_SET: PermissionLevel.LOW,
        IntentType.BATTERY_STATUS: PermissionLevel.NONE,
        IntentType.APP_OPEN: PermissionLevel.LOW,
        IntentType.APP_CLOSE: PermissionLevel.MEDIUM,
        IntentType.PLAY_MUSIC: PermissionLevel.LOW,
        IntentType.TAKE_PHOTO: PermissionLevel.MEDIUM,
        IntentType.TIME_CHECK: PermissionLevel.NONE,
        IntentType.WEATHER_CHECK: PermissionLevel.LOW,
        IntentType.NEWS_READ: PermissionLevel.LOW,
        IntentType.GREETING: PermissionLevel.NONE,
        IntentType.GOODBYE: PermissionLevel.NONE,
        IntentType.THANKS: PermissionLevel.NONE,
        IntentType.HELP: PermissionLevel.NONE,
        IntentType.CONFIRM: PermissionLevel.NONE,
        IntentType.CANCEL: PermissionLevel.NONE,
        IntentType.REPEAT: PermissionLevel.NONE,
        IntentType.UNKNOWN: PermissionLevel.NONE,
        IntentType.CONVERSATION: PermissionLevel.NONE,
    }
    
    # Intent patterns - English
    ENGLISH_PATTERNS = {
        IntentType.CALL_PICKUP: [
            r'\bpick up\b', r'\banswer\b', r'\baccept call\b',
            r'\bhello\b.*\bcall\b', r'\btake call\b',
        ],
        IntentType.CALL_END: [
            r'\bend call\b', r'\bhang up\b', r'\bcut call\b',
            r'\bdisconnect\b', r'\bstop call\b',
        ],
        IntentType.WHATSAPP_READ: [
            r'\bread whatsapp\b', r'\bwhatsapp messages\b',
            r'\bcheck whatsapp\b', r'\bnew messages\b',
        ],
        IntentType.WHATSAPP_SEND: [
            r'\bsend whatsapp\b', r'\bwhatsapp .*\bto\b',
            r'\bmessage .*\bon whatsapp\b',
        ],
        IntentType.CALENDAR_ADD: [
            r'\badd event\b', r'\bschedule\b', r'\bcreate meeting\b',
            r'\bset reminder\b.*\bcalendar\b', r'\bbook appointment\b',
        ],
        IntentType.CALENDAR_VIEW: [
            r'\bshow calendar\b', r'\bview schedule\b',
            r'\bwhat.*\btoday\b', r'\bmy events\b',
        ],
        IntentType.TIME_CHECK: [
            r'\bwhat time\b', r'\bcurrent time\b',
            r'\btime is it\b', r'\bclock\b',
        ],
        IntentType.TORCH_TOGGLE: [
            r'\btorch\b', r'\bflashlight\b', r'\bflash\b',
            r'\bturn on light\b', r'\bturn off light\b',
        ],
        IntentType.GREETING: [
            r'^hi\b', r'^hello\b', r'^hey\b', r'^good morning\b',
            r'^good afternoon\b', r'^good evening\b', r'^namaste\b',
        ],
        IntentType.GOODBYE: [
            r'\bbye\b', r'\bgoodbye\b', r'\bsee you\b',
            r'\btake care\b', r'\bcatch you later\b',
        ],
        IntentType.THANKS: [
            r'\bthank\b', r'\bthanks\b', r'\bthank you\b',
            r'\bshukriya\b', r'\bdhanyawad\b',
        ],
        IntentType.HELP: [
            r'\bhelp\b', r'\bassist\b', r'\bwhat can you do\b',
            r'\bcommands\b', r'\bhow to\b',
        ],
    }
    
    # Intent patterns - Hinglish (Hindi written in English)
    HINGLISH_PATTERNS = {
        IntentType.CALL_PICKUP: [
            r'\bcall uthao\b', r'\bcall pick\b', r'\bphone uthao\b',
            r'\bcall receive\b', r'\bhello bolo\b',
        ],
        IntentType.CALL_END: [
            r'\bcall cut\b', r'\bcall band\b', r'\bphone band\b',
            r'\bcall khatam\b', r'\bcall end\b',
        ],
        IntentType.WHATSAPP_READ: [
            r'\bwhatsapp padho\b', r'\bmessages padho\b',
            r'\bwhatsapp check\b', r'\bkya messages\b',
        ],
        IntentType.WHATSAPP_SEND: [
            r'\bwhatsapp bhejo\b', r'\bmessage bhejo\b',
            r'\bwhatsapp karo\b', r'\blikh do\b',
        ],
        IntentType.CALENDAR_ADD: [
            r'\bevent add\b', r'\bmeeting fix\b',
            r'\breminder lagao\b', r'\bschedule karo\b',
        ],
        IntentType.CALENDAR_VIEW: [
            r'\bcalendar dikhao\b', r'\bschedule dikhao\b',
            r'\baaj kya\b', r'\bmere events\b',
        ],
        IntentType.TIME_CHECK: [
            r'\btime kya\b', r'\bkitna time\b',
            r'\bghadi me kya\b', r'\bsamay\b',
        ],
        IntentType.TORCH_TOGGLE: [
            r'\btorch on\b', r'\btorch off\b',
            r'\bflash on\b', r'\bflash off\b',
            r'\blight\b',
        ],
        IntentType.GREETING: [
            r'\bnamaste\b', r'\bnamaskar\b', r'\bkya haal\b',
            r'\bkaise ho\b', r'\bsuprabhat\b',
        ],
        IntentType.GOODBYE: [
            r'\balvida\b', r'\bphir milenge\b',
            r'\bbye\b', r'\bja raha\b',
        ],
        IntentType.THANKS: [
            r'\bshukriya\b', r'\bdhanyawad\b',
            r'\bthank you\b', r'\bmeharbani\b',
        ],
    }
    
    # Intent patterns - Manglish (Marathi written in English)
    MANGLISH_PATTERNS = {
        IntentType.CALL_PICKUP: [
            r'\bcall ghe\b', r'\bcall uthva\b',
            r'\bphone ghe\b', r'\bcall receive\b',
        ],
        IntentType.CALL_END: [
            r'\bcall band\b', r'\bcall samapt\b',
            r'\bcall cut\b', r'\bphone thev\b',
        ],
        IntentType.GREETING: [
            r'\bnamaskar\b', r'\bnamsakar\b',
            r'\bkaay chal\b', r'\bkashe ahat\b',
        ],
        IntentType.GOODBYE: [
            r'\bbye\b', r'\bpunha bhetu\b',
            r'\bjate\b', r'\bjaychay\b',
        ],
    }
    
    def __init__(self):
        self._compiled_patterns: Dict[IntentType, List[re.Pattern]] = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile all regex patterns"""
        all_patterns = [
            ("en", self.ENGLISH_PATTERNS),
            ("hi-en", self.HINGLISH_PATTERNS),
            ("mr-en", self.MANGLISH_PATTERNS),
        ]
        
        for lang, patterns in all_patterns:
            for intent_type, regex_list in patterns.items():
                if intent_type not in self._compiled_patterns:
                    self._compiled_patterns[intent_type] = []
                
                for regex in regex_list:
                    try:
                        pattern = re.compile(regex, re.IGNORECASE)
                        self._compiled_patterns[intent_type].append(pattern)
                    except re.error as e:
                        logger.warning(f"Invalid regex pattern: {regex}, error: {e}")
    
    def parse(self, text: str, context: Optional[Dict] = None) -> Intent:
        """
        Parse text and extract intent
        
        Args:
            text: User input text
            context: Optional context from previous interactions
            
        Returns:
            Intent object with type, confidence, params
        """
        if not text:
            return self._create_intent(IntentType.UNKNOWN, 0.0, {}, text)
        
        text_lower = text.lower().strip()
        context = context or {}
        
        # Try to match patterns
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        
        for intent_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    confidence = self._calculate_confidence(pattern, text_lower)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent_type
        
        # Extract parameters
        params = self._extract_params(best_intent, text)
        
        # Detect language
        language = self._detect_language(text)
        
        # Handle conversation if no intent found
        if best_intent == IntentType.UNKNOWN:
            if len(text.split()) > 3:
                best_intent = IntentType.CONVERSATION
                best_confidence = 0.5
        
        return self._create_intent(best_intent, best_confidence, params, text, language)
    
    def _calculate_confidence(self, pattern: re.Pattern, text: str) -> float:
        """Calculate confidence score for a match"""
        match = pattern.search(text)
        if not match:
            return 0.0
        
        # Base confidence
        confidence = 0.7
        
        # Boost if pattern matches at start
        if match.start() == 0:
            confidence += 0.1
        
        # Boost for exact matches
        if match.group() == text:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _extract_params(self, intent_type: IntentType, text: str) -> Dict[str, Any]:
        """Extract parameters from text based on intent type"""
        params = {}
        text_lower = text.lower()
        
        # Contact extraction
        contact_patterns = [
            r'\bto\s+(\w+)',
            r'\bfrom\s+(\w+)',
            r'\bsend\s+to\s+(\w+)',
            r'\bmessage\s+(\w+)',
        ]
        
        # Time extraction
        time_patterns = [
            r'\bat\s+(\d{1,2}:\d{2})',
            r'\bat\s+(\d{1,2})\s*(am|pm)?',
            r'\bin\s+(\d+)\s+minutes?',
            r'\bin\s+(\d+)\s+hours?',
        ]
        
        # Date extraction
        date_patterns = [
            r'\bon\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'\bon\s+(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)',
            r'\btomorrow\b',
            r'\btoday\b',
        ]
        
        # Extract based on intent
        if intent_type in [IntentType.WHATSAPP_SEND, IntentType.SMS_SEND, IntentType.CALL_PICKUP]:
            for pattern in contact_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    params['contact'] = match.group(1).capitalize()
                    break
        
        if intent_type in [IntentType.CALENDAR_ADD, IntentType.REMINDER_SET, IntentType.ALARM_SET]:
            for pattern in time_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    params['time'] = match.group(0)
                    break
            
            for pattern in date_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    params['date'] = match.group(0)
                    break
        
        if intent_type == IntentType.APP_OPEN:
            app_match = re.search(r'\bopen\s+(\w+)\b', text_lower)
            if app_match:
                params['app_name'] = app_match.group(1)
        
        # Extract raw message content for messaging intents
        if intent_type in [IntentType.WHATSAPP_SEND, IntentType.SMS_SEND]:
            message_match = re.search(r'\bsaying\s+(.+)|\bthat\s+(.+)|\bmessage\s+(.+?)\sto', text_lower)
            if message_match:
                params['message'] = next((g for g in message_match.groups() if g), '')
        
        return params
    
    def _detect_language(self, text: str) -> str:
        """Detect language of input text"""
        text_lower = text.lower()
        
        # Check for Hinglish indicators
        hinglish_words = ['kya', 'hai', 'kar', 'do', 'padho', 'bhejo', 'dikhao', 'kaise', 'ho', 'haal']
        if any(word in text_lower for word in hinglish_words):
            return 'hi-en'
        
        # Check for Manglish indicators
        manglish_words = ['kaay', 'kashe', 'ahat', 'ghe', 'thev', 'samapt', 'punha', 'bhetu']
        if any(word in text_lower for word in manglish_words):
            return 'mr-en'
        
        # Check for pure Hindi/Marathi (Devanagari)
        devanagari_range = range(0x0900, 0x097F)
        if any(ord(c) in devanagari_range for c in text):
            return 'hi' if 'है' in text or 'क्या' in text else 'mr'
        
        return 'en'
    
    def _create_intent(
        self,
        intent_type: IntentType,
        confidence: float,
        params: Dict[str, Any],
        raw_text: str,
        language: str = 'en'
    ) -> Intent:
        """Create Intent object"""
        permission = self.PERMISSION_MAP.get(intent_type, PermissionLevel.NONE)
        
        return Intent(
            type=intent_type,
            confidence=confidence,
            params=params,
            permission_level=permission,
            raw_text=raw_text,
            language=language
        )
    
    def batch_parse(self, texts: List[str]) -> List[Intent]:
        """Parse multiple texts"""
        return [self.parse(text) for text in texts]
    
    def get_supported_intents(self) -> List[str]:
        """Get list of supported intent types"""
        return [intent.value for intent in IntentType]
    
    def get_intent_description(self, intent_type: IntentType) -> str:
        """Get human-readable description of intent"""
        descriptions = {
            IntentType.CALL_PICKUP: "Answer incoming call",
            IntentType.CALL_END: "End current call",
            IntentType.WHATSAPP_READ: "Read WhatsApp messages",
            IntentType.WHATSAPP_SEND: "Send WhatsApp message",
            IntentType.CALENDAR_ADD: "Add calendar event",
            IntentType.TIME_CHECK: "Check current time",
            IntentType.TORCH_TOGGLE: "Toggle flashlight",
            IntentType.GREETING: "Greeting",
            IntentType.GOODBYE: "Goodbye",
            IntentType.HELP: "Request help",
        }
        return descriptions.get(intent_type, "Unknown action")
