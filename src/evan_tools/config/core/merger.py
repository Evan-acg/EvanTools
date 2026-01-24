"""Configuration merger using deep merge strategy."""

from typing import Any

import pydash


class ConfigMerger:
    """Merges multiple configuration dictionaries using deep merge.
    
    Uses pydash's merge_with for deep merging, ensuring nested
    dictionaries are properly combined rather than replaced.
    """
    
    @staticmethod
    def merge(*configs: dict[str, Any]) -> dict[str, Any]:
        """Deep merge multiple configuration dictionaries.
        
        Later configs override earlier ones. Nested dicts are merged
        recursively rather than replaced entirely.
        
        Args:
            *configs: Variable number of configuration dicts to merge.
        
        Returns:
            A new dict containing the merged configuration.
        
        Example:
            >>> base = {"db": {"host": "localhost", "port": 5432}}
            >>> override = {"db": {"host": "prod.example.com"}}
            >>> ConfigMerger.merge(base, override)
            {'db': {'host': 'prod.example.com', 'port': 5432}}
        """
        if not configs:
            return {}
        
        result: dict[str, Any] = {}
        for config in configs:
            result = pydash.merge_with(result, config)
        
        return result
