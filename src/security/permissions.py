"""
Permission System

L1-L4 permission levels for granular access control.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from functools import wraps


logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """
    Permission levels from L1 (lowest) to L4 (highest).
    
    L1: Auto (no auth) - Safe read-only queries
    L2: PIN - Read sensitive data (WhatsApp, SMS)
    L3: Confirm - Write/modify data (Calendar, Files)
    L4: Confirm+Delay - High-risk actions (Calls, System)
    """
    L1_AUTO = 1
    L2_PIN = 2
    L3_CONFIRM = 3
    L4_CONFIRM_DELAY = 4


class PermissionDenied(Exception):
    """Raised when permission check fails."""
    
    def __init__(self, required_level: PermissionLevel, current_level: PermissionLevel, message: str = ""):
        self.required_level = required_level
        self.current_level = current_level
        self.message = message or f"Permission denied: requires {required_level.name}, current {current_level.name}"
        super().__init__(self.message)


@dataclass
class PermissionAction:
    """Defines a permission-protected action."""
    name: str
    description: str
    level: PermissionLevel
    requires_confirmation: bool = False
    delay_seconds: int = 0
    audit_log: bool = True


@dataclass
class UserPermissions:
    """User permission state."""
    user_id: int
    current_level: PermissionLevel = PermissionLevel.L1_AUTO
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    confirmed_actions: List[str] = field(default_factory=list)
    pending_confirmations: Dict[str, datetime] = field(default_factory=dict)


class PermissionManager:
    """
    Manages L1-L4 permission system.
    
    Features:
    - Level-based access control
    - Confirmation flows for L3/L4
    - Delay enforcement for L4
    - Session management
    - Audit logging
    """
    
    # Default action definitions
    DEFAULT_ACTIONS = {
        # L1: Auto - No authentication required
        "query_status": PermissionAction("query_status", "Query system status", PermissionLevel.L1_AUTO),
        "list_tasks": PermissionAction("list_tasks", "List active tasks", PermissionLevel.L1_AUTO),
        "get_time": PermissionAction("get_time", "Get current time", PermissionLevel.L1_AUTO),
        "help": PermissionAction("help", "Show help", PermissionLevel.L1_AUTO),
        
        # L2: PIN - Read sensitive data
        "read_whatsapp": PermissionAction("read_whatsapp", "Read WhatsApp messages", PermissionLevel.L2_PIN),
        "read_sms": PermissionAction("read_sms", "Read SMS messages", PermissionLevel.L2_PIN),
        "read_call_log": PermissionAction("read_call_log", "Read call history", PermissionLevel.L2_PIN),
        "read_contacts": PermissionAction("read_contacts", "Read contacts", PermissionLevel.L2_PIN),
        
        # L3: Confirm - Write data
        "write_calendar": PermissionAction("write_calendar", "Modify calendar", PermissionLevel.L3_CONFIRM, requires_confirmation=True),
        "write_files": PermissionAction("write_files", "Modify files", PermissionLevel.L3_CONFIRM, requires_confirmation=True),
        "send_message": PermissionAction("send_message", "Send message", PermissionLevel.L3_CONFIRM, requires_confirmation=True),
        "create_reminder": PermissionAction("create_reminder", "Create reminder", PermissionLevel.L3_CONFIRM, requires_confirmation=True),
        
        # L4: Confirm+Delay - High-risk actions
        "make_call": PermissionAction("make_call", "Make phone call", PermissionLevel.L4_CONFIRM_DELAY, requires_confirmation=True, delay_seconds=10),
        "system_command": PermissionAction("system_command", "Execute system command", PermissionLevel.L4_CONFIRM_DELAY, requires_confirmation=True, delay_seconds=15),
        "modify_settings": PermissionAction("modify_settings", "Modify system settings", PermissionLevel.L4_CONFIRM_DELAY, requires_confirmation=True, delay_seconds=10),
        "shutdown": PermissionAction("shutdown", "Shutdown/reboot system", PermissionLevel.L4_CONFIRM_DELAY, requires_confirmation=True, delay_seconds=30),
    }
    
    def __init__(
        self,
        session_timeout_minutes: int = 5,
        audit_callback: Optional[Callable[[str, Any], None]] = None
    ):
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.audit_callback = audit_callback
        
        self._actions: Dict[str, PermissionAction] = dict(self.DEFAULT_ACTIONS)
        self._user_sessions: Dict[int, UserPermissions] = {}
        self._confirmation_callbacks: Dict[str, Callable] = {}
        
        logger.info("PermissionManager initialized")
    
    def register_action(self, action: PermissionAction):
        """Register a new permission action."""
        self._actions[action.name] = action
        logger.debug(f"Registered action: {action.name} -> {action.level.name}")
    
    def get_action(self, action_name: str) -> Optional[PermissionAction]:
        """Get action definition by name."""
        return self._actions.get(action_name)
    
    def check_permission(
        self,
        user_id: int,
        action_name: str,
        auto_confirm: bool = False
    ) -> bool:
        """
        Check if user has permission for action.
        
        Args:
            user_id: User identifier
            action_name: Action to check
            auto_confirm: Skip confirmation for L3/L4
            
        Returns:
            True if allowed
            
        Raises:
            PermissionDenied: If not allowed
        """
        action = self._actions.get(action_name)
        if not action:
            logger.warning(f"Unknown action: {action_name}")
            raise PermissionDenied(
                PermissionLevel.L1_AUTO,
                PermissionLevel.L1_AUTO,
                f"Unknown action: {action_name}"
            )
        
        user_perms = self._get_user_permissions(user_id)
        
        # Check if session expired
        if user_perms.expires_at and datetime.now() > user_perms.expires_at:
            logger.info(f"Session expired for user {user_id}")
            user_perms.current_level = PermissionLevel.L1_AUTO
            user_perms.granted_at = None
            user_perms.expires_at = None
        
        # Check level
        if user_perms.current_level.value < action.level.value:
            logger.warning(
                f"Permission denied for user {user_id}: "
                f"{action_name} requires {action.level.name}, "
                f"user has {user_perms.current_level.name}"
            )
            raise PermissionDenied(action.level, user_perms.current_level)
        
        # Check confirmation requirement
        if action.requires_confirmation and not auto_confirm:
            if action_name not in user_perms.confirmed_actions:
                # Check if pending
                if action_name in user_perms.pending_confirmations:
                    # Check delay for L4
                    if action.level == PermissionLevel.L4_CONFIRM_DELAY:
                        pending_time = user_perms.pending_confirmations[action_name]
                        elapsed = (datetime.now() - pending_time).total_seconds()
                        if elapsed < action.delay_seconds:
                            remaining = action.delay_seconds - elapsed
                            logger.info(f"Delay pending for {action_name}: {remaining:.0f}s remaining")
                            raise PermissionDenied(
                                action.level,
                                user_perms.current_level,
                                f"Please wait {remaining:.0f} seconds before confirming"
                            )
                    return True  # Ready to confirm
                else:
                    # Needs confirmation
                    logger.info(f"Confirmation required for {action_name}")
                    return False
        
        # Audit log
        if action.audit_log:
            self._audit_log(f"ACTION_ALLOWED", {
                "user_id": user_id,
                "action": action_name,
                "level": action.level.name
            })
        
        return True
    
    def request_confirmation(self, user_id: int, action_name: str) -> bool:
        """
        Request user confirmation for action.
        
        Args:
            user_id: User to confirm
            action_name: Action requiring confirmation
            
        Returns:
            True if confirmation started
        """
        action = self._actions.get(action_name)
        if not action:
            return False
        
        user_perms = self._get_user_permissions(user_id)
        
        # Set pending confirmation
        user_perms.pending_confirmations[action_name] = datetime.now()
        
        self._audit_log("CONFIRMATION_REQUESTED", {
            "user_id": user_id,
            "action": action_name,
            "delay": action.delay_seconds if action.level == PermissionLevel.L4_CONFIRM_DELAY else 0
        })
        
        logger.info(f"Confirmation requested for {action_name} by user {user_id}")
        return True
    
    def confirm_action(self, user_id: int, action_name: str) -> bool:
        """
        Confirm pending action.
        
        Args:
            user_id: User confirming
            action_name: Action to confirm
            
        Returns:
            True if confirmed successfully
        """
        user_perms = self._get_user_permissions(user_id)
        
        if action_name not in user_perms.pending_confirmations:
            logger.warning(f"No pending confirmation for {action_name}")
            return False
        
        action = self._actions.get(action_name)
        if not action:
            return False
        
        # Check delay for L4
        if action.level == PermissionLevel.L4_CONFIRM_DELAY:
            pending_time = user_perms.pending_confirmations[action_name]
            elapsed = (datetime.now() - pending_time).total_seconds()
            if elapsed < action.delay_seconds:
                logger.warning(f"Confirmation too early for {action_name}")
                return False
        
        # Mark as confirmed
        user_perms.confirmed_actions.append(action_name)
        del user_perms.pending_confirmations[action_name]
        
        self._audit_log("ACTION_CONFIRMED", {
            "user_id": user_id,
            "action": action_name
        })
        
        logger.info(f"Action {action_name} confirmed by user {user_id}")
        return True
    
    def cancel_confirmation(self, user_id: int, action_name: str):
        """Cancel pending confirmation."""
        user_perms = self._get_user_permissions(user_id)
        if action_name in user_perms.pending_confirmations:
            del user_perms.pending_confirmations[action_name]
            self._audit_log("CONFIRMATION_CANCELLED", {
                "user_id": user_id,
                "action": action_name
            })
    
    def set_user_level(
        self,
        user_id: int,
        level: PermissionLevel,
        duration_minutes: Optional[int] = None
    ):
        """
        Set user's permission level.
        
        Args:
            user_id: User to set
            level: New permission level
            duration_minutes: Session duration (default: self.session_timeout)
        """
        user_perms = self._get_user_permissions(user_id)
        user_perms.current_level = level
        user_perms.granted_at = datetime.now()
        
        timeout = timedelta(minutes=duration_minutes) if duration_minutes else self.session_timeout
        user_perms.expires_at = datetime.now() + timeout
        
        # Clear confirmations when level changes
        user_perms.confirmed_actions.clear()
        user_perms.pending_confirmations.clear()
        
        self._audit_log("LEVEL_CHANGED", {
            "user_id": user_id,
            "new_level": level.name,
            "expires": user_perms.expires_at.isoformat()
        })
        
        logger.info(f"User {user_id} level set to {level.name}")
    
    def clear_user_session(self, user_id: int):
        """Clear user's session."""
        if user_id in self._user_sessions:
            del self._user_sessions[user_id]
            self._audit_log("SESSION_CLEARED", {"user_id": user_id})
            logger.info(f"Session cleared for user {user_id}")
    
    def get_user_level(self, user_id: int) -> PermissionLevel:
        """Get user's current permission level."""
        return self._get_user_permissions(user_id).current_level
    
    def _get_user_permissions(self, user_id: int) -> UserPermissions:
        """Get or create user permissions."""
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = UserPermissions(user_id=user_id)
        return self._user_sessions[user_id]
    
    def _audit_log(self, event: str, data: dict):
        """Send audit log."""
        if self.audit_callback:
            try:
                self.audit_callback(event, data)
            except Exception as e:
                logger.error(f"Audit log failed: {e}")
        
        logger.info(f"AUDIT: {event} - {data}")
    
    def require_permission(self, action_name: str):
        """
        Decorator to require permission for function.
        
        Usage:
            @permission_manager.require_permission("make_call")
            async def make_phone_call(user_id: int, number: str):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Extract user_id from args or kwargs
                user_id = kwargs.get('user_id')
                if not user_id and len(args) > 0:
                    user_id = args[0]
                
                if not user_id:
                    raise ValueError("user_id required for permission check")
                
                if self.check_permission(user_id, action_name):
                    return await func(*args, **kwargs)
                else:
                    raise PermissionDenied(
                        self._actions[action_name].level,
                        self.get_user_level(user_id)
                    )
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                user_id = kwargs.get('user_id')
                if not user_id and len(args) > 0:
                    user_id = args[0]
                
                if not user_id:
                    raise ValueError("user_id required for permission check")
                
                if self.check_permission(user_id, action_name):
                    return func(*args, **kwargs)
                else:
                    raise PermissionDenied(
                        self._actions[action_name].level,
                        self.get_user_level(user_id)
                    )
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator


import asyncio
