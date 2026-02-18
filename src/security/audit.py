"""
Audit Logging Module - Tamper-resistant audit trail
Logs all actions with timestamps for security monitoring
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from functools import wraps
import threading


class AuditLogger:
    """
    Tamper-resistant audit logging system.
    - Logs every action with timestamp
    - Logs permission checks
    - Logs data access
    - Logs errors
    - Log rotation (keep 30 days)
    """
    
    def __init__(self, log_dir: str = "~/closed-claw/logs/audit"):
        self.log_dir = Path(log_dir).expanduser()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Separate current and archived logs
        self.current_log = self.log_dir / "audit_current.log"
        self.archive_dir = self.log_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
        
        # Integrity check file
        self.integrity_file = self.log_dir / ".integrity"
        
        # Thread-safe logging
        self._lock = threading.Lock()
        
        # Setup rotation
        self._setup_rotation()
        
    def _setup_rotation(self):
        """Setup daily log rotation (keep 30 days)"""
        # Rotate if current log is from a different day
        if self.current_log.exists():
            mtime = datetime.fromtimestamp(self.current_log.stat().st_mtime)
            if mtime.date() != datetime.now().date():
                self._rotate_log()
        
        # Clean old logs
        self._clean_old_logs()
    
    def _rotate_log(self):
        """Rotate current log to archive"""
        if not self.current_log.exists():
            return
            
        timestamp = datetime.fromtimestamp(
            self.current_log.stat().st_mtime
        ).strftime("%Y%m%d")
        archive_path = self.archive_dir / f"audit_{timestamp}.log"
        
        # Add integrity hash before archiving
        self._add_integrity_hash(self.current_log)
        
        # Move to archive
        self.current_log.rename(archive_path)
        
    def _clean_old_logs(self):
        """Remove logs older than 30 days"""
        cutoff = datetime.now() - timedelta(days=30)
        
        for log_file in self.archive_dir.glob("audit_*.log"):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff:
                    log_file.unlink()
            except OSError:
                pass
    
    def _add_integrity_hash(self, log_file: Path):
        """Add SHA-256 hash for tamper detection"""
        if not log_file.exists():
            return
            
        with open(log_file, 'rb') as f:
            content = f.read()
        
        hash_value = hashlib.sha256(content).hexdigest()
        timestamp = datetime.now().isoformat()
        
        integrity_entry = {
            "file": str(log_file.name),
            "hash": hash_value,
            "timestamp": timestamp
        }
        
        with open(self.integrity_file, 'a') as f:
            f.write(json.dumps(integrity_entry) + '\n')
    
    def _verify_integrity(self, log_file: Path) -> bool:
        """Verify log file integrity"""
        if not log_file.exists() or not self.integrity_file.exists():
            return True
            
        with open(log_file, 'rb') as f:
            current_hash = hashlib.sha256(f.read()).hexdigest()
        
        with open(self.integrity_file, 'r') as f:
            for line in f:
                entry = json.loads(line.strip())
                if entry.get("file") == log_file.name:
                    return entry.get("hash") == current_hash
        
        return True
    
    def log(self, action: str, category: str, details: Dict[str, Any], 
            user: str = "system", success: bool = True):
        """
        Log an action to the audit trail
        
        Args:
            action: The action performed
            category: Category (permission_check, data_access, error, etc.)
            details: Additional details
            user: User/system performing action
            success: Whether action succeeded
        """
        with self._lock:
            self._setup_rotation()
            
            entry = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "category": category,
                "user": user,
                "success": success,
                "details": details
            }
            
            try:
                with open(self.current_log, 'a') as f:
                    f.write(json.dumps(entry) + '\n')
            except Exception as e:
                # Fallback to stderr if file logging fails
                print(f"AUDIT LOG ERROR: {e}", flush=True)
    
    def log_permission_check(self, resource: str, action: str, 
                            granted: bool, user: str = "system"):
        """Log a permission check"""
        self.log(
            action=f"permission_check:{action}",
            category="permission",
            details={"resource": resource, "granted": granted},
            user=user,
            success=granted
        )
    
    def log_data_access(self, data_type: str, operation: str, 
                       record_id: Optional[str] = None, user: str = "system"):
        """Log data access"""
        self.log(
            action=f"data_access:{operation}",
            category="data_access",
            details={
                "data_type": data_type,
                "record_id": record_id or "bulk"
            },
            user=user,
            success=True
        )
    
    def log_error(self, error_type: str, message: str, 
                 details: Optional[Dict] = None, user: str = "system"):
        """Log an error"""
        self.log(
            action=f"error:{error_type}",
            category="error",
            details={
                "message": message,
                "extra": details or {}
            },
            user=user,
            success=False
        )
    
    def log_security_event(self, event_type: str, severity: str,
                          details: Dict[str, Any], user: str = "system"):
        """Log security-related events"""
        self.log(
            action=f"security:{event_type}",
            category="security",
            details={
                "severity": severity,
                **details
            },
            user=user,
            success=(severity != "critical")
        )
    
    def get_recent_logs(self, hours: int = 24) -> list:
        """Get logs from the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        logs = []
        
        if self.current_log.exists():
            with open(self.current_log, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        if entry_time > cutoff:
                            logs.append(entry)
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def audit_action(category: str, action_name: Optional[str] = None):
    """
    Decorator to automatically audit function calls
    
    Usage:
        @audit_action("data_access")
        def read_user_data(user_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_audit_logger()
            action = action_name or func.__name__
            
            try:
                result = func(*args, **kwargs)
                logger.log(
                    action=action,
                    category=category,
                    details={"args": str(args), "kwargs": str(kwargs)},
                    success=True
                )
                return result
            except Exception as e:
                logger.log(
                    action=action,
                    category=category,
                    details={
                        "args": str(args),
                        "kwargs": str(kwargs),
                        "error": str(e)
                    },
                    success=False
                )
                raise
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test the audit logger
    logger = AuditLogger()
    
    logger.log_permission_check("user_data", "read", True)
    logger.log_data_access("messages", "query", "12345")
    logger.log_error("database", "Connection failed")
    logger.log_security_event("suspicious_access", "high", 
                              {"ip": "192.168.1.1"})
    
    print("Audit logs:", logger.get_recent_logs())
