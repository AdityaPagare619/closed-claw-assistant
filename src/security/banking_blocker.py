"""
Banking Blocker Module - Financial App and Data Protection
Blocks access to banking apps, financial SMS, and UPI data
"""

import os
import re
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging


class AlertLevel(Enum):
    """Security alert levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class SecurityAlert:
    """Security alert data structure"""
    timestamp: str
    level: AlertLevel
    category: str
    message: str
    details: Dict


class BankingBlocker:
    """
    Blocks access to banking and financial applications/data.
    
    Features:
    - Blocked banking app detection
    - Financial SMS blocking
    - UPI keyword filtering
    - Security alerts on attempted access
    """
    
    # Blocked banking and payment apps (package names and directories)
    BLOCKED_APPS: Set[str] = {
        # UPI Apps
        "com.phonepe.app", "com.phonepe.app.v4",
        "com.google.android.apps.nbu.paisa.user",  # GPay
        "net.one97.paytm", "com.paytm.app",
        "in.org.npci.upiapp",  # BHIM
        "com.cred.app", "com.dreamplug.androidapp",
        "com.mobikwik_new", "com.freecharge.android",
        "in.amazon.mShop.android.shopping",  # Amazon Pay
        "com.paypal.android.p2pmobile",
        "com.hdfcbank.payzapp",
        "com.samsung.android.samsungpay",
        
        # Banking Apps
        "com.snapwork.hdfc", "com.hdfcbank.mobilebanking",
        "com.sbi.SBIFreedomPlus", "com.sbi.lotusintouch",
        "com.icicibank.iciciapp", "com.icicibank.imobile",
        "com.axis.mobile", "com.axis.netbanking",
        "com.kotak.kotakmobilebanking",
        "com.pnb.android", "com.bankofbaroda.mconnect",
        "com.canarabank.mobility",
        "com.unionbank.ecommerce",
        "com.idbi", "com.idbi.mpassbook",
        "com.bobcard.bobcard",
        "com.bandhan.bank",
        "com.yesbank.yesonline",
        
        # Wallets
        "com.whatsapp.w4b",  # WhatsApp Business
        "com.google.android.apps.walletnfcrel",
        "com.samsung.android.spaymini",
    }
    
    # Blocked app display names (for detection)
    BLOCKED_APP_NAMES: Set[str] = {
        "phonepe", "google pay", "gpay", "paytm",
        "bhim", "cred", "mobikwik", "freecharge",
        "amazon pay", "paypal", "payzapp", "samsung pay",
        "hdfc bank", "sbi", "icici", "axis", "kotak",
        "pnb", "bob", "bank of baroda", "canara bank",
        "union bank", "idbi", "yes bank", "bandhan bank",
        "upi", "wallet", "tez", "lime", "pingpay",
    }
    
    # UPI-related keywords to block
    UPI_KEYWORDS: Set[str] = {
        "upi", "vpa", "virtual payment address",
        "@oksbi", "@okhdfcbank", "@okicici", "@okaxis",
        "@paytm", "@upi", "@ybl", "@ibl",
        "@kotak", "@axl", "@apl", "@indus",
        "upi pin", "upi id", "qr code payment",
        "scan and pay", "upi transaction",
    }
    
    # Financial SMS patterns
    FINANCIAL_SMS_PATTERNS: List[str] = [
        r"\b(?:rs|inr|₹)\s*\.?\s*[\d,]+(?:\.\d{2})?\b",  # Currency amounts
        r"\b(?:credited|debited|withdrawn|transferred)\b",
        r"\b(?:account|a/c|acct)\s*(?:no|number)?[:\s]*\d+",
        r"\b(?:available\s*balance|avlbl\s*bal)\b",
        r"\bupi\s*(?:ref|reference|txn|transaction)\s*[:\s]*\w+",
        r"\b(?:imps|neft|rtgs)\s*(?:ref|reference)?\b",
        r"\b(?:otp|one.?time.?password)\s*(?:is)?[:\s]*\d+",
    ]
    
    # Sensitive data patterns
    SENSITIVE_PATTERNS: Dict[str, str] = {
        "account_number": r"\b\d{9,18}\b",
        "card_number": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "cvv": r"\bcvv[:\s]*\d{3,4}\b",
        "otp": r"\b(?:otp|pin)[:\s]*\d{4,6}\b",
        "upi_id": r"\b[\w.-]+@[\w]+\b",
        "ifsc": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._alert_handlers: List[callable] = []
        self._block_count = 0
        
        # Compile SMS patterns
        self._sms_patterns = [
            re.compile(p, re.IGNORECASE) 
            for p in self.FINANCIAL_SMS_PATTERNS
        ]
        
        # Compile sensitive patterns
        self._sensitive_patterns = {
            k: re.compile(v, re.IGNORECASE)
            for k, v in self.SENSITIVE_PATTERNS.items()
        }
    
    def add_alert_handler(self, handler: callable):
        """Add handler for security alerts"""
        self._alert_handlers.append(handler)
    
    def _trigger_alert(self, level: AlertLevel, category: str, 
                      message: str, details: Dict):
        """Trigger security alert"""
        alert = SecurityAlert(
            timestamp=datetime.now().isoformat(),
            level=level,
            category=category,
            message=message,
            details=details
        )
        
        self.logger.warning(f"SECURITY ALERT [{level.value}]: {message}")
        
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler failed: {e}")
    
    def is_banking_app(self, package_name: str) -> bool:
        """Check if package is a banking/payment app"""
        pkg_lower = package_name.lower()
        
        # Check exact matches
        if pkg_lower in self.BLOCKED_APPS:
            return True
        
        # Check partial matches
        for blocked in self.BLOCKED_APPS:
            if blocked in pkg_lower or pkg_lower in blocked:
                return True
        
        return False
    
    def check_app_access(self, package_name: str, 
                        action: str = "access") -> Tuple[bool, Optional[str]]:
        """
        Check if app access is allowed
        
        Returns:
            (allowed, reason) tuple
        """
        if self.is_banking_app(package_name):
            self._block_count += 1
            self._trigger_alert(
                level=AlertLevel.CRITICAL,
                category="app_blocked",
                message=f"Blocked {action} to banking app: {package_name}",
                details={"package": package_name, "action": action}
            )
            return False, f"Access to banking app '{package_name}' is blocked"
        
        return True, None
    
    def contains_upi_keywords(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check if text contains UPI keywords
        
        Returns:
            (has_keywords, found_keywords) tuple
        """
        text_lower = text.lower()
        found = []
        
        for keyword in self.UPI_KEYWORDS:
            if keyword in text_lower:
                found.append(keyword)
        
        return len(found) > 0, found
    
    def is_financial_sms(self, message: str) -> Tuple[bool, float]:
        """
        Check if SMS is financial in nature
        
        Returns:
            (is_financial, confidence_score) tuple
        """
        matches = 0
        
        for pattern in self._sms_patterns:
            if pattern.search(message):
                matches += 1
        
        confidence = matches / len(self._sms_patterns)
        is_financial = confidence > 0.3 or matches >= 2
        
        if is_financial:
            self._trigger_alert(
                level=AlertLevel.WARNING,
                category="financial_sms_blocked",
                message="Blocked access to financial SMS",
                details={"matches": matches, "confidence": confidence}
            )
        
        return is_financial, confidence
    
    def redact_sensitive_data(self, text: str) -> str:
        """
        Redact sensitive financial data from text
        
        Returns:
            Text with sensitive data replaced
        """
        redacted = text
        
        for data_type, pattern in self._sensitive_patterns.items():
            redacted = pattern.sub(f"[{data_type.upper()}_REDACTED]", redacted)
        
        # Also redact UPI IDs
        upi_pattern = self._sensitive_patterns.get("upi_id")
        if upi_pattern:
            redacted = upi_pattern.sub("[UPI_ID_REDACTED]", redacted)
        
        return redacted
    
    def scan_text(self, text: str) -> Dict:
        """
        Comprehensive text scan for financial data
        
        Returns:
            Scan report dictionary
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "has_upi_keywords": False,
            "upi_keywords_found": [],
            "is_financial_sms": False,
            "financial_sms_confidence": 0.0,
            "sensitive_data_found": {},
            "action_taken": "none"
        }
        
        # Check UPI keywords
        has_upi, keywords = self.contains_upi_keywords(text)
        report["has_upi_keywords"] = has_upi
        report["upi_keywords_found"] = keywords
        
        # Check for financial SMS patterns
        is_financial, confidence = self.is_financial_sms(text)
        report["is_financial_sms"] = is_financial
        report["financial_sms_confidence"] = confidence
        
        # Check for sensitive data
        for data_type, pattern in self._sensitive_patterns.items():
            matches = pattern.findall(text)
            if matches:
                report["sensitive_data_found"][data_type] = len(matches)
        
        # Determine action
        if is_financial or has_upi:
            report["action_taken"] = "blocked"
            self._trigger_alert(
                level=AlertLevel.CRITICAL,
                category="financial_data_detected",
                message="Financial data detected and blocked",
                details=report
            )
        elif report["sensitive_data_found"]:
            report["action_taken"] = "redacted"
        
        return report
    
    def get_stats(self) -> Dict:
        """Get blocking statistics"""
        return {
            "total_blocks": self._block_count,
            "blocked_apps": len(self.BLOCKED_APPS),
            "blocked_keywords": len(self.UPI_KEYWORDS),
            "patterns_active": len(self.FINANCIAL_SMS_PATTERNS)
        }


# Global blocker instance
_blocker: Optional[BankingBlocker] = None


def get_banking_blocker() -> BankingBlocker:
    """Get or create global banking blocker"""
    global _blocker
    if _blocker is None:
        _blocker = BankingBlocker()
    return _blocker


if __name__ == "__main__":
    # Test banking blocker
    blocker = BankingBlocker()
    
    # Define test alert handler
    def print_alert(alert):
        print(f"ALERT: [{alert.level.value}] {alert.message}")
    
    blocker.add_alert_handler(print_alert)
    
    # Test app blocking
    print("\n=== Testing App Blocking ===")
    test_apps = [
        "com.phonepe.app",
        "com.google.android.apps.nbu.paisa.user",
        "com.whatsapp",
        "com.android.settings"
    ]
    
    for app in test_apps:
        allowed, reason = blocker.check_app_access(app)
        status = "ALLOWED" if allowed else "BLOCKED"
        print(f"{app}: {status}")
    
    # Test SMS scanning
    print("\n=== Testing SMS Scanning ===")
    test_messages = [
        "Your a/c XX1234 credited with Rs.5000. Avl Bal: Rs.25000",
        "UPI txn of Rs.100 to test@okaxis successful",
        "Hello, how are you today?",
        "OTP for transaction is 123456",
    ]
    
    for msg in test_messages:
        report = blocker.scan_text(msg)
        action = report["action_taken"]
        print(f"Message: {msg[:40]}... -> Action: {action}")
    
    # Test redaction
    print("\n=== Testing Data Redaction ===")
    sensitive_text = "My account 12345678901 and UPI id test@okaxis"
    redacted = blocker.redact_sensitive_data(sensitive_text)
    print(f"Original: {sensitive_text}")
    print(f"Redacted: {redacted}")
    
    print("\n=== Stats ===")
    print(blocker.get_stats())
