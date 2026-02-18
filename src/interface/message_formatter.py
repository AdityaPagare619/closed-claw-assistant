"""
Message Formatter

Format messages for Telegram with support for various message types.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class FormatType(Enum):
    """Message format types."""
    CALL_NOTIFICATION = "call"
    WHATSAPP_SUMMARY = "whatsapp"
    SMS_SUMMARY = "sms"
    SYSTEM_STATUS = "system"
    AUTH_REQUEST = "auth"
    PERMISSION_DENIED = "denied"
    ERROR = "error"


@dataclass
class CallInfo:
    """Incoming call information."""
    caller_name: str
    caller_number: str
    timestamp: datetime
    call_type: str = "incoming"  # incoming, outgoing, missed


@dataclass
class WhatsAppMessage:
    """WhatsApp message summary."""
    sender: str
    group_name: Optional[str]
    message_preview: str
    unread_count: int
    timestamp: datetime
    is_group: bool = False


@dataclass
class SystemStatus:
    """System status information."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_tasks: int
    uptime_hours: float
    pending_notifications: int = 0


class MessageFormatter:
    """
    Format messages for Telegram display.
    
    Supports multiple languages and formatting styles.
    """
    
    def __init__(self, language: str = "en"):
        self.language = language
        self._translations = self._load_translations()
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translations for supported languages."""
        return {
            "en": {
                "incoming_call": "Incoming Call",
                "missed_call": "Missed Call",
                "from": "From",
                "number": "Number",
                "time": "Time",
                "whatsapp_summary": "WhatsApp Summary",
                "sms_summary": "SMS Summary",
                "unread": "unread",
                "group": "Group",
                "system_status": "System Status",
                "cpu": "CPU",
                "memory": "Memory",
                "disk": "Disk",
                "uptime": "Uptime",
                "tasks": "Tasks",
                "pending": "Pending",
                "auth_required": "Authentication Required",
                "enter_pin": "Please enter your PIN",
                "permission_denied": "Permission Denied",
                "insufficient_level": "This action requires higher permission level",
                "error": "Error",
                "confirm": "Confirm",
                "cancel": "Cancel",
                "accept": "Accept",
                "reject": "Reject",
                "snooze": "Snooze"
            },
            "es": {
                "incoming_call": "Llamada Entrante",
                "missed_call": "Llamada Perdida",
                "from": "De",
                "number": "Número",
                "time": "Hora",
                "whatsapp_summary": "Resumen WhatsApp",
                "sms_summary": "Resumen SMS",
                "unread": "no leídos",
                "group": "Grupo",
                "system_status": "Estado del Sistema",
                "cpu": "CPU",
                "memory": "Memoria",
                "disk": "Disco",
                "uptime": "Tiempo activo",
                "tasks": "Tareas",
                "pending": "Pendientes",
                "auth_required": "Autenticación Requerida",
                "enter_pin": "Por favor ingrese su PIN",
                "permission_denied": "Permiso Denegado",
                "insufficient_level": "Esta acción requiere mayor nivel de permiso",
                "error": "Error",
                "confirm": "Confirmar",
                "cancel": "Cancelar",
                "accept": "Aceptar",
                "reject": "Rechazar",
                "snooze": "Posponer"
            }
        }
    
    def _t(self, key: str) -> str:
        """Get translation for key."""
        return self._translations.get(self.language, {}).get(key, key)
    
    def format_call_notification(self, call: CallInfo) -> str:
        """
        Format incoming call notification.
        
        Args:
            call: Call information
            
        Returns:
            Formatted message string
        """
        if call.call_type == "missed":
            title = f"🔴 *{self._t('missed_call')}*"
        else:
            title = f"📞 *{self._t('incoming_call')}*"
        
        return (
            f"{title}\n\n"
            f"*{self._t('from')}:* {call.caller_name}\n"
            f"*{self._t('number')}:* `{call.caller_number}`\n"
            f"*{self._t('time')}:* {call.timestamp.strftime('%H:%M:%S')}"
        )
    
    def format_whatsapp_summary(
        self,
        messages: List[WhatsAppMessage],
        total_unread: int
    ) -> str:
        """
        Format WhatsApp summary.
        
        Args:
            messages: List of WhatsApp messages
            total_unread: Total unread count
            
        Returns:
            Formatted message string
        """
        lines = [
            f"💬 *{self._t('whatsapp_summary')}*",
            f"_{total_unread} {self._t('unread')}_\n"
        ]
        
        for msg in messages[:5]:  # Show max 5
            sender = msg.sender
            if msg.is_group and msg.group_name:
                sender = f"{msg.group_name} • {sender}"
            
            preview = msg.message_preview[:50]
            if len(msg.message_preview) > 50:
                preview += "..."
            
            lines.append(f"• *{sender}*: {preview}")
        
        if len(messages) > 5:
            lines.append(f"\n_...and {len(messages) - 5} more_")
        
        return "\n".join(lines)
    
    def format_sms_summary(
        self,
        messages: List[Dict[str, Any]],
        total_unread: int
    ) -> str:
        """
        Format SMS summary.
        
        Args:
            messages: List of SMS messages
            total_unread: Total unread count
            
        Returns:
            Formatted message string
        """
        lines = [
            f"📱 *{self._t('sms_summary')}*",
            f"_{total_unread} {self._t('unread')}_\n"
        ]
        
        for msg in messages[:5]:
            sender = msg.get("sender", "Unknown")
            preview = msg.get("body", "")[:50]
            if len(msg.get("body", "")) > 50:
                preview += "..."
            
            lines.append(f"• *{sender}*: {preview}")
        
        return "\n".join(lines)
    
    def format_system_status(self, status: SystemStatus) -> str:
        """
        Format system status message.
        
        Args:
            status: System status information
            
        Returns:
            Formatted message string
        """
        # Add emojis based on status
        cpu_emoji = "🟢" if status.cpu_percent < 50 else "🟡" if status.cpu_percent < 80 else "🔴"
        mem_emoji = "🟢" if status.memory_percent < 50 else "🟡" if status.memory_percent < 80 else "🔴"
        disk_emoji = "🟢" if status.disk_percent < 80 else "🟡" if status.disk_percent < 90 else "🔴"
        
        return (
            f"⚙️ *{self._t('system_status')}*\n\n"
            f"{cpu_emoji} *{self._t('cpu')}:* {status.cpu_percent:.1f}%\n"
            f"{mem_emoji} *{self._t('memory')}:* {status.memory_percent:.1f}%\n"
            f"{disk_emoji} *{self._t('disk')}:* {status.disk_percent:.1f}%\n"
            f"⏱ *{self._t('uptime')}:* {status.uptime_hours:.1f}h\n"
            f"📋 *{self._t('tasks')}:* {status.active_tasks}\n"
            f"🔔 *{self._t('pending')}:* {status.pending_notifications}"
        )
    
    def format_auth_request(self, action: str, level: int) -> str:
        """
        Format authentication request.
        
        Args:
            action: Action requiring authentication
            level: Required permission level
            
        Returns:
            Formatted message string
        """
        return (
            f"🔐 *{self._t('auth_required')}*\n\n"
            f"Action: `{action}`\n"
            f"Level: L{level}\n\n"
            f"_{self._t('enter_pin')}_"
        )
    
    def format_permission_denied(self, required_level: int) -> str:
        """
        Format permission denied message.
        
        Args:
            required_level: Required permission level
            
        Returns:
            Formatted message string
        """
        return (
            f"⛔ *{self._t('permission_denied')}*\n\n"
            f"_{self._t('insufficient_level')}_\n"
            f"Required: L{required_level}"
        )
    
    def format_error(self, error_message: str) -> str:
        """
        Format error message.
        
        Args:
            error_message: Error description
            
        Returns:
            Formatted message string
        """
        return f"❌ *{self._t('error')}*\n\n`{error_message}`"
    
    def create_confirmation_buttons(
        self,
        confirm_callback: str,
        cancel_callback: str
    ) -> List[List[Dict[str, str]]]:
        """
        Create confirmation button layout.
        
        Args:
            confirm_callback: Callback data for confirm
            cancel_callback: Callback data for cancel
            
        Returns:
            Button layout definition
        """
        return [
            [
                {"text": f"✓ {self._t('confirm')}", "callback_data": confirm_callback},
                {"text": f"✗ {self._t('cancel')}", "callback_data": cancel_callback}
            ]
        ]
    
    def create_call_buttons(self, call_id: str) -> List[List[Dict[str, str]]]:
        """
        Create call action buttons.
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            Button layout definition
        """
        return [
            [
                {"text": f"✓ {self._t('accept')}", "callback_data": f"call_accept:{call_id}"},
                {"text": f"✗ {self._t('reject')}", "callback_data": f"call_reject:{call_id}"}
            ],
            [
                {"text": f"⏰ {self._t('snooze')}", "callback_data": f"call_snooze:{call_id}"}
            ]
        ]
    
    def create_auth_buttons(self, request_id: str) -> List[List[Dict[str, str]]]:
        """
        Create authentication action buttons.
        
        Args:
            request_id: Auth request identifier
            
        Returns:
            Button layout definition
        """
        return [
            [
                {"text": "1️⃣", "callback_data": f"auth:{request_id}:1"},
                {"text": "2️⃣", "callback_data": f"auth:{request_id}:2"},
                {"text": "3️⃣", "callback_data": f"auth:{request_id}:3"}
            ],
            [
                {"text": "4️⃣", "callback_data": f"auth:{request_id}:4"},
                {"text": "5️⃣", "callback_data": f"auth:{request_id}:5"},
                {"text": "6️⃣", "callback_data": f"auth:{request_id}:6"}
            ],
            [
                {"text": "7️⃣", "callback_data": f"auth:{request_id}:7"},
                {"text": "8️⃣", "callback_data": f"auth:{request_id}:8"},
                {"text": "9️⃣", "callback_data": f"auth:{request_id}:9"}
            ],
            [
                {"text": "❌", "callback_data": f"auth:{request_id}:cancel"},
                {"text": "0️⃣", "callback_data": f"auth:{request_id}:0"},
                {"text": "✓", "callback_data": f"auth:{request_id}:submit"}
            ]
        ]
