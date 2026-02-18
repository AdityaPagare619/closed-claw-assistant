"""
Greeting generator for phone calls.
Provides personalized and context-aware greetings.
"""

from typing import Optional, Dict, List
from datetime import datetime
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GreetingGenerator:
    """
    Generates greetings for phone calls.
    
    Features:
    - Personalized greetings for known contacts
    - Professional greetings for unknown numbers
    - Multi-language support (English, Hindi, Marathi)
    - Time-of-day aware greetings
    """
    
    # Known contacts database (can be extended)
    KNOWN_CONTACTS: Dict[str, Dict] = {
        # Example: "+1234567890": {"name": "John", "relation": "friend", "language": "en"}
    }
    
    # Greeting templates by language
    GREETINGS = {
        'en': {
            'morning': [
                "Good morning! {name} is currently unavailable. How may I help you?",
                "Hello, good morning! {name} can't take your call right now.",
            ],
            'afternoon': [
                "Good afternoon! {name} is busy at the moment. How can I assist?",
                "Hello! {name} isn't available right now. What can I do for you?",
            ],
            'evening': [
                "Good evening! {name} is unavailable. How may I help?",
                "Hello, good evening! {name} can't answer right now.",
            ],
            'night': [
                "Hello! {name} is resting now. Is this urgent?",
                "Good evening! {name} is unavailable at this hour.",
            ],
            'unknown': [
                "Hello! You've reached {name}. I'm unavailable right now. Please leave a message.",
                "Hi! {name} can't take your call. How can I help?",
            ],
        },
        'hi': {
            'morning': [
                "Namaste! {name} abhi uplabdh nahi hain. Main kya madad kar sakta hoon?",
                "Subah pranam! {name} abhi call nahi utha sakte.",
            ],
            'afternoon': [
                "Namaste! {name} abhi vyast hain. Main aapki kya madad karoon?",
            ],
            'evening': [
                "Namaste! {name} abhi uplabdh nahi hain.",
            ],
            'night': [
                "Namaste! {name} abhi aaram kar rahe hain.",
            ],
            'unknown': [
                "Namaste! {name} ka phone hai. Main unki madad se baat kar raha hoon.",
            ],
        },
        'mr': {
            'morning': [
                "Namaskar! {name} yaa veli upalabdh nahi. Mein kay madat karu shakto?",
            ],
            'afternoon': [
                "Namaskar! {name} vyast ahet. Mein aapli kay madat karu?",
            ],
            'evening': [
                "Namaskar! {name} upalabdh nahi ahet.",
            ],
            'night': [
                "Namaskar! {name} vishranti gheta ahet.",
            ],
            'unknown': [
                "Namaskar! {name} che phone aahe. Mein tyanchya vatine bolato.",
            ],
        }
    }
    
    # Professional greetings for unknown callers
    PROFESSIONAL_GREETINGS = {
        'en': [
            "Hello! You've reached {owner_name}. I'm unavailable right now. Please leave your name and message.",
            "Hello! This is {owner_name}'s assistant. They're unavailable. How can I help?",
            "Hi there! {owner_name} can't take your call. Would you like to leave a message?",
        ],
        'hi': [
            "Namaste! Aapne {owner_name} ka phone lagaya hai. Woh abhi uplabdh nahi hain. Kripya sandesh chhodiye.",
            "Namaste! Main {owner_name} ki madad se bol raha hoon. Woh abhi call nahi utha sakte.",
        ],
        'mr': [
            "Namaskar! Aap {owner_name} yanna call kelaa aahe. Te upalabdh nahi. Kripaya sandesh soda.",
            "Namaskar! Mein {owner_name} che sahayyane bolato. Te yaa veli call gheu shakat nahi.",
        ]
    }
    
    def __init__(self, owner_name: str = "Aditya", default_language: str = "en"):
        """
        Initialize greeting generator.
        
        Args:
            owner_name: Name of the phone owner
            default_language: Default language code (en/hi/mr)
        """
        self.owner_name = owner_name
        self.default_language = default_language
        
        logger.info(f"GreetingGenerator initialized for {owner_name}")
    
    def _get_time_of_day(self) -> str:
        """Determine current time of day."""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
    
    def _detect_language(self, text: Optional[str] = None) -> str:
        """
        Detect language from context or use default.
        
        Args:
            text: Optional text to analyze for language detection
            
        Returns:
            Language code (en/hi/mr)
        """
        if text:
            # Simple detection based on common words
            text_lower = text.lower()
            
            hindi_words = ['namaste', 'hai', 'kaise', 'aap', 'main', 'hoon']
            marathi_words = ['namaskar', 'ahe', 'kase', 'tumhi', 'mi', 'aahe']
            
            hindi_score = sum(1 for w in hindi_words if w in text_lower)
            marathi_score = sum(1 for w in marathi_words if w in text_lower)
            
            if hindi_score > 0:
                return 'hi'
            elif marathi_score > 0:
                return 'mr'
        
        return self.default_language
    
    def _get_contact_info(self, phone_number: str) -> Optional[Dict]:
        """Get contact info for a known number."""
        return self.KNOWN_CONTACTS.get(phone_number)
    
    def add_contact(self, phone_number: str, name: str, relation: str = "contact", language: str = "en"):
        """
        Add a known contact.
        
        Args:
            phone_number: Phone number with country code
            name: Contact name
            relation: Relationship type
            language: Preferred language code
        """
        self.KNOWN_CONTACTS[phone_number] = {
            'name': name,
            'relation': relation,
            'language': language
        }
        logger.info(f"Added contact: {name} ({phone_number})")
    
    def generate(
        self,
        caller_number: Optional[str] = None,
        caller_name: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """
        Generate appropriate greeting.
        
        Args:
            caller_number: Caller's phone number
            caller_name: Caller's name (if known)
            language: Language code override
            
        Returns:
            Generated greeting string
        """
        time_of_day = self._get_time_of_day()
        
        # Check if known contact
        contact_info = None
        if caller_number:
            contact_info = self._get_contact_info(caller_number)
        
        # Determine language
        if language:
            lang = language
        elif contact_info:
            lang = contact_info.get('language', self.default_language)
        else:
            lang = self.default_language
        
        # Get greeting template
        if contact_info:
            # Personalized greeting for known contact
            name = contact_info['name']
            greetings = self.GREETINGS.get(lang, self.GREETINGS['en'])
            
            if time_of_day in greetings:
                templates = greetings[time_of_day]
            else:
                templates = greetings['unknown']
            
            greeting = random.choice(templates).format(name=self.owner_name)
        else:
            # Professional greeting for unknown caller
            prof_greetings = self.PROFESSIONAL_GREETINGS.get(
                lang, self.PROFESSIONAL_GREETINGS['en']
            )
            greeting = random.choice(prof_greetings).format(owner_name=self.owner_name)
        
        return greeting
    
    def generate_follow_up(self, context: str = "", language: str = "en") -> str:
        """
        Generate follow-up message when caller doesn't respond.
        
        Args:
            context: Context for the follow-up
            language: Language code
            
        Returns:
            Follow-up message
        """
        follow_ups = {
            'en': [
                "I'm still here. How can I help you?",
                "Are you there? Please let me know how I can assist.",
                "I didn't catch that. Could you please repeat?",
            ],
            'hi': [
                "Main yahin hoon. Aapko kya chahiye?",
                "Kya aap hain? Kripaya batayein main kaise madad karoon.",
            ],
            'mr': [
                "Mi ithech aahe. Tumhala kay hava?",
                "Tumhi aahat ka? Kripaya sanga mein kay madat karu.",
            ]
        }
        
        templates = follow_ups.get(language, follow_ups['en'])
        return random.choice(templates)
    
    def generate_closing(self, language: str = "en", urgent: bool = False) -> str:
        """
        Generate closing/goodbye message.
        
        Args:
            language: Language code
            urgent: Whether call was marked urgent
            
        Returns:
            Closing message
        """
        if urgent:
            closings = {
                'en': [
                    "I'll make sure {owner_name} gets this message urgently. Goodbye!",
                    "This seems urgent. I'll notify {owner_name} immediately. Thank you!",
                ],
                'hi': [
                    "Main turant {owner_name} ko sandesh doonga. Alvida!",
                    "Yah aavashyak lagta hai. Main turant suchna dunga. Dhanyavaad!",
                ],
                'mr': [
                    "Mi {owner_name} yanna turant sandesh denaar. Namaskar!",
                    "He tatkalinche aahe. Mi turant suchna denaar. Dhanyavaad!",
                ]
            }
        else:
            closings = {
                'en': [
                    "Thank you for calling! {owner_name} will get back to you.",
                    "Have a great day! {owner_name} will contact you soon.",
                    "Goodbye! I'll pass on your message to {owner_name}.",
                ],
                'hi': [
                    "Call karne ke liye dhanyavaad! {owner_name} aapko call karenge.",
                    "Aapka din shubh ho! {owner_name} jald hi sampark karenge.",
                ],
                'mr': [
                    "Call kelebadal dhanyavaad! {owner_name} tumhala call karil.",
                    "Tumcha divas shubh aso! {owner_name} lAvkarach sampark karel.",
                ]
            }
        
        templates = closings.get(language, closings['en'])
        return random.choice(templates).format(owner_name=self.owner_name)


if __name__ == "__main__":
    # Test
    generator = GreetingGenerator(owner_name="Aditya")
    
    # Add a test contact
    generator.add_contact("+1234567890", "Mom", "family", "hi")
    
    # Test different scenarios
    print("Unknown caller (English):")
    print(generator.generate(language="en"))
    print()
    
    print("Known contact (Hindi):")
    print(generator.generate(caller_number="+1234567890"))
    print()
    
    print("Time-based greeting:")
    print(f"Time of day: {generator._get_time_of_day()}")
    print()
    
    print("Closing (normal):")
    print(generator.generate_closing(language="en", urgent=False))
    print()
    
    print("Closing (urgent):")
    print(generator.generate_closing(language="en", urgent=True))
