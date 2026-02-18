"""
Android Notification Manager using Termux:API
Read notification access, filter by app, extract actionable info
Local processing only, privacy-focused
"""

import json
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Manage Android notifications using Termux:API
    Read-only access to notification content, filter by app
    """
    
    def __init__(self, 
                 monitored_apps: Optional[List[str]] = None,
                 on_notification_callback: Optional[Callable] = None):
        # Apps to monitor (default: WhatsApp, SMS, Phone)
        self.monitored_apps = monitored_apps or [
            'com.whatsapp',
            'com.whatsapp.w4b',  # WhatsApp Business
            'com.google.android.apps.messaging',  # Google Messages
            'com.android.messaging',
            'com.android.mms',
            'com.samsung.android.messaging',
            'com.google.android.dialer',  # Phone app
            'com.android.dialer'
        ]
        
        self.on_notification = on_notification_callback
        self.recent_notifications: List[Dict] = []
        self.max_history = 100
        
        # Track seen notifications to avoid duplicates
        self.seen_ids: set = set()
        
        self._stop_event = asyncio.Event()
        self._polling_task: Optional[asyncio.Task] = None
    
    async def start(self, poll_interval: float = 2.0):
        """Start polling for notifications"""
        logger.info("Starting notification manager...")
        
        # Check if Termux:API is available
        if not self._check_termux_api():
            logger.error("Termux:API not available. Install Termux:API app.")
            return False
        
        self._stop_event.clear()
        self._polling_task = asyncio.create_task(self._poll_notifications(poll_interval))
        return True
    
    async def stop(self):
        """Stop polling for notifications"""
        logger.info("Stopping notification manager...")
        self._stop_event.set()
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
    
    def _check_termux_api(self) -> bool:
        """Check if Termux:API commands are available"""
        try:
            result = subprocess.run(
                ['termux-notification-list', '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 or 'usage' in result.stderr.lower()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def _poll_notifications(self, interval: float):
        """Poll for new notifications"""
        while not self._stop_event.is_set():
            try:
                notifications = await self._fetch_notifications()
                
                for notification in notifications:
                    await self._process_notification(notification)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error polling notifications: {e}")
                await asyncio.sleep(interval)
    
    async def _fetch_notifications(self) -> List[Dict[str, Any]]:
        """Fetch current notifications using Termux:API"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ['termux-notification-list'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            )
            
            if result.returncode == 0 and result.stdout:
                try:
                    notifications = json.loads(result.stdout)
                    return notifications if isinstance(notifications, list) else []
                except json.JSONDecodeError:
                    logger.error("Failed to parse notification list")
                    return []
            
            return []
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout fetching notifications")
            return []
        except Exception as e:
            logger.error(f"Error fetching notifications: {e}")
            return []
    
    async def _process_notification(self, notification: Dict[str, Any]):
        """Process a single notification"""
        try:
            # Create unique ID for deduplication
            notif_id = self._create_notification_id(notification)
            
            if notif_id in self.seen_ids:
                return
            
            self.seen_ids.add(notif_id)
            
            # Parse notification
            parsed = self.parse_notification(notification)
            
            # Check if from monitored app
            if not self._should_monitor(parsed):
                return
            
            # Store in history
            self.recent_notifications.append(parsed)
            if len(self.recent_notifications) > self.max_history:
                self.recent_notifications.pop(0)
            
            # Call callback if provided
            if self.on_notification:
                self.on_notification(parsed)
            
            logger.debug(f"New notification: {parsed.get('app_name')} - {parsed.get('title')}")
            
        except Exception as e:
            logger.error(f"Error processing notification: {e}")
    
    def _create_notification_id(self, notification: Dict) -> str:
        """Create unique ID for notification deduplication"""
        key = f"{notification.get('packageName', '')}:{notification.get('title', '')}:{notification.get('content', '')}:{notification.get('when', '')}"
        return key
    
    def parse_notification(self, raw_notification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a raw notification into structured format
        
        Args:
            raw_notification: Raw notification from Termux:API
            
        Returns:
            Parsed notification dict
        """
        parsed = {
            'id': raw_notification.get('id'),
            'app_package': raw_notification.get('packageName', ''),
            'app_name': self._get_app_name(raw_notification.get('packageName', '')),
            'title': raw_notification.get('title', ''),
            'content': raw_notification.get('content', ''),
            'ticker': raw_notification.get('tickerText', ''),
            'timestamp': raw_notification.get('when', 0),
            'datetime': datetime.fromtimestamp(raw_notification.get('when', 0) / 1000) if raw_notification.get('when') else None,
            'is_group': raw_notification.get('group', False),
            'is_clearable': raw_notification.get('clearable', True),
            'priority': raw_notification.get('priority', 0),
            'extracted_info': {}
        }
        
        # Extract actionable information
        content = parsed['content'] or parsed['ticker'] or ''
        parsed['extracted_info'] = self._extract_info(content)
        
        return parsed
    
    def _get_app_name(self, package_name: str) -> str:
        """Get human-readable app name from package name"""
        app_names = {
            'com.whatsapp': 'WhatsApp',
            'com.whatsapp.w4b': 'WhatsApp Business',
            'com.google.android.apps.messaging': 'Messages',
            'com.android.messaging': 'Messaging',
            'com.android.mms': 'SMS',
            'com.samsung.android.messaging': 'Samsung Messages',
            'com.google.android.dialer': 'Phone',
            'com.android.dialer': 'Phone',
            'com.facebook.orca': 'Messenger',
            'com.instagram.android': 'Instagram',
            'com.twitter.android': 'Twitter',
            'com.telegram.messenger': 'Telegram'
        }
        return app_names.get(package_name, package_name.split('.')[-1].title())
    
    def _should_monitor(self, notification: Dict) -> bool:
        """Check if notification should be monitored"""
        return notification.get('app_package') in self.monitored_apps
    
    def _extract_info(self, content: str) -> Dict[str, Any]:
        """Extract actionable information from notification content"""
        info = {
            'urls': [],
            'phone_numbers': [],
            'emails': [],
            'codes': [],
            'addresses': [],
            'mentions': []
        }
        
        if not content:
            return info
        
        # Extract URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        info['urls'] = re.findall(url_pattern, content)
        
        # Extract phone numbers
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        info['phone_numbers'] = re.findall(phone_pattern, content)
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        info['emails'] = re.findall(email_pattern, content)
        
        # Extract verification codes (common patterns)
        code_patterns = [
            r'\b\d{4,8}\b',  # 4-8 digit codes
            r'code[\s:]+(\d+)',  # "code: 123456"
            r'otp[\s:]+(\d+)',  # "otp: 123456"
        ]
        for pattern in code_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            info['codes'].extend(matches)
        
        return info
    
    def get_recent_notifications(self, 
                                app_filter: Optional[str] = None,
                                limit: int = 20) -> List[Dict]:
        """Get recent notifications with optional filtering"""
        notifications = self.recent_notifications
        
        if app_filter:
            notifications = [
                n for n in notifications 
                if app_filter.lower() in n.get('app_name', '').lower()
            ]
        
        return notifications[-limit:]
    
    def clear_history(self):
        """Clear notification history"""
        self.recent_notifications.clear()
        self.seen_ids.clear()
        logger.info("Notification history cleared")
    
    def add_monitored_app(self, package_name: str):
        """Add an app to monitor"""
        if package_name not in self.monitored_apps:
            self.monitored_apps.append(package_name)
            logger.info(f"Added {package_name} to monitored apps")
    
    def remove_monitored_app(self, package_name: str):
        """Remove an app from monitoring"""
        if package_name in self.monitored_apps:
            self.monitored_apps.remove(package_name)
            logger.info(f"Removed {package_name} from monitored apps")
    
    def is_important_notification(self, notification: Dict) -> Tuple[bool, str]:
        """
        Determine if a notification is important
        
        Returns:
            Tuple of (is_important, reason)
        """
        # High priority notifications
        if notification.get('priority', 0) > 1:
            return True, "high_priority"
        
        # Missed call
        title = notification.get('title', '').lower()
        content = notification.get('content', '').lower()
        
        if 'missed call' in content or 'missed call' in title:
            return True, "missed_call"
        
        # Voice message
        if 'voice message' in content or 'voice message' in title:
            return True, "voice_message"
        
        # Contains URL or code
        extracted = notification.get('extracted_info', {})
        if extracted.get('urls'):
            return True, "contains_url"
        if extracted.get('codes'):
            return True, "contains_code"
        
        # Direct mentions in WhatsApp groups
        if notification.get('is_group') and '@' in content:
            return True, "group_mention"
        
        return False, ""
    
    def format_for_telegram(self, notification: Dict) -> str:
        """Format notification for Telegram forwarding"""
        app = notification.get('app_name', 'Unknown')
        title = notification.get('title', '')
        content = notification.get('content', '')
        
        # Truncate long content
        if len(content) > 200:
            content = content[:197] + '...'
        
        return f"📱 *{app}*\n*{title}*\n{content}"


# Convenience functions
async def create_notification_manager(on_notification: Callable) -> NotificationManager:
    """Create and start notification manager"""
    manager = NotificationManager(on_notification_callback=on_notification)
    await manager.start()
    return manager


# Example usage
if __name__ == "__main__":
    async def main():
        def on_notif(notification):
            print(f"[Notification] {notification.get('app_name')}: {notification.get('title')}")
        
        manager = NotificationManager(on_notification_callback=on_notif)
        
        if await manager.start():
            print("Notification manager started. Press Ctrl+C to stop.")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                await manager.stop()
        else:
            print("Failed to start notification manager")
    
    asyncio.run(main())
