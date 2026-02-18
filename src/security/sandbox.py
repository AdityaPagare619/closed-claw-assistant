"""
Sandbox Module - Data Isolation and Path Security
Restricts file access to safe directories and prevents data leakage
"""

import os
import re
from pathlib import Path
from typing import Optional, Set, List
import logging


class SandboxError(Exception):
    """Raised when sandbox policy is violated"""
    pass


class Sandbox:
    """
    File system sandbox for data isolation.
    
    Security features:
    - Restrict file access to ~/closed-claw/
    - Block banking app directories
    - Block sensitive file patterns
    - Path validation (no traversal)
    - Symlink protection
    """
    
    # Blocked banking and financial apps/directories
    BLOCKED_PATTERNS = [
        # Banking apps
        r"phonepe", r"gpay", r"googlepay", r"paytm",
        r"bhim", r"cred", r"mobikwik", r"freecharge",
        r"amazonpay", r"paypal", r"payzapp",
        # Bank apps
        r"hdfc", r"sbi", r"icici", r"axis", r"kotak",
        r"pnb", r"bob", r"canara", r"union", r"idbi",
        # UPI and wallets
        r"upi", r"wallet", r"tez", r"lime", r"pingpay",
        # Financial data
        r"transactions", r"statements", r"passbook",
    ]
    
    # Sensitive file patterns to block
    BLOCKED_FILE_PATTERNS = [
        r"\.bank$", r"\.upi$", r"\.wallet$",
        r"statement", r"transaction", r"passbook",
        r"account_details", r"card_details",
    ]
    
    # Allowed base directory
    ALLOWED_BASE = "~/closed-claw"
    
    def __init__(self, allowed_base: Optional[str] = None):
        self.allowed_base = Path(
            allowed_base or self.ALLOWED_BASE
        ).expanduser().resolve()
        
        # Ensure allowed directory exists
        self.allowed_base.mkdir(parents=True, exist_ok=True)
        
        # Compile regex patterns for performance
        self._blocked_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.BLOCKED_PATTERNS
        ]
        self._blocked_file_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.BLOCKED_FILE_PATTERNS
        ]
        
        self.logger = logging.getLogger(__name__)
    
    def _resolve_path(self, path: str) -> Path:
        """
        Resolve path with symlink protection
        
        Raises:
            SandboxError: If path contains symlinks or is invalid
        """
        path_obj = Path(path).expanduser()
        
        # Check for symlinks in any component of the path
        for part in path_obj.parts:
            part_path = Path(part)
            if part_path.is_symlink():
                raise SandboxError(
                    f"Symlink detected in path: {path}"
                )
        
        # Resolve to absolute path
        try:
            resolved = path_obj.resolve()
        except (OSError, RuntimeError) as e:
            raise SandboxError(f"Invalid path: {path} - {e}")
        
        return resolved
    
    def _check_path_traversal(self, resolved_path: Path) -> bool:
        """
        Check for path traversal attacks
        
        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Path should be within allowed base after resolution
            resolved_path.relative_to(self.allowed_base)
            return True
        except ValueError:
            return False
    
    def _check_blocked_patterns(self, path: Path) -> bool:
        """
        Check if path matches blocked banking/financial patterns
        
        Returns:
            True if path is safe, False if blocked
        """
        path_str = str(path).lower()
        
        # Check directory patterns
        for pattern in self._blocked_patterns:
            if pattern.search(path_str):
                self.logger.warning(
                    f"Blocked path matching banking pattern: {path}"
                )
                return False
        
        # Check file patterns
        if path.is_file():
            for pattern in self._blocked_file_patterns:
                if pattern.search(path.name):
                    self.logger.warning(
                        f"Blocked file matching sensitive pattern: {path}"
                    )
                    return False
        
        return True
    
    def validate_path(self, path: str, for_write: bool = False) -> Path:
        """
        Validate a path for sandbox access
        
        Args:
            path: The path to validate
            for_write: Whether this is for write operation
            
        Returns:
            Resolved Path object if valid
            
        Raises:
            SandboxError: If path violates sandbox policy
        """
        # Resolve path
        try:
            resolved = self._resolve_path(path)
        except SandboxError:
            raise
        
        # Check path traversal
        if not self._check_path_traversal(resolved):
            raise SandboxError(
                f"Path traversal detected: {path} resolves outside "
                f"allowed directory {self.allowed_base}"
            )
        
        # Check blocked patterns
        if not self._check_blocked_patterns(resolved):
            raise SandboxError(
                f"Access to banking/financial path blocked: {path}"
            )
        
        self.logger.debug(f"Path validated: {resolved}")
        return resolved
    
    def safe_open(self, path: str, mode: str = 'r', **kwargs):
        """
        Safely open a file within sandbox
        
        Args:
            path: File path
            mode: File mode (read/write)
            **kwargs: Additional arguments for open()
            
        Returns:
            File handle
            
        Raises:
            SandboxError: If file access is not allowed
        """
        resolved = self.validate_path(path, for_write='w' in mode)
        
        # Ensure parent directory exists for writes
        if 'w' in mode or 'a' in mode:
            resolved.parent.mkdir(parents=True, exist_ok=True)
        
        return open(resolved, mode, **kwargs)
    
    def safe_read(self, path: str) -> str:
        """Safely read file contents"""
        with self.safe_open(path, 'r') as f:
            return f.read()
    
    def safe_write(self, path: str, content: str):
        """Safely write file contents"""
        with self.safe_open(path, 'w') as f:
            f.write(content)
    
    def safe_listdir(self, path: str = ".") -> List[str]:
        """Safely list directory contents"""
        resolved = self.validate_path(path)
        
        items = []
        for item in resolved.iterdir():
            # Filter out blocked patterns
            if self._check_blocked_patterns(item):
                items.append(item.name)
        
        return items
    
    def safe_exists(self, path: str) -> bool:
        """Safely check if path exists"""
        try:
            resolved = self.validate_path(path)
            return resolved.exists()
        except SandboxError:
            return False
    
    def safe_makedirs(self, path: str, exist_ok: bool = True):
        """Safely create directories"""
        resolved = self.validate_path(path, for_write=True)
        resolved.mkdir(parents=True, exist_ok=exist_ok)
    
    def is_in_sandbox(self, path: str) -> bool:
        """Check if path is within sandbox boundaries"""
        try:
            self.validate_path(path)
            return True
        except SandboxError:
            return False


# Global sandbox instance
_sandbox: Optional[Sandbox] = None


def get_sandbox() -> Sandbox:
    """Get or create global sandbox"""
    global _sandbox
    if _sandbox is None:
        _sandbox = Sandbox()
    return _sandbox


def configure_sandbox(allowed_base: str):
    """Configure global sandbox with custom base directory"""
    global _sandbox
    _sandbox = Sandbox(allowed_base)


if __name__ == "__main__":
    # Test sandbox
    sb = Sandbox()
    
    # Test allowed paths
    print("Testing allowed paths...")
    try:
        sb.validate_path("~/closed-claw/test.txt")
        print("✓ Allowed path accepted")
    except SandboxError as e:
        print(f"✗ Failed: {e}")
    
    # Test blocked paths
    print("\nTesting blocked paths...")
    blocked_tests = [
        "~/phonepe/data.txt",
        "~/closed-claw/../../../etc/passwd",
        "~/gpay/wallet.json",
    ]
    
    for test_path in blocked_tests:
        try:
            sb.validate_path(test_path)
            print(f"✗ {test_path} - Should have been blocked!")
        except SandboxError as e:
            print(f"✓ {test_path} - Correctly blocked")
    
    print("\nSandbox tests complete!")
