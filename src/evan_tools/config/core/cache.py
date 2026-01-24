"""Configuration cache manager with time-windowed reloading."""

import time
from typing import Any, Optional


class ConfigCache:
    """Manages configuration cache with time-window based invalidation.
    
    This cache stores the last loaded configuration and decides whether
    a reload is needed based on a time window. It helps avoid excessive
    file system checks when config is accessed frequently.
    
    Attributes:
        _cache: The cached configuration dict.
        _last_reload_time: Timestamp of last reload.
        _reload_interval_seconds: Minimum time between reloads.
    """
    
    def __init__(self, reload_interval_seconds: float = 5.0):
        """Initialize cache.
        
        Args:
            reload_interval_seconds: Minimum seconds between reload checks.
                Defaults to 5.0 seconds.
        """
        self._cache: Optional[dict[str, Any]] = None
        self._last_reload_time: float = 0.0
        self._reload_interval_seconds = reload_interval_seconds
    
    def get(self) -> Optional[dict[str, Any]]:
        """Get cached configuration.
        
        Returns:
            The cached config dict, or None if not loaded yet.
        """
        return self._cache
    
    def set(self, config: dict[str, Any]) -> None:
        """Update cache with new configuration.
        
        Args:
            config: The configuration dict to cache.
        """
        self._cache = config
        self._last_reload_time = time.time()
    
    def should_reload(self) -> bool:
        """Check if enough time has passed to consider a reload.
        
        Returns:
            True if reload interval has elapsed since last reload,
            False otherwise.
        """
        if self._cache is None:
            return True
        
        elapsed = time.time() - self._last_reload_time
        return elapsed >= self._reload_interval_seconds
    
    def clear(self) -> None:
        """Clear the cache."""
        self._cache = None
        self._last_reload_time = 0.0
