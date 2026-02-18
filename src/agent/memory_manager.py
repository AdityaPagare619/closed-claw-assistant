"""
Memory Manager Module
RAM optimization through lazy loading and component lifecycle management.
"""

import asyncio
import gc
import logging
import psutil
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class MemoryConfig:
    """Configuration for memory management."""
    unload_after_idle_seconds: float = 300.0  # 5 minutes
    memory_check_interval_seconds: float = 60.0
    memory_threshold_percent: float = 85.0
    gc_threshold_mb: float = 100.0


class ComponentRef:
    """Lazy-loaded component reference with lifecycle management."""
    
    def __init__(
        self,
        name: str,
        factory: Callable[[], T],
        unload_callback: Optional[Callable[[T], None]] = None
    ):
        self.name = name
        self._factory = factory
        self._unload_callback = unload_callback
        self._instance: Optional[T] = None
        self._last_accessed: Optional[datetime] = None
        self._access_count = 0
        self._loaded_at: Optional[datetime] = None
    
    @property
    def is_loaded(self) -> bool:
        """Check if component is currently loaded."""
        return self._instance is not None
    
    @property
    def instance(self) -> Optional[T]:
        """Get the component instance."""
        return self._instance
    
    @property
    def last_accessed(self) -> Optional[datetime]:
        """Get last access timestamp."""
        return self._last_accessed
    
    @property
    def idle_duration(self) -> float:
        """Get idle duration in seconds."""
        if self._last_accessed is None:
            return float('inf')
        return (datetime.now() - self._last_accessed).total_seconds()
    
    def load(self) -> T:
        """Load component if not already loaded."""
        if self._instance is None:
            logger.info(f"Loading component: {self.name}")
            start_time = time.time()
            self._instance = self._factory()
            self._loaded_at = datetime.now()
            load_time = time.time() - start_time
            logger.info(f"Component {self.name} loaded in {load_time:.2f}s")
        
        self._last_accessed = datetime.now()
        self._access_count += 1
        return self._instance
    
    def unload(self) -> None:
        """Unload component and free memory."""
        if self._instance is not None:
            logger.info(f"Unloading component: {self.name}")
            
            if self._unload_callback:
                try:
                    self._unload_callback(self._instance)
                except Exception as e:
                    logger.error(f"Error unloading {self.name}: {e}")
            
            self._instance = None
            gc.collect()
            logger.info(f"Component {self.name} unloaded")


class MemoryManager:
    """
    Manages memory optimization through lazy loading and component lifecycle.
    
    Features:
        - Lazy loading of heavy components
        - Automatic unloading after idle timeout
        - Memory usage monitoring
        - Garbage collection triggers
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self._components: dict[str, ComponentRef] = {}
        self._lock = asyncio.Lock()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._last_gc_at: Optional[datetime] = None
        
        # Track memory metrics
        self._peak_memory_mb = 0.0
        self._component_load_times: dict[str, float] = {}
        
        logger.info("MemoryManager initialized")
    
    def register_component(
        self,
        name: str,
        factory: Callable[[], T],
        unload_callback: Optional[Callable[[T], None]] = None
    ) -> ComponentRef:
        """Register a lazy-loaded component."""
        if name in self._components:
            logger.warning(f"Component {name} already registered, overwriting")
        
        component = ComponentRef(name, factory, unload_callback)
        self._components[name] = component
        logger.info(f"Registered component: {name}")
        return component
    
    def get_component(self, name: str) -> Optional[T]:
        """Get a component, loading it if necessary."""
        if name not in self._components:
            logger.error(f"Component {name} not registered")
            return None
        
        component = self._components[name]
        return component.load()
    
    def unload_component(self, name: str) -> bool:
        """Unload a specific component."""
        if name not in self._components:
            return False
        
        self._components[name].unload()
        return True
    
    def unload_idle_components(self) -> list[str]:
        """Unload components that have been idle too long."""
        unloaded = []
        threshold = self.config.unload_after_idle_seconds
        
        for name, component in self._components.items():
            if component.is_loaded and component.idle_duration > threshold:
                component.unload()
                unloaded.append(name)
        
        if unloaded:
            logger.info(f"Unloaded idle components: {unloaded}")
        
        return unloaded
    
    def unload_all(self) -> None:
        """Unload all components."""
        for component in self._components.values():
            component.unload()
        logger.info("All components unloaded")
    
    def get_memory_usage(self) -> dict[str, Any]:
        """Get current memory usage statistics."""
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
            "system_percent": system_memory.percent,
            "available_mb": system_memory.available / 1024 / 1024,
            "peak_mb": self._peak_memory_mb,
        }
    
    async def start_monitoring(self) -> None:
        """Start background memory monitoring."""
        if self._monitoring_task is not None:
            return
        
        logger.info("Starting memory monitoring")
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self) -> None:
        """Stop background memory monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
            logger.info("Memory monitoring stopped")
    
    async def _monitor_loop(self) -> None:
        """Background loop for memory monitoring."""
        while True:
            try:
                await asyncio.sleep(self.config.memory_check_interval_seconds)
                await self._check_memory()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Memory monitor error: {e}")
    
    async def _check_memory(self) -> None:
        """Check memory usage and optimize if needed."""
        memory = self.get_memory_usage()
        
        # Update peak memory
        if memory["rss_mb"] > self._peak_memory_mb:
            self._peak_memory_mb = memory["rss_mb"]
        
        logger.debug(
            f"Memory: {memory['rss_mb']:.1f}MB "
            f"({memory['percent']:.1f}%), "
            f"System: {memory['system_percent']:.1f}%"
        )
        
        # Unload idle components
        self.unload_idle_components()
        
        # Trigger GC if memory is high
        if memory["system_percent"] > self.config.memory_threshold_percent:
            logger.warning(f"High memory usage detected: {memory['system_percent']:.1f}%")
            await self._trigger_gc()
    
    async def _trigger_gc(self) -> None:
        """Trigger garbage collection."""
        if self._last_gc_at:
            time_since_gc = (datetime.now() - self._last_gc_at).total_seconds()
            if time_since_gc < 30:  # Don't GC too frequently
                return
        
        logger.info("Triggering garbage collection")
        gc.collect()
        self._last_gc_at = datetime.now()
        
        memory_after = self.get_memory_usage()
        logger.info(f"GC complete: {memory_after['rss_mb']:.1f}MB")
    
    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive memory statistics."""
        memory = self.get_memory_usage()
        
        component_stats = {}
        for name, component in self._components.items():
            component_stats[name] = {
                "loaded": component.is_loaded,
                "access_count": component._access_count,
                "idle_seconds": component.idle_duration if component.is_loaded else None,
            }
        
        return {
            "memory": memory,
            "components": component_stats,
            "total_components": len(self._components),
            "loaded_components": sum(1 for c in self._components.values() if c.is_loaded),
            "last_gc": self._last_gc_at.isoformat() if self._last_gc_at else None,
        }
