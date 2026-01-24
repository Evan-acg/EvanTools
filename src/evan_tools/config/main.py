"""Configuration management module - backward compatibility adapter.

This module provides a backward-compatible API that delegates to the new
SOLID-based ConfigManager. The original global function API is preserved
for existing code.
"""

import logging
import typing as t
from pathlib import Path

from .core.manager import ConfigManager

logger = logging.getLogger(__name__)

# Type variable for overload signatures
T = t.TypeVar("T")

# Global ConfigManager instance for backward compatibility
_manager: ConfigManager | None = None


def _get_manager() -> ConfigManager:
    """Get or create the global ConfigManager instance.
    
    Returns:
        The global ConfigManager singleton.
    """
    global _manager
    if _manager is None:
        _manager = ConfigManager()
    return _manager


# ============================================================
# Public APIs (Backward Compatible)
# ============================================================

def load_config(path: Path | None = None) -> None:
    """Load configuration from disk.
    
    Args:
        path: Path to the configuration file or directory. If None, defaults to "config".
            If a directory is provided, scans and merges all YAML files in it.
            If a file is provided, loads just that file.
    
    Raises:
        FileNotFoundError: If the configuration file/directory doesn't exist.
        ValueError: If the file format is not supported.
    """
    if path is None:
        path = Path("config")
    else:
        path = Path(path)
    
    # If path is a directory, just use it directly
    # DirectoryConfigSource will handle scanning
    if path.is_dir():
        logger.info(f"Loading configuration from directory: {path}")
        try:
            _get_manager().load(path)
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
        return
    
    # If path doesn't have extension and isn't a directory, try to find config.yaml/yml
    if not path.suffix:
        if (path.parent / f"{path.name}.yaml").exists():
            path = path.parent / f"{path.name}.yaml"
        elif (path.parent / f"{path.name}.yml").exists():
            path = path.parent / f"{path.name}.yml"
        else:
            # Try the directory approach for "config" without extension
            if path.name == "config":
                path = path.parent / "config"
                if path.is_dir():
                    logger.info(f"Loading configuration from directory: {path}")
                    try:
                        _get_manager().load(path)
                        logger.info("Configuration loaded successfully")
                    except Exception as e:
                        logger.error(f"Failed to load configuration: {e}")
                        raise
                    return
            # Default to yaml extension
            path = path.with_suffix(".yaml")
    
    logger.info(f"Loading configuration from: {path}")
    
    try:
        _get_manager().load(path)
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


PathT = t.Union[t.Hashable, t.List[t.Hashable]]


@t.overload
def get_config(path: PathT, default: T) -> T: ...


@t.overload
def get_config(path: PathT, default: None = None) -> t.Any: ...


@t.overload
def get_config(path: None = None, default: t.Any = None) -> t.Any: ...


def get_config(path: PathT | None = None, default: t.Any = None) -> t.Any:
    """Get configuration value with automatic hot-reload.
    
    Args:
        path: Dot-notation path to configuration value (e.g., "db.host").
            Can also be a list of keys. If None, returns entire config.
        default: Default value if path doesn't exist.
    
    Returns:
        The configuration value, or default if not found.
    
    Example:
        >>> load_config("config.yaml")
        >>> get_config("database.host")
        'localhost'
        >>> get_config(["database", "port"], 5432)
        5432
    """
    manager = _get_manager()
    
    # Convert path to dot notation if it's a list
    if isinstance(path, list):
        query = ".".join(str(p) for p in path)
    elif path is None:
        query = None
    else:
        query = str(path)
    
    result = manager.get(query, default)
    logger.debug(f"Retrieved config: {query}")
    return result


def sync_config() -> None:
    """Write current configuration back to file.
    
    Persists the in-memory configuration to the original config file.
    
    Raises:
        RuntimeError: If no configuration has been loaded yet.
    """
    logger.info("Syncing configuration to file")
    
    try:
        _get_manager().sync()
        logger.info("Configuration synced successfully")
    except Exception as e:
        logger.error(f"Failed to sync configuration: {e}")
        raise


# Preserve any additional exports for backward compatibility
__all__ = ["load_config", "get_config", "sync_config"]
