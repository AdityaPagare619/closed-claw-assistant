"""
State Manager Module
Manages agent state transitions and battery optimization.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent operational states."""
    IDLE = auto()
    BUSY = auto()
    SLEEPING = auto()


@dataclass
class StateConfig:
    """Configuration for state management."""
    sleep_after_idle_seconds: float = 300.0  # 5 minutes
    wake_on_event: bool = True
    battery_optimization: bool = True


class StateManager:
    """
    Manages agent state machine with battery optimization.
    
    States:
        - IDLE: Ready to process events, components loaded
        - BUSY: Actively processing tasks
        - SLEEPING: Low power mode, components unloaded
    """
    
    def __init__(self, config: Optional[StateConfig] = None):
        self.config = config or StateConfig()
        self._state = AgentState.IDLE
        self._state_changed_at = datetime.now()
        self._last_activity_at = datetime.now()
        self._lock = asyncio.Lock()
        self._callbacks: dict[AgentState, list[Callable]] = {
            state: [] for state in AgentState
        }
        self._sleep_task: Optional[asyncio.Task] = None
        
        logger.info("StateManager initialized")
    
    @property
    def current_state(self) -> AgentState:
        """Get current agent state."""
        return self._state
    
    @property
    def is_idle(self) -> bool:
        """Check if agent is idle."""
        return self._state == AgentState.IDLE
    
    @property
    def is_busy(self) -> bool:
        """Check if agent is busy."""
        return self._state == AgentState.BUSY
    
    @property
    def is_sleeping(self) -> bool:
        """Check if agent is sleeping."""
        return self._state == AgentState.SLEEPING
    
    @property
    def idle_duration(self) -> float:
        """Get duration in seconds since last activity."""
        return (datetime.now() - self._last_activity_at).total_seconds()
    
    def register_callback(self, state: AgentState, callback: Callable) -> None:
        """Register a callback for state changes."""
        self._callbacks[state].append(callback)
        logger.debug(f"Registered callback for state {state.name}")
    
    async def _notify_callbacks(self, state: AgentState) -> None:
        """Notify all callbacks for a state change."""
        for callback in self._callbacks[state]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(state)
                else:
                    callback(state)
            except Exception as e:
                logger.error(f"State callback error: {e}")
    
    async def transition_to(self, new_state: AgentState) -> None:
        """Transition to a new state."""
        async with self._lock:
            if self._state == new_state:
                return
            
            old_state = self._state
            self._state = new_state
            self._state_changed_at = datetime.now()
            
            if new_state == AgentState.BUSY:
                self._last_activity_at = datetime.now()
                if self._sleep_task:
                    self._sleep_task.cancel()
                    self._sleep_task = None
            
            logger.info(f"State transition: {old_state.name} -> {new_state.name}")
            await self._notify_callbacks(new_state)
    
    async def set_busy(self) -> None:
        """Transition to busy state."""
        await self.transition_to(AgentState.BUSY)
    
    async def set_idle(self) -> None:
        """Transition to idle state."""
        await self.transition_to(AgentState.IDLE)
        if self.config.battery_optimization:
            self._schedule_sleep()
    
    async def set_sleeping(self) -> None:
        """Transition to sleeping state."""
        await self.transition_to(AgentState.SLEEPING)
    
    def _schedule_sleep(self) -> None:
        """Schedule transition to sleep after idle timeout."""
        if self._sleep_task:
            self._sleep_task.cancel()
        
        async def sleep_after_timeout():
            await asyncio.sleep(self.config.sleep_after_idle_seconds)
            await self.set_sleeping()
        
        self._sleep_task = asyncio.create_task(sleep_after_timeout())
        logger.debug(f"Scheduled sleep in {self.config.sleep_after_idle_seconds}s")
    
    async def wake_if_sleeping(self) -> bool:
        """Wake from sleep if sleeping. Returns True if was sleeping."""
        if self.is_sleeping:
            await self.set_idle()
            return True
        return False
    
    async def activity(self) -> None:
        """Record activity and ensure not sleeping."""
        self._last_activity_at = datetime.now()
        await self.wake_if_sleeping()
