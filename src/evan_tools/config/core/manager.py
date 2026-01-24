"""Unified configuration manager coordinating all components."""

import logging
from pathlib import Path
from typing import Any, Optional

import pydash

from .cache import ConfigCache
from .merger import ConfigMerger
from .reload_controller import ReloadController
from .source import ConfigSource
from ..concurrency.rw_lock import RWLock
from ..sources.directory_source import DirectoryConfigSource

logger = logging.getLogger(__name__)


class ConfigManager:
    """Thread-safe configuration manager with hot-reload support.

    Coordinates configuration loading, caching, merging, and hot-reload
    using dependency injection. All components are replaceable for testing.

    Attributes:
        _source: Configuration source for reading/writing files.
        _cache: Configuration cache with time-window invalidation.
        _reload_controller: Tracks file modifications for hot-reload.
        _merger: Merges multiple configuration dictionaries.
        _lock: Read-write lock for thread-safe access.
        _config_path: Path to the primary configuration file.
        _base_path: Base directory for resolving relative paths.
        _default_config: Default configuration merged with loaded config.
    """

    def __init__(
        self,
        source: Optional[ConfigSource] = None,
        cache: Optional[ConfigCache] = None,
        reload_controller: Optional[ReloadController] = None,
        merger: Optional[ConfigMerger] = None,
        lock: Optional[RWLock] = None,
        reload_interval_seconds: float = 5.0,
    ):
        """Initialize configuration manager.

        Args:
            source: Configuration source. Defaults to DirectoryConfigSource.
            cache: Configuration cache. Defaults to new ConfigCache.
            reload_controller: Reload controller. Defaults to new ReloadController.
            merger: Configuration merger. Defaults to ConfigMerger.
            lock: Read-write lock. Defaults to new RWLock.
            reload_interval_seconds: Minimum seconds between reload checks.
        """
        self._source = source or DirectoryConfigSource()
        self._cache = cache or ConfigCache(reload_interval_seconds)
        self._reload_controller = reload_controller or ReloadController()
        self._merger = merger or ConfigMerger()
        self._lock = lock or RWLock()

        self._config_path: Optional[Path] = None
        self._base_path: Optional[Path] = None
        self._default_config: dict[str, Any] = {}

    def load(
        self,
        config_path: str | Path,
        base_path: Optional[str | Path] = None,
        default_config: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Load configuration from file.

        Loads the configuration file and merges it with the default config.
        Sets up hot-reload tracking for this configuration file.

        Args:
            config_path: Path to the configuration file.
            base_path: Base directory for resolving relative paths.
                If None, uses config_path's parent directory.
            default_config: Default configuration to merge with loaded config.
                Later values (from file) override defaults.

        Returns:
            The loaded and merged configuration dictionary.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            ValueError: If the file format is not supported by the source.
        """
        config_path = Path(config_path)

        if not self._source.supports(config_path):
            raise ValueError(f"Unsupported configuration format: {config_path.suffix}")

        if base_path is None:
            base_path = config_path.parent
        else:
            base_path = Path(base_path)

        self._lock.acquire_write()
        try:
            # Load from source
            loaded_config = self._source.read(config_path, base_path)

            # Merge with defaults
            if default_config:
                final_config = self._merger.merge(default_config, loaded_config)
            else:
                final_config = loaded_config

            # Update cache
            self._cache.set(final_config)

            # Track for hot-reload
            resolved_path = (
                config_path if config_path.is_absolute() else base_path / config_path
            )
            self._reload_controller.set_config_path(resolved_path.resolve())

            # Store for reload
            self._config_path = config_path
            self._base_path = base_path
            self._default_config = default_config or {}

            logger.info(f"Configuration loaded: {config_path}")
            return final_config

        finally:
            self._lock.release_write()

    def get(self, query: Optional[str] = None, default: Any = None) -> Any:
        """Get configuration value with hot-reload support.

        Automatically reloads configuration if the file has changed and
        the reload interval has elapsed. Uses pydash for nested queries.

        Args:
            query: Dot-notation path to configuration value (e.g., "db.host").
                If None, returns the entire configuration.
            default: Default value if query doesn't match anything.

        Returns:
            The configuration value, or default if not found.

        Example:
            >>> manager.load("config.yaml")
            >>> manager.get("database.host")
            'localhost'
            >>> manager.get("nonexistent.key", "fallback")
            'fallback'
        """
        self._reload_if_needed()

        self._lock.acquire_read()
        try:
            config = self._cache.get()
            if config is None:
                return default

            if query is None:
                return config

            return pydash.get(config, query, default)

        finally:
            self._lock.release_read()

    def set(self, query: str, value: Any) -> None:
        """Set a configuration value and optionally sync to file.

        Updates the in-memory configuration using pydash.set_.
        Does NOT automatically write to file - call sync() to persist.

        Args:
            query: Dot-notation path to set (e.g., "db.host").
            value: The value to set.

        Example:
            >>> manager.set("database.host", "prod.example.com")
            >>> manager.sync()  # Persist to file
        """
        self._lock.acquire_write()
        try:
            config = self._cache.get()
            if config is None:
                config = {}

            pydash.set_(config, query, value)
            self._cache.set(config)

        finally:
            self._lock.release_write()

    def sync(self) -> None:
        """Write the current configuration back to file.

        Persists the in-memory configuration to the original config file.
        Requires that load() has been called first.

        Raises:
            RuntimeError: If no configuration has been loaded yet.
        """
        if self._config_path is None:
            raise RuntimeError("No configuration loaded. Call load() before sync().")

        self._lock.acquire_read()
        try:
            config = self._cache.get()
            if config is None:
                raise RuntimeError("No configuration in cache.")

            # Extract the non-default parts for writing
            # (We don't want to write defaults back to the file)
            # For now, just write the whole config
            self._source.write(self._config_path, config, self._base_path)

            logger.info(f"Configuration synced to {self._config_path}")

        finally:
            self._lock.release_read()

    def reload(self) -> dict[str, Any]:
        """Force immediate reload of configuration from file.

        Bypasses cache and reload interval checks. Useful for testing
        or when you know the config file has changed.

        Returns:
            The reloaded configuration dictionary.

        Raises:
            RuntimeError: If no configuration has been loaded yet.
        """
        if self._config_path is None:
            raise RuntimeError("No configuration loaded. Call load() before reload().")

        return self.load(self._config_path, self._base_path, self._default_config)

    def _reload_if_needed(self) -> None:
        """Check if reload is needed and perform it if so.

        Reload happens if:
        1. Cache indicates reload interval has elapsed
        2. ReloadController detects file modification
        """
        if not self._cache.should_reload():
            return  # Not time yet

        if self._reload_controller.has_file_changed():
            logger.info("Configuration file changed, reloading...")
            self.reload()
