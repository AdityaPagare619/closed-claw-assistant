"""
Agent Daemon Module
Main daemon process for Closed Claw Assistant.
"""

import asyncio
import logging
import signal
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .state_manager import StateManager, AgentState, StateConfig
from .memory_manager import MemoryManager, MemoryConfig
from .event_loop import EventLoop, EventLoopConfig, EventType, EventPriority, Event

logger = logging.getLogger(__name__)


@dataclass
class DaemonConfig:
    """Configuration for the agent daemon."""
    call_poll_interval_ms: float = 500.0
    whatsapp_poll_interval_ms: float = 5000.0
    telegram_poll_interval_ms: float = 500.0
    memory_check_interval_ms: float = 60000.0
    shutdown_timeout_seconds: float = 30.0


class AgentDaemon:
    """
    Main agent daemon process for Closed Claw Assistant.
    
    Features:
        - Always-running async daemon
        - Lazy loading of heavy components (brain, voice)
        - Event loops for: calls (500ms), WhatsApp (5s), Telegram (500ms), memory (60s)
        - Graceful shutdown handling
        - State management (idle/busy/sleeping)
    
    Usage:
        daemon = AgentDaemon()
        await daemon.start()
        await daemon.run()
    """
    
    def __init__(
        self,
        config: Optional[DaemonConfig] = None,
        state_config: Optional[StateConfig] = None,
        memory_config: Optional[MemoryConfig] = None,
        event_config: Optional[EventLoopConfig] = None
    ):
        self.config = config or DaemonConfig()
        self.state_manager = StateManager(state_config)
        self.memory_manager = MemoryManager(memory_config)
        self.event_loop = EventLoop(event_config)
        
        self._running = False
        self._shutdown_requested = False
        self._tasks: list[asyncio.Task] = []
        self._startup_time: Optional[datetime] = None
        
        # Component placeholders (lazy loaded)
        self._brain: Optional[Any] = None
        self._voice_engine: Optional[Any] = None
        
        # Setup signal handlers
        self._setup_signals()
        
        logger.info("AgentDaemon initialized")
    
    def _setup_signals(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        try:
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, self._signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass
    
    def _signal_handler(self) -> None:
        """Handle shutdown signals."""
        logger.info("Shutdown signal received")
        self._shutdown_requested = True
    
    @property
    def is_running(self) -> bool:
        """Check if daemon is running."""
        return self._running
    
    async def start(self) -> None:
        """Start the daemon and all subsystems."""
        if self._running:
            logger.warning("Daemon already running")
            return
        
        self._startup_time = datetime.now()
        logger.info("Starting AgentDaemon...")
        
        # Register state callbacks
        self.state_manager.register_callback(
            AgentState.SLEEPING,
            self._on_sleep
        )
        self.state_manager.register_callback(
            AgentState.IDLE,
            self._on_wake
        )
        
        # Register event handlers
        self._register_event_handlers()
        
        # Start subsystems
        await self.event_loop.start()
        await self.memory_manager.start_monitoring()
        
        # Register lazy-loaded components
        self._register_components()
        
        self._running = True
        logger.info("AgentDaemon started successfully")
    
    async def stop(self) -> None:
        """Stop the daemon gracefully."""
        if not self._running:
            return
        
        logger.info("Stopping AgentDaemon...")
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Stop subsystems
        await self.event_loop.stop(timeout=self.config.shutdown_timeout_seconds)
        await self.memory_manager.stop_monitoring()
        
        # Unload all components
        self.memory_manager.unload_all()
        
        logger.info("AgentDaemon stopped")
    
    def _register_event_handlers(self) -> None:
        """Register handlers for different event types."""
        self.event_loop.register_handler(EventType.CALL, self._handle_call)
        self.event_loop.register_handler(EventType.WHATSAPP, self._handle_whatsapp)
        self.event_loop.register_handler(EventType.TELEGRAM, self._handle_telegram)
        self.event_loop.register_handler(EventType.MEMORY, self._handle_memory)
        self.event_loop.register_handler(EventType.SYSTEM, self._handle_system)
    
    def _register_components(self) -> None:
        """Register lazy-loaded components with the memory manager."""
        # Brain component (AI model)
        self.memory_manager.register_component(
            name="brain",
            factory=self._create_brain,
            unload_callback=self._unload_brain
        )
        
        # Voice engine component
        self.memory_manager.register_component(
            name="voice",
            factory=self._create_voice_engine,
            unload_callback=self._unload_voice_engine
        )
        
        logger.info("Components registered")
    
    def _create_brain(self) -> Any:
        """Factory for brain component."""
        logger.info("Creating brain component...")
        # Placeholder - actual implementation will load AI model
        brain = {"type": "brain", "status": "initialized"}
        logger.info("Brain component created")
        return brain
    
    def _unload_brain(self, brain: Any) -> None:
        """Unload brain component."""
        logger.info("Unloading brain component...")
        # Cleanup resources
        self._brain = None
        logger.info("Brain component unloaded")
    
    def _create_voice_engine(self) -> Any:
        """Factory for voice engine component."""
        logger.info("Creating voice engine component...")
        # Placeholder - actual implementation will load voice model
        voice = {"type": "voice", "status": "initialized"}
        logger.info("Voice engine component created")
        return voice
    
    def _unload_voice_engine(self, voice: Any) -> None:
        """Unload voice engine component."""
        logger.info("Unloading voice engine component...")
        # Cleanup resources
        self._voice_engine = None
        logger.info("Voice engine component unloaded")
    
    async def _on_sleep(self, state: AgentState) -> None:
        """Callback when entering sleep state."""
        logger.info("Entering sleep mode - unloading components")
        self.memory_manager.unload_all()
    
    async def _on_wake(self, state: AgentState) -> None:
        """Callback when waking from sleep."""
        logger.info("Waking from sleep mode")
    
    async def _handle_call(self, event: Event) -> None:
        """Handle call events."""
        await self.state_manager.set_busy()
        logger.info(f"Processing call event: {event.data}")
        
        # Lazy load voice engine
        voice = self.memory_manager.get_component("voice")
        
        # Process call...
        await asyncio.sleep(0.1)  # Placeholder
        
        await self.state_manager.set_idle()
    
    async def _handle_whatsapp(self, event: Event) -> None:
        """Handle WhatsApp events."""
        await self.state_manager.set_busy()
        logger.info(f"Processing WhatsApp event: {event.data}")
        
        # Lazy load brain
        brain = self.memory_manager.get_component("brain")
        
        # Process WhatsApp message...
        await asyncio.sleep(0.1)  # Placeholder
        
        await self.state_manager.set_idle()
    
    async def _handle_telegram(self, event: Event) -> None:
        """Handle Telegram events."""
        await self.state_manager.set_busy()
        logger.info(f"Processing Telegram event: {event.data}")
        
        # Lazy load brain
        brain = self.memory_manager.get_component("brain")
        
        # Process Telegram message...
        await asyncio.sleep(0.1)  # Placeholder
        
        await self.state_manager.set_idle()
    
    async def _handle_memory(self, event: Event) -> None:
        """Handle memory check events."""
        logger.debug("Processing memory check event")
        stats = self.memory_manager.get_stats()
        logger.debug(f"Memory stats: {stats}")
    
    async def _handle_system(self, event: Event) -> None:
        """Handle system events."""
        logger.info(f"Processing system event: {event.data}")
    
    async def _poll_calls(self) -> None:
        """Poll for incoming calls every 500ms."""
        logger.info("Call polling started (500ms interval)")
        
        while self._running and not self._shutdown_requested:
            try:
                # Simulate call check
                # In production: Check for incoming calls
                has_call = False  # Placeholder
                
                if has_call:
                    await self.event_loop.emit(
                        EventType.CALL,
                        {"type": "incoming"},
                        EventPriority.HIGH
                    )
                
                await asyncio.sleep(self.config.call_poll_interval_ms / 1000)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Call polling error: {e}")
                await asyncio.sleep(1.0)
        
        logger.info("Call polling stopped")
    
    async def _poll_whatsapp(self) -> None:
        """Poll for WhatsApp messages every 5 seconds."""
        logger.info("WhatsApp polling started (5s interval)")
        
        while self._running and not self._shutdown_requested:
            try:
                # Simulate WhatsApp check
                # In production: Check for new messages
                has_message = False  # Placeholder
                
                if has_message:
                    await self.event_loop.emit(
                        EventType.WHATSAPP,
                        {"type": "message"},
                        EventPriority.NORMAL
                    )
                
                await asyncio.sleep(self.config.whatsapp_poll_interval_ms / 1000)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"WhatsApp polling error: {e}")
                await asyncio.sleep(1.0)
        
        logger.info("WhatsApp polling stopped")
    
    async def _poll_telegram(self) -> None:
        """Poll for Telegram messages every 500ms."""
        logger.info("Telegram polling started (500ms interval)")
        
        while self._running and not self._shutdown_requested:
            try:
                # Simulate Telegram check
                # In production: Check for new messages
                has_message = False  # Placeholder
                
                if has_message:
                    await self.event_loop.emit(
                        EventType.TELEGRAM,
                        {"type": "message"},
                        EventPriority.NORMAL
                    )
                
                await asyncio.sleep(self.config.telegram_poll_interval_ms / 1000)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Telegram polling error: {e}")
                await asyncio.sleep(1.0)
        
        logger.info("Telegram polling stopped")
    
    async def _memory_check(self) -> None:
        """Perform periodic memory checks every 60 seconds."""
        logger.info("Memory check started (60s interval)")
        
        while self._running and not self._shutdown_requested:
            try:
                await self.event_loop.emit(
                    EventType.MEMORY,
                    {"type": "check"},
                    EventPriority.LOW
                )
                
                await asyncio.sleep(self.config.memory_check_interval_ms / 1000)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Memory check error: {e}")
                await asyncio.sleep(1.0)
        
        logger.info("Memory check stopped")
    
    async def run(self) -> None:
        """Main run loop - start all polling tasks."""
        logger.info("Starting main event loops...")
        
        # Create polling tasks
        self._tasks = [
            asyncio.create_task(self._poll_calls(), name="call-poller"),
            asyncio.create_task(self._poll_whatsapp(), name="whatsapp-poller"),
            asyncio.create_task(self._poll_telegram(), name="telegram-poller"),
            asyncio.create_task(self._memory_check(), name="memory-checker"),
        ]
        
        # Wait for shutdown signal
        while self._running and not self._shutdown_requested:
            await asyncio.sleep(0.1)
        
        logger.info("Main loop ending...")
    
    def get_status(self) -> dict[str, Any]:
        """Get daemon status and metrics."""
        uptime = None
        if self._startup_time:
            uptime = (datetime.now() - self._startup_time).total_seconds()
        
        return {
            "running": self._running,
            "state": self.state_manager.current_state.name,
            "uptime_seconds": uptime,
            "event_metrics": self.event_loop.get_metrics(),
            "memory_stats": self.memory_manager.get_stats(),
            "queue_size": self.event_loop.get_queue_size(),
        }


async def main():
    """Main entry point."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start daemon
    daemon = AgentDaemon()
    
    try:
        await daemon.start()
        await daemon.run()
    except Exception as e:
        logger.exception(f"Daemon error: {e}")
    finally:
        await daemon.stop()


if __name__ == "__main__":
    asyncio.run(main())
