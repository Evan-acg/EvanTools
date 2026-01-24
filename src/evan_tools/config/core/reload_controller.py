"""Configuration reload controller with file modification time tracking."""

import os
from pathlib import Path
from typing import Optional


class ReloadController:
    """Controls when configuration should be reloaded based on file changes.
    
    Tracks the modification time of the config file and determines if
    a reload is necessary by comparing current mtime with cached mtime.
    
    Attributes:
        _config_path: Path to the config file being tracked.
        _last_mtime: Last known modification time of the config file.
    """
    
    def __init__(self):
        """Initialize reload controller."""
        self._config_path: Optional[Path] = None
        self._last_mtime: Optional[float] = None
    
    def set_config_path(self, config_path: Path) -> None:
        """Set the configuration file path to track.
        
        Args:
            config_path: Path to the configuration file.
        """
        self._config_path = config_path
        self._update_mtime()
    
    def _update_mtime(self) -> None:
        """Update the cached modification time from the file system."""
        if self._config_path and self._config_path.exists():
            self._last_mtime = os.path.getmtime(self._config_path)
        else:
            self._last_mtime = None
    
    def has_file_changed(self) -> bool:
        """Check if the config file has been modified since last check.
        
        Returns:
            True if file has changed or doesn't exist, False if unchanged.
        """
        if not self._config_path:
            return True  # No path set, should load
        
        if not self._config_path.exists():
            # File deleted or doesn't exist
            if self._last_mtime is not None:
                # File was there before, now gone
                self._last_mtime = None
                return True
            return False  # Never existed
        
        current_mtime = os.path.getmtime(self._config_path)
        if self._last_mtime is None:
            # First time checking
            self._last_mtime = current_mtime
            return True
        
        if current_mtime != self._last_mtime:
            self._last_mtime = current_mtime
            return True
        
        return False
    
    def reset(self) -> None:
        """Reset the controller state."""
        self._config_path = None
        self._last_mtime = None
