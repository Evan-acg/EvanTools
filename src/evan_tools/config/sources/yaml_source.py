"""YAML configuration source implementation."""

import logging
from pathlib import Path
from typing import Any, Optional

import yaml

from ..core.source import ConfigSource

logger = logging.getLogger(__name__)


class YamlConfigSource(ConfigSource):
    """Configuration source for YAML files.
    
    Reads and writes configuration from/to YAML files using PyYAML.
    Supports safe loading and preserves formatting when possible.
    """
    
    def read(self, path: Path, base_path: Optional[Path] = None) -> dict[str, Any]:
        """Read configuration from a YAML file.
        
        Args:
            path: Path to the YAML file.
            base_path: Optional base directory for resolving relative paths.
        
        Returns:
            The configuration as a dictionary.
        
        Raises:
            FileNotFoundError: If the file doesn't exist.
            yaml.YAMLError: If the file is not valid YAML.
        """
        resolved_path = self._resolve_path(path, base_path)
        
        if not resolved_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {resolved_path}")
        
        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # yaml.safe_load returns None for empty files
            if data is None:
                data = {}
            
            logger.info(f"Loaded configuration from {resolved_path}")
            return data
        
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML file {resolved_path}: {e}")
            raise
    
    def write(self, path: Path, config: dict[str, Any], 
              base_path: Optional[Path] = None) -> None:
        """Write configuration to a YAML file.
        
        Args:
            path: Path to write the YAML file.
            config: Configuration dictionary to write.
            base_path: Optional base directory for resolving relative paths.
        
        Raises:
            IOError: If writing fails.
        """
        resolved_path = self._resolve_path(path, base_path)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(resolved_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f, default_flow_style=False, 
                              allow_unicode=True, sort_keys=False)
            
            logger.info(f"Wrote configuration to {resolved_path}")
        
        except IOError as e:
            logger.error(f"Failed to write YAML file {resolved_path}: {e}")
            raise
    
    def supports(self, path: Path) -> bool:
        """Check if this source supports the given file path.
        
        Args:
            path: Path to check.
        
        Returns:
            True if the file has a .yaml or .yml extension.
        """
        return path.suffix.lower() in {'.yaml', '.yml'}
    
    def _resolve_path(self, path: Path, base_path: Optional[Path]) -> Path:
        """Resolve a potentially relative path against a base path.
        
        Args:
            path: The path to resolve.
            base_path: Optional base directory.
        
        Returns:
            An absolute Path.
        """
        if path.is_absolute():
            return path
        
        if base_path is None:
            return path.resolve()
        
        return (base_path / path).resolve()
