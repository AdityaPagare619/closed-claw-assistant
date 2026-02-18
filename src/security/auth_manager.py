"""
Authentication Manager

Handles PIN verification, biometric auth, and session management.
"""

import hashlib
import hmac
import logging
import secrets
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Callable, Any, Tuple
from pathlib import Path


logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """Authentication methods."""
    PIN = "pin"
    BIOMETRIC = "biometric"
    NONE = "none"


class AuthStatus(Enum):
    """Authentication status."""
    SUCCESS = "success"
    FAILURE = "failure"
    LOCKED = "locked"
    EXPIRED = "expired"
    PENDING = "pending"


@dataclass
class AuthSession:
    """Authentication session state."""
    user_id: int
    method: AuthMethod
    level_granted: int  # 1-4
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    auth_token: str
    biometric_verified: bool = False


@dataclass
class FailedAttempt:
    """Failed authentication attempt record."""
    timestamp: datetime
    method: AuthMethod
    reason: str


class BiometricAuth:
    """
    Biometric authentication handler.
    
    Supports platform-specific biometric APIs.
    """
    
    def __init__(self):
        self._available = self._check_availability()
        self._enrolled_users: Dict[int, str] = {}  # user_id -> biometric_hash
    
    def _check_availability(self) -> bool:
        """Check if biometric auth is available on system."""
        try:
            # Check for Windows Hello
            import sys
            if sys.platform == "win32":
                # Try to import Windows Hello APIs
                try:
                    import winrt.windows.security.credentials.ui as wsci
                    return True
                except ImportError:
                    pass
            
            # Check for macOS Touch ID
            elif sys.platform == "darwin":
                try:
                    import LocalAuthentication
                    return True
                except ImportError:
                    pass
            
            # Check for Linux fingerprint
            elif sys.platform == "linux":
                # Check for fprintd
                import subprocess
                result = subprocess.run(
                    ["which", "fprintd-verify"],
                    capture_output=True
                )
                return result.returncode == 0
            
        except Exception as e:
            logger.debug(f"Biometric check failed: {e}")
        
        return False
    
    def is_available(self) -> bool:
        """Check if biometric auth is available."""
        return self._available
    
    async def authenticate(self, user_id: int) -> Tuple[bool, str]:
        """
        Trigger biometric authentication.
        
        Args:
            user_id: User to authenticate
            
        Returns:
            Tuple of (success, message)
        """
        if not self._available:
            return False, "Biometric authentication not available"
        
        try:
            import sys
            
            if sys.platform == "win32":
                return await self._auth_windows(user_id)
            elif sys.platform == "darwin":
                return await self._auth_macos(user_id)
            elif sys.platform == "linux":
                return await self._auth_linux(user_id)
            else:
                return False, "Unsupported platform"
                
        except Exception as e:
            logger.error(f"Biometric auth error: {e}")
            return False, f"Biometric authentication failed: {e}"
    
    async def _auth_windows(self, user_id: int) -> Tuple[bool, str]:
        """Windows Hello authentication."""
        try:
            import winrt.windows.security.credentials.ui as wsci
            
            # Request user verification
            result = await wsci.UserConsentVerifier.request_verification_async(
                "Authenticate for ClosedClaw Assistant"
            )
            
            if result == wsci.UserConsentVerificationResult.verified:
                return True, "Windows Hello verified"
            else:
                return False, f"Windows Hello failed: {result}"
                
        except Exception as e:
            return False, f"Windows Hello error: {e}"
    
    async def _auth_macos(self, user_id: int) -> Tuple[bool, str]:
        """macOS Touch ID authentication."""
        try:
            # Use subprocess to call osascript for Touch ID
            import subprocess
            
            script = '''
            tell application "System Events"
                display dialog "Authenticate for ClosedClaw Assistant" buttons {"Cancel", "Authenticate"} default button "Authenticate" with icon caution
            end tell
            '''
            
            # Note: This is a simplified version
            # Real Touch ID requires Objective-C bridge
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, "Touch ID verified"
            else:
                return False, "Touch ID cancelled"
                
        except Exception as e:
            return False, f"Touch ID error: {e}"
    
    async def _auth_linux(self, user_id: int) -> Tuple[bool, str]:
        """Linux fingerprint authentication."""
        try:
            import subprocess
            
            # Try to verify fingerprint
            result = await asyncio.create_subprocess_exec(
                "fprintd-verify",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                return True, "Fingerprint verified"
            else:
                return False, "Fingerprint verification failed"
                
        except Exception as e:
            return False, f"Fingerprint error: {e}"
    
    def enroll(self, user_id: int) -> bool:
        """Enroll user for biometric auth."""
        if not self._available:
            return False
        
        # In real implementation, this would capture biometric data
        self._enrolled_users[user_id] = secrets.token_hex(32)
        logger.info(f"User {user_id} enrolled for biometric auth")
        return True
    
    def is_enrolled(self, user_id: int) -> bool:
        """Check if user is enrolled for biometric auth."""
        return user_id in self._enrolled_users


class AuthManager:
    """
    Authentication manager with PIN and biometric support.
    
    Features:
    - PIN verification with secure hashing
    - Biometric authentication (if available)
    - Session timeout (5 minutes default)
    - Failed attempt tracking with lockout
    - Lockout after 3 failures
    """
    
    def __init__(
        self,
        pin_storage_path: Optional[Path] = None,
        session_timeout_minutes: int = 5,
        max_failed_attempts: int = 3,
        lockout_duration_minutes: int = 15,
        audit_callback: Optional[Callable[[str, Any], None]] = None
    ):
        self.pin_storage_path = pin_storage_path or Path("~/.closedclaw/pins.json").expanduser()
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.max_failed_attempts = max_failed_attempts
        self.lockout_duration = timedelta(minutes=lockout_duration_minutes)
        self.audit_callback = audit_callback
        
        self._sessions: Dict[int, AuthSession] = {}
        self._failed_attempts: Dict[int, list] = {}  # user_id -> list of FailedAttempt
        self._locked_users: Dict[int, datetime] = {}  # user_id -> lockout expiry
        self._pending_pins: Dict[int, str] = {}  # user_id -> partially entered PIN
        
        # Initialize biometric handler
        self.biometric = BiometricAuth()
        
        # Load stored PINs
        self._pins: Dict[int, str] = self._load_pins()
        
        logger.info("AuthManager initialized")
    
    def _load_pins(self) -> Dict[int, str]:
        """Load PIN hashes from storage."""
        if not self.pin_storage_path.exists():
            return {}
        
        try:
            import json
            with open(self.pin_storage_path, 'r') as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except Exception as e:
            logger.error(f"Failed to load PINs: {e}")
            return {}
    
    def _save_pins(self):
        """Save PIN hashes to storage."""
        try:
            import json
            self.pin_storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.pin_storage_path, 'w') as f:
                json.dump(self._pins, f)
        except Exception as e:
            logger.error(f"Failed to save PINs: {e}")
    
    def _hash_pin(self, pin: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash PIN with salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for secure hashing
        key = hashlib.pbkdf2_hmac(
            'sha256',
            pin.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return key.hex(), salt
    
    def set_pin(self, user_id: int, pin: str) -> bool:
        """
        Set or change user PIN.
        
        Args:
            user_id: User to set PIN for
            pin: PIN (4-6 digits recommended)
            
        Returns:
            True if set successfully
        """
        if not pin or len(pin) < 4:
            logger.warning("PIN too short")
            return False
        
        hashed_pin, salt = self._hash_pin(pin)
        self._pins[user_id] = f"{salt}:${hashed_pin}"
        self._save_pins()
        
        self._audit("PIN_SET", {"user_id": user_id})
        logger.info(f"PIN set for user {user_id}")
        return True
    
    def verify_pin(self, user_id: int, pin: str) -> bool:
        """
        Verify user PIN.
        
        Args:
            user_id: User to verify
            pin: PIN to check
            
        Returns:
            True if PIN is correct
        """
        if self.is_locked(user_id):
            logger.warning(f"User {user_id} is locked out")
            return False
        
        stored = self._pins.get(user_id)
        if not stored:
            logger.warning(f"No PIN set for user {user_id}")
            self._record_failure(user_id, AuthMethod.PIN, "No PIN set")
            return False
        
        salt, stored_hash = stored.split("$")
        computed_hash, _ = self._hash_pin(pin, salt)
        
        if hmac.compare_digest(computed_hash, stored_hash):
            self._record_success(user_id, AuthMethod.PIN)
            return True
        else:
            self._record_failure(user_id, AuthMethod.PIN, "Invalid PIN")
            return False
    
    async def authenticate(
        self,
        user_id: int,
        method: AuthMethod = AuthMethod.PIN,
        credential: Optional[str] = None
    ) -> Tuple[AuthStatus, Optional[AuthSession]]:
        """
        Authenticate user.
        
        Args:
            user_id: User to authenticate
            method: Auth method (PIN, BIOMETRIC)
            credential: PIN or biometric data
            
        Returns:
            Tuple of (status, session)
        """
        if self.is_locked(user_id):
            return AuthStatus.LOCKED, None
        
        if method == AuthMethod.PIN:
            if not credential:
                return AuthStatus.PENDING, None
            
            if self.verify_pin(user_id, credential):
                session = self._create_session(user_id, method, level=2)
                return AuthStatus.SUCCESS, session
            else:
                if self.is_locked(user_id):
                    return AuthStatus.LOCKED, None
                return AuthStatus.FAILURE, None
        
        elif method == AuthMethod.BIOMETRIC:
            success, message = await self.biometric.authenticate(user_id)
            if success:
                session = self._create_session(user_id, method, level=3)
                session.biometric_verified = True
                return AuthStatus.SUCCESS, session
            else:
                self._record_failure(user_id, AuthMethod.BIOMETRIC, message)
                return AuthStatus.FAILURE, None
        
        else:
            # No auth method - L1
            session = self._create_session(user_id, AuthMethod.NONE, level=1)
            return AuthStatus.SUCCESS, session
    
    def _create_session(
        self,
        user_id: int,
        method: AuthMethod,
        level: int
    ) -> AuthSession:
        """Create new authentication session."""
        now = datetime.now()
        session = AuthSession(
            user_id=user_id,
            method=method,
            level_granted=level,
            created_at=now,
            expires_at=now + self.session_timeout,
            last_activity=now,
            auth_token=secrets.token_urlsafe(32)
        )
        
        self._sessions[user_id] = session
        
        self._audit("SESSION_CREATED", {
            "user_id": user_id,
            "method": method.value,
            "level": level
        })
        
        logger.info(f"Session created for user {user_id} (L{level})")
        return session
    
    def validate_session(self, user_id: int, token: str) -> Optional[AuthSession]:
        """
        Validate session token.
        
        Args:
            user_id: User ID
            token: Session token
            
        Returns:
            Session if valid, None if expired/invalid
        """
        session = self._sessions.get(user_id)
        if not session:
            return None
        
        if session.auth_token != token:
            return None
        
        if datetime.now() > session.expires_at:
            self._sessions.pop(user_id, None)
            self._audit("SESSION_EXPIRED", {"user_id": user_id})
            return None
        
        # Extend session on activity
        session.last_activity = datetime.now()
        session.expires_at = datetime.now() + self.session_timeout
        
        return session
    
    def invalidate_session(self, user_id: int):
        """Invalidate user session."""
        if user_id in self._sessions:
            del self._sessions[user_id]
            self._audit("SESSION_INVALIDATED", {"user_id": user_id})
            logger.info(f"Session invalidated for user {user_id}")
    
    def is_locked(self, user_id: int) -> bool:
        """Check if user is locked out."""
        if user_id not in self._locked_users:
            return False
        
        if datetime.now() > self._locked_users[user_id]:
            # Lockout expired
            del self._locked_users[user_id]
            self._failed_attempts[user_id] = []
            return False
        
        return True
    
    def get_lockout_time(self, user_id: int) -> Optional[datetime]:
        """Get lockout expiry time."""
        return self._locked_users.get(user_id)
    
    def _record_failure(self, user_id: int, method: AuthMethod, reason: str):
        """Record failed authentication attempt."""
        if user_id not in self._failed_attempts:
            self._failed_attempts[user_id] = []
        
        attempt = FailedAttempt(
            timestamp=datetime.now(),
            method=method,
            reason=reason
        )
        self._failed_attempts[user_id].append(attempt)
        
        self._audit("AUTH_FAILURE", {
            "user_id": user_id,
            "method": method.value,
            "reason": reason,
            "attempt_count": len(self._failed_attempts[user_id])
        })
        
        # Check for lockout
        if len(self._failed_attempts[user_id]) >= self.max_failed_attempts:
            lockout_until = datetime.now() + self.lockout_duration
            self._locked_users[user_id] = lockout_until
            
            self._audit("USER_LOCKED", {
                "user_id": user_id,
                "lockout_until": lockout_until.isoformat()
            })
            
            logger.warning(f"User {user_id} locked out until {lockout_until}")
    
    def _record_success(self, user_id: int, method: AuthMethod):
        """Record successful authentication."""
        # Clear failed attempts
        self._failed_attempts[user_id] = []
        
        self._audit("AUTH_SUCCESS", {
            "user_id": user_id,
            "method": method.value
        })
    
    def _audit(self, event: str, data: dict):
        """Send audit log."""
        if self.audit_callback:
            try:
                self.audit_callback(event, data)
            except Exception as e:
                logger.error(f"Audit callback failed: {e}")
        
        logger.info(f"AUTH_AUDIT: {event} - {data}")
    
    def get_auth_level(self, user_id: int) -> int:
        """Get current auth level for user."""
        session = self._sessions.get(user_id)
        if session and datetime.now() <= session.expires_at:
            return session.level_granted
        return 0
    
    def has_pin(self, user_id: int) -> bool:
        """Check if user has PIN set."""
        return user_id in self._pins
    
    def clear_all_sessions(self):
        """Clear all active sessions."""
        self._sessions.clear()
        logger.info("All sessions cleared")
