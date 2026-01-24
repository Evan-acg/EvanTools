"""Directory-based configuration source with multi-file scanning."""

import logging
from pathlib import Path
from typing import Any, Optional

from .yaml_source import YamlConfigSource

logger = logging.getLogger(__name__)


class DirectoryConfigSource(YamlConfigSource):
    """Configuration source that scans and merges multiple YAML files from a directory.
    
    Extends YamlConfigSource to support loading all YAML files from a directory,
    merging them in sorted order (deterministic priority).
    """
    
    def read(self, path: Path, base_path: Optional[Path] = None) -> dict[str, Any]:
        """Read and merge all YAML files from a directory.
        
        If path is a directory, scans for all .yaml/.yml files and merges them.
        If path is a file, delegates to parent YamlConfigSource.read().
        
        Args:
            path: Path to directory or YAML file.
            base_path: Optional base directory for resolving relative paths.
        
        Returns:
            The merged configuration as a dictionary.
        
        Raises:
            FileNotFoundError: If the path doesn't exist.
            yaml.YAMLError: If any file is not valid YAML.
        """
        resolved_path = self._resolve_path(path, base_path)
        
        if not resolved_path.exists():
            raise FileNotFoundError(f"Configuration path not found: {resolved_path}")
        
        # If it's a file, use parent implementation
        if resolved_path.is_file():
            return super().read(path, base_path)
        
        # It's a directory - scan for all YAML files
        return self._read_directory(resolved_path)
    
    def _read_directory(self, directory: Path) -> dict[str, Any]:
        """Read and merge all YAML files from a directory.
        
        Args:
            directory: The directory path.
        
        Returns:
            Merged configuration from all YAML files.
        """
        yaml_files = sorted(
            list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))
        )
        
        if not yaml_files:
            logger.warning(f"No YAML files found in {directory}")
            return {}
        
        merged_config: dict[str, Any] = {}
        
        for yaml_file in yaml_files:
            try:
                file_config = super().read(yaml_file)
                # Deep merge the file config
                from ..core.merger import ConfigMerger
                merged_config = ConfigMerger.merge(merged_config, file_config)
                logger.debug(f"Loaded and merged {yaml_file.name}")
            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")
                # Continue with next file on error
                continue
        
        logger.info(f"Loaded and merged {len(yaml_files)} YAML files from {directory}")
        return merged_config
    
    def supports(self, path: Path) -> bool:
        """Check if this source supports the given path.
        
        Supports both directories and YAML files.
        
        Args:
            path: Path to check.
        
        Returns:
            True if path is a directory or has .yaml/.yml extension.
        """
        return path.is_dir() or path.suffix.lower() in {'.yaml', '.yml'}
    
    def write(self, path: Path, config: dict[str, Any], 
              base_path: Optional[Path] = None) -> None:
        """Write configuration to a YAML file.
        
        For directories, this is not supported. Use a file path instead.
        For files, delegates to parent YamlConfigSource.write().
        
        Args:
            path: Path to directory or YAML file.
            config: Configuration dictionary to write.
            base_path: Optional base directory for resolving relative paths.
        
        Raises:
            ValueError: If path is a directory.
        """
        resolved_path = self._resolve_path(path, base_path)
        
        if resolved_path.is_dir():
            raise ValueError(
                f"Cannot write to directory {resolved_path}. "
                "Use a specific YAML file path instead."
            )
        
        # Delegate to parent implementation for file writing
        super().write(path, config, base_path)
