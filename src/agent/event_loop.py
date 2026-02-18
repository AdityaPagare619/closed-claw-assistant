"""
Event Loop Module
Async event handling with priority queue and error recovery.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class EventType(Enum):
    """Event types."""
    CALL = auto()
    WHATSAPP = auto()
    TELEGRAM = auto()
    MEMORY = auto()
    SYSTEM = auto()
    USER = auto()


@dataclass
class Event:
    """Represents an event to be processed."""
    event_type: EventType
    data: Any
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    event_id: str = field(default_factory=lambda: f"evt_{id(object())}")
    
    def __lt__(self, other: 'Event') -> bool:
        """Compare events for priority queue ordering."""
        if not isinstance(other, Event):
            return NotImplemented
        return self.priority.value < other.priority.value


@dataclass
class EventLoopConfig:
    """Configuration for event loop."""
    max_queue_size: int = 1000
    worker_count: int = 4
    default_timeout_seconds: float = 30.0
    retry_delay_seconds: float = 1.0
    max_retry_delay_seconds: float = 60.0


class EventLoop:
    """
    Async event loop with priority queue and error recovery.
    
    Features:
        - Priority-based event processing
        - Multiple worker tasks
        - Automatic retry with exponential backoff
        - Error handling and recovery
    """
    
    def __init__(self, config: Optional[EventLoopConfig] = None):
        self.config = config or EventLoopConfig()
        self._queue: asyncio.PriorityQueue[Event] = asyncio.PriorityQueue(
            maxsize=self.config.max_queue_size
        )
        self._handlers: dict[EventType, list[Callable[[Event], Any]]] = {
            event_type: [] for event_type in EventType
        }
        self._workers: list[asyncio.Task] = []
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._metrics = {
            "processed": 0,
            "failed": 0,
            "retried": 0,
            "dropped": 0,
        }
        
        logger.info("EventLoop initialized")
    
    def register_handler(
        self,
        event_type: EventType,
        handler: Callable[[Event], Any]
    ) -> None:
        """Register a handler for an event type."""
        self._handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type.name}")
    
    async def emit(
        self,
        event_type: EventType,
        data: Any,
        priority: EventPriority = EventPriority.NORMAL
    ) -> Optional[Event]:
        """Emit an event to the queue."""
        event = Event(
            event_type=event_type,
            data=data,
            priority=priority
        )
        
        try:
            self._queue.put_nowait(event)
            logger.debug(f"Event emitted: {event_type.name} (priority: {priority.name})")
            return event
        except asyncio.QueueFull:
            logger.error(f"Event queue full, dropping event: {event_type.name}")
            self._metrics["dropped"] += 1
            return None
    
    async def start(self) -> None:
        """Start the event loop with workers."""
        if self._running:
            return
        
        self._running = True
        self._shutdown_event.clear()
        
        # Start worker tasks
        for i in range(self.config.worker_count):
            worker = asyncio.create_task(
                self._worker_loop(f"worker-{i}"),
                name=f"event-worker-{i}"
            )
            self._workers.append(worker)
        
        logger.info(f"EventLoop started with {self.config.worker_count} workers")
    
    async def stop(self, timeout: float = 30.0) -> None:
        """Stop the event loop gracefully."""
        if not self._running:
            return
        
        logger.info("Stopping EventLoop...")
        self._running = False
        self._shutdown_event.set()
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to finish
        if self._workers:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._workers, return_exceptions=True),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning("EventLoop stop timeout, forcing shutdown")
        
        self._workers.clear()
        logger.info("EventLoop stopped")
    
    async def _worker_loop(self, worker_id: str) -> None:
        """Worker loop for processing events."""
        logger.debug(f"Worker {worker_id} started")
        
        while self._running:
            try:
                # Wait for event with timeout to check running flag
                try:
                    event = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                await self._process_event(event)
                self._queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
        
        logger.debug(f"Worker {worker_id} stopped")
    
    async def _process_event(self, event: Event) -> None:
        """Process a single event."""
        handlers = self._handlers.get(event.event_type, [])
        
        if not handlers:
            logger.warning(f"No handlers for event type: {event.event_type.name}")
            return
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await asyncio.wait_for(
                        handler(event),
                        timeout=self.config.default_timeout_seconds
                    )
                else:
                    handler(event)
                
                self._metrics["processed"] += 1
                
            except asyncio.TimeoutError:
                logger.error(f"Handler timeout for {event.event_type.name}")
                await self._handle_failure(event, "timeout")
                
            except Exception as e:
                logger.error(f"Handler error for {event.event_type.name}: {e}")
                await self._handle_failure(event, str(e))
    
    async def _handle_failure(self, event: Event, error: str) -> None:
        """Handle event processing failure with retry."""
        self._metrics["failed"] += 1
        
        if event.retry_count < event.max_retries:
            event.retry_count += 1
            self._metrics["retried"] += 1
            
            # Exponential backoff
            delay = min(
                self.config.retry_delay_seconds * (2 ** (event.retry_count - 1)),
                self.config.max_retry_delay_seconds
            )
            
            logger.info(
                f"Retrying event {event.event_type.name} "
                f"(attempt {event.retry_count}/{event.max_retries}) in {delay:.1f}s"
            )
            
            await asyncio.sleep(delay)
            
            try:
                self._queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.error(f"Queue full, dropping retry for {event.event_type.name}")
                self._metrics["dropped"] += 1
        else:
            logger.error(
                f"Event {event.event_type.name} failed after {event.max_retries} retries"
            )
    
    def get_metrics(self) -> dict[str, int]:
        """Get event processing metrics."""
        return self._metrics.copy()
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()
