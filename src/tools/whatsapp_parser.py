"""
WhatsApp Message Parser
Parse message content, extract metadata, filter system messages
Read-only processing, local only
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhatsAppParser:
    """
    Parse WhatsApp messages to extract text, metadata, and important information
    Handles various message types including text, media, and system messages
    """
    
    def __init__(self):
        self.media_types = ['imageMessage', 'videoMessage', 'audioMessage', 
                           'documentMessage', 'stickerMessage', 'voiceMessage']
        self.system_types = ['protocolMessage', 'senderKeyDistributionMessage']
    
    def parse_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a raw WhatsApp message into structured format
        
        Args:
            raw_message: Raw message dict from WhatsApp Web
            
        Returns:
            Parsed message with extracted fields
        """
        try:
            parsed = {
                'id': raw_message.get('id'),
                'chat_id': raw_message.get('chat_id'),
                'sender': raw_message.get('sender'),
                'sender_name': raw_message.get('sender_name', 'Unknown'),
                'timestamp': self._parse_timestamp(raw_message.get('timestamp')),
                'is_group': raw_message.get('is_group', False),
                'type': 'unknown',
                'content': None,
                'has_media': False,
                'media_type': None,
                'is_system': False,
                'is_important': False,
                'mentions': [],
                'urls': [],
                'phone_numbers': []
            }
            
            # Extract message content
            message_content = raw_message.get('message', {})
            
            # Check if system message
            if self._is_system_message(message_content):
                parsed['is_system'] = True
                parsed['type'] = 'system'
                parsed['content'] = self._extract_system_info(message_content)
                return parsed
            
            # Parse message based on type
            if 'conversation' in message_content:
                # Plain text message
                parsed['type'] = 'text'
                parsed['content'] = message_content['conversation']
                
            elif 'extendedTextMessage' in message_content:
                # Text with formatting/mentions
                parsed['type'] = 'text'
                ext_msg = message_content['extendedTextMessage']
                parsed['content'] = ext_msg.get('text', '')
                parsed['mentions'] = self._extract_mentions(ext_msg)
                
            elif 'imageMessage' in message_content:
                parsed['type'] = 'image'
                parsed['has_media'] = True
                parsed['media_type'] = 'image'
                parsed['content'] = message_content['imageMessage'].get('caption', '[Image]')
                
            elif 'videoMessage' in message_content:
                parsed['type'] = 'video'
                parsed['has_media'] = True
                parsed['media_type'] = 'video'
                parsed['content'] = message_content['videoMessage'].get('caption', '[Video]')
                
            elif 'audioMessage' in message_content:
                parsed['type'] = 'audio'
                parsed['has_media'] = True
                parsed['media_type'] = 'audio'
                parsed['content'] = '[Audio message]'
                
            elif 'voiceMessage' in message_content:
                parsed['type'] = 'voice'
                parsed['has_media'] = True
                parsed['media_type'] = 'voice'
                parsed['content'] = '[Voice message]'
                
            elif 'documentMessage' in message_content:
                parsed['type'] = 'document'
                parsed['has_media'] = True
                parsed['media_type'] = 'document'
                doc_msg = message_content['documentMessage']
                parsed['content'] = f"[Document: {doc_msg.get('fileName', 'Unknown')}]"
                
            elif 'stickerMessage' in message_content:
                parsed['type'] = 'sticker'
                parsed['has_media'] = True
                parsed['media_type'] = 'sticker'
                parsed['content'] = '[Sticker]'
                
            elif 'locationMessage' in message_content:
                parsed['type'] = 'location'
                loc_msg = message_content['locationMessage']
                parsed['content'] = f"[Location: {loc_msg.get('degreesLatitude')}, {loc_msg.get('degreesLongitude')}]"
                
            elif 'contactMessage' in message_content:
                parsed['type'] = 'contact'
                contact_msg = message_content['contactMessage']
                parsed['content'] = f"[Contact: {contact_msg.get('displayName', 'Unknown')}]"
                
            else:
                # Unknown message type
                parsed['type'] = 'unknown'
                parsed['content'] = '[Unsupported message type]'
            
            # Extract URLs and phone numbers from text content
            if parsed['content'] and isinstance(parsed['content'], str):
                parsed['urls'] = self._extract_urls(parsed['content'])
                parsed['phone_numbers'] = self._extract_phone_numbers(parsed['content'])
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return {
                'type': 'error',
                'content': str(e),
                'raw': raw_message
            }
    
    def _parse_timestamp(self, timestamp: Optional[int]) -> Optional[datetime]:
        """Convert Unix timestamp to datetime"""
        if timestamp:
            try:
                return datetime.fromtimestamp(timestamp)
            except (ValueError, TypeError):
                return None
        return None
    
    def _is_system_message(self, message_content: Dict) -> bool:
        """Check if message is a system message"""
        if not message_content:
            return True
        
        # Check for system message types
        for sys_type in self.system_types:
            if sys_type in message_content:
                return True
        
        # Check for message deletion/revoke
        if 'protocolMessage' in message_content:
            return True
        
        return False
    
    def _extract_system_info(self, message_content: Dict) -> str:
        """Extract information from system messages"""
        if 'protocolMessage' in message_content:
            proto_msg = message_content['protocolMessage']
            if proto_msg.get('type') == 0:
                return '[Message deleted]'
        
        return '[System message]'
    
    def _extract_mentions(self, ext_msg: Dict) -> List[str]:
        """Extract mentioned user IDs from message"""
        mentions = []
        context_info = ext_msg.get('contextInfo', {})
        
        if 'mentionedJid' in context_info:
            mentions = context_info['mentionedJid']
        
        return mentions
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from message text"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
    
    def _extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from message text"""
        # Simple phone number pattern
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        return re.findall(phone_pattern, text)
    
    def filter_messages(self, 
                       messages: List[Dict], 
                       skip_system: bool = True,
                       skip_media: bool = False) -> List[Dict]:
        """
        Filter messages based on criteria
        
        Args:
            messages: List of parsed messages
            skip_system: Skip system messages
            skip_media: Skip messages with media
            
        Returns:
            Filtered list of messages
        """
        filtered = []
        
        for msg in messages:
            # Skip system messages if requested
            if skip_system and msg.get('is_system'):
                continue
            
            # Skip media messages if requested
            if skip_media and msg.get('has_media'):
                continue
            
            filtered.append(msg)
        
        return filtered
    
    def extract_important_info(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract important actionable information from a message
        
        Returns:
            Dict with extracted information types
        """
        content = message.get('content', '')
        if not content or not isinstance(content, str):
            return {}
        
        info = {
            'has_urls': bool(message.get('urls')),
            'has_phone_numbers': bool(message.get('phone_numbers')),
            'has_mentions': bool(message.get('mentions')),
            'word_count': len(content.split()),
            'is_reply': False,
            'is_forwarded': False
        }
        
        # Check for reply/forward indicators
        raw_msg = message.get('raw', {})
        if raw_msg:
            message_content = raw_msg.get('message', {})
            context_info = message_content.get('contextInfo', {})
            
            if context_info.get('stanzaId'):
                info['is_reply'] = True
            if context_info.get('isForwarded'):
                info['is_forwarded'] = True
        
        return info
    
    def format_for_notification(self, message: Dict[str, Any]) -> str:
        """Format a parsed message for notification display"""
        sender = message.get('sender_name', 'Unknown')
        content = message.get('content', '')
        chat_type = 'Group' if message.get('is_group') else 'Chat'
        
        # Truncate long messages
        if len(content) > 100:
            content = content[:97] + '...'
        
        return f"📱 WhatsApp {chat_type} - {sender}: {content}"


# Convenience functions
def parse_single_message(raw_message: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a single message"""
    parser = WhatsAppParser()
    return parser.parse_message(raw_message)


def parse_multiple_messages(raw_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse multiple messages"""
    parser = WhatsAppParser()
    return [parser.parse_message(msg) for msg in raw_messages]


# Example usage
if __name__ == "__main__":
    # Test parsing
    test_messages = [
        {
            'id': '123',
            'chat_id': '123456789@s.whatsapp.net',
            'sender': '123456789@s.whatsapp.net',
            'sender_name': 'John Doe',
            'timestamp': 1704067200,
            'is_group': False,
            'message': {
                'conversation': 'Hello! Check out this link: https://example.com'
            }
        },
        {
            'id': '124',
            'chat_id': 'group123@g.us',
            'sender': '987654321@s.whatsapp.net',
            'sender_name': 'Jane Smith',
            'timestamp': 1704067300,
            'is_group': True,
            'message': {
                'imageMessage': {
                    'caption': 'Look at this photo!'
                }
            }
        }
    ]
    
    parser = WhatsAppParser()
    for msg in test_messages:
        parsed = parser.parse_message(msg)
        print(f"Parsed: {parsed}")
