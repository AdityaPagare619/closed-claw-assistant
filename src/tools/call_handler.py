"""
Call detection and control module using Termux:API.
Handles incoming calls, auto-pickup, and call state monitoring.
"""

import subprocess
import time
import json
import re
from enum import Enum
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CallState(Enum):
    """Enumeration of possible call states."""
    IDLE = "idle"
    RINGING = "ringing"
    OFFHOOK = "offhook"
    DISCONNECTED = "disconnected"
    UNKNOWN = "unknown"


class DetectionMethod(Enum):
    """Available methods for call detection."""
    TERMUX_API = "termux-api"
    ADB = "adb"
    TELEPHONY_LOG = "telephony-log"
    NONE = "none"


@dataclass
class CallInfo:
    """Data class to hold call information."""
    phone_number: Optional[str] = None
    state: CallState = CallState.UNKNOWN
    timestamp: Optional[datetime] = None
    display_name: Optional[str] = None
    call_duration: int = 0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CallHandler:
    """
    Handles call detection, monitoring, and control via Termux:API.
    
    Features:
    - Detect incoming calls
    - Monitor call state changes
    - Auto-pickup after configurable delay
    - Reject calls
    - Get caller information
    """
    
    def __init__(self, pickup_delay: int = 20):
        """
        Initialize the CallHandler.
        
        Args:
            pickup_delay: Seconds to wait before auto-picking up (default: 20)
        """
        self.pickup_delay = pickup_delay
        self.detection_method = self._detect_method()
        self.current_call: Optional[CallInfo] = None
        self.state_callbacks: list[Callable[[CallState, CallInfo], None]] = []
        self._running = False
        self._ringing_start_time: Optional[float] = None
        
        logger.info(f"CallHandler initialized with {self.detection_method.value} method")
    
    def _detect_method(self) -> DetectionMethod:
        """Detect available call detection method."""
        # Check for Termux:API
        try:
            result = subprocess.run(
                ['termux-telephony-deviceinfo'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("Termux:API detected")
                return DetectionMethod.TERMUX_API
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for ADB
        try:
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if 'device' in result.stdout:
                logger.info("ADB detected")
                return DetectionMethod.ADB
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.warning("No call detection method available")
        return DetectionMethod.NONE
    
    def _get_call_state_termux(self) -> CallInfo:
        """Get current call state using Termux:API."""
        try:
            # Get device info which includes call state
            result = subprocess.run(
                ['termux-telephony-deviceinfo'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                state_str = data.get('call_state', 'UNKNOWN').lower()
                
                state_map = {
                    'idle': CallState.IDLE,
                    'ringing': CallState.RINGING,
                    'offhook': CallState.OFFHOOK,
                    'disconnected': CallState.DISCONNECTED,
                }
                
                return CallInfo(
                    state=state_map.get(state_str, CallState.UNKNOWN),
                    timestamp=datetime.now()
                )
        except Exception as e:
            logger.error(f"Error getting call state: {e}")
        
        return CallInfo(state=CallState.UNKNOWN)
    
    def _get_call_state_adb(self) -> CallInfo:
        """Get current call state using ADB."""
        try:
            result = subprocess.run(
                ['adb', 'shell', 'dumpsys', 'telephony.registry'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout
            
            if 'mCallState=1' in output:
                return CallInfo(state=CallState.RINGING)
            elif 'mCallState=2' in output:
                return CallInfo(state=CallState.OFFHOOK)
            else:
                return CallInfo(state=CallState.IDLE)
                
        except Exception as e:
            logger.error(f"Error getting ADB call state: {e}")
        
        return CallInfo(state=CallState.UNKNOWN)
    
    def get_call_state(self) -> CallInfo:
        """Get current call state using available method."""
        if self.detection_method == DetectionMethod.TERMUX_API:
            return self._get_call_state_termux()
        elif self.detection_method == DetectionMethod.ADB:
            return self._get_call_state_adb()
        else:
            return CallInfo(state=CallState.UNKNOWN)
    
    def get_caller_number(self) -> Optional[str]:
        """Get the incoming caller's phone number."""
        if self.detection_method == DetectionMethod.TERMUX_API:
            try:
                result = subprocess.run(
                    ['termux-telephony-call'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                # Parse output for caller number
                match = re.search(r'(\+?[\d\s-]{10,})', result.stdout)
                if match:
                    return match.group(1).strip()
                    
            except Exception as e:
                logger.error(f"Error getting caller number: {e}")
        
        return None
    
    def pickup_call(self) -> bool:
        """
        Pickup the incoming call.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.detection_method == DetectionMethod.TERMUX_API:
                # Use input keyevent to simulate headset button (pickup)
                result = subprocess.run(
                    ['termux-media-player', 'play', '/dev/null'],  # Dummy to trigger
                    capture_output=True,
                    timeout=5
                )
                
                # Alternative: use input keyevent 79 (headset hook)
                subprocess.run(
                    ['input', 'keyevent', '79'],
                    capture_output=True,
                    timeout=5
                )
                
                logger.info("Call picked up")
                return True
                
            elif self.detection_method == DetectionMethod.ADB:
                result = subprocess.run(
                    ['adb', 'shell', 'input', 'keyevent', '79'],
                    capture_output=True,
                    timeout=5
                )
                return result.returncode == 0
                
        except Exception as e:
            logger.error(f"Error picking up call: {e}")
        
        return False
    
    def reject_call(self) -> bool:
        """
        Reject the incoming call.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.detection_method == DetectionMethod.TERMUX_API:
                # Use ENDCALL keyevent
                subprocess.run(
                    ['input', 'keyevent', '6'],
                    capture_output=True,
                    timeout=5
                )
                
                logger.info("Call rejected")
                return True
                
            elif self.detection_method == DetectionMethod.ADB:
                result = subprocess.run(
                    ['adb', 'shell', 'input', 'keyevent', '6'],
                    capture_output=True,
                    timeout=5
                )
                return result.returncode == 0
                
        except Exception as e:
            logger.error(f"Error rejecting call: {e}")
        
        return False
    
    def register_callback(self, callback: Callable[[CallState, CallInfo], None]):
        """Register a callback for state changes."""
        self.state_callbacks.append(callback)
    
    def _notify_state_change(self, state: CallState, call_info: CallInfo):
        """Notify all registered callbacks of state change."""
        for callback in self.state_callbacks:
            try:
                callback(state, call_info)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def monitor_calls(self):
        """
        Main loop to monitor calls and handle auto-pickup.
        Runs until stop() is called.
        """
        self._running = True
        previous_state = CallState.IDLE
        
        logger.info("Starting call monitoring...")
        
        while self._running:
            try:
                call_info = self.get_call_state()
                current_state = call_info.state
                
                # Detect state changes
                if current_state != previous_state:
                    logger.info(f"Call state changed: {previous_state.value} -> {current_state.value}")
                    
                    if current_state == CallState.RINGING:
                        self._ringing_start_time = time.time()
                        call_info.phone_number = self.get_caller_number()
                        self.current_call = call_info
                        logger.info(f"Incoming call from: {call_info.phone_number or 'Unknown'}")
                    
                    elif current_state == CallState.OFFHOOK and previous_state == CallState.RINGING:
                        logger.info("Call answered")
                    
                    elif current_state == CallState.IDLE and previous_state == CallState.OFFHOOK:
                        logger.info("Call ended")
                        self.current_call = None
                    
                    self._notify_state_change(current_state, call_info)
                    previous_state = current_state
                
                # Handle auto-pickup
                if (current_state == CallState.RINGING and 
                    self._ringing_start_time is not None):
                    
                    elapsed = time.time() - self._ringing_start_time
                    
                    if elapsed >= self.pickup_delay:
                        logger.info(f"Auto-pickup triggered after {elapsed:.1f}s")
                        if self.pickup_call():
                            self._ringing_start_time = None
                
                time.sleep(0.5)  # Poll every 500ms
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(1)
    
    def stop(self):
        """Stop the call monitoring loop."""
        self._running = False
        logger.info("Call monitoring stopped")
    
    def is_running(self) -> bool:
        """Check if monitoring is active."""
        return self._running


if __name__ == "__main__":
    # Test the handler
    handler = CallHandler(pickup_delay=20)
    
    def on_state_change(state: CallState, info: CallInfo):
        print(f"State: {state.value}, Number: {info.phone_number}")
    
    handler.register_callback(on_state_change)
    
    try:
        handler.monitor_calls()
    except KeyboardInterrupt:
        handler.stop()
