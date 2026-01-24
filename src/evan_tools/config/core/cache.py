"""配置缓存管理器，支持时间窗口重载。"""

import time
from typing import Any, Optional


class ConfigCache:
    """使用时间窗口失效管理配置缓存。

    存储最后加载的配置，并根据时间窗口决定是否需要重载。
    有助于避免在频繁访问配置时进行过多的文件系统检查。

    属性:
        _cache: 缓存的配置字典。
        _last_reload_time: 上次重载的时间戳。
        _reload_interval_seconds: 两次重载之间的最小时间。
    """

    def __init__(self, reload_interval_seconds: float = 5.0):
        """初始化缓存。

        参数:
            reload_interval_seconds: 两次重载检查之间的最小秒数。
                默认为 5.0 秒。
        """
        self._cache: Optional[dict[str, Any]] = None
        self._last_reload_time: float = 0.0
        self._reload_interval_seconds = reload_interval_seconds

    def get(self) -> Optional[dict[str, Any]]:
        """获取缓存的配置。

        返回:
            缓存的配置字典，如果尚未加载则返回 None。
        """
        return self._cache

    def set(self, config: dict[str, Any]) -> None:
        """使用新配置更新缓存。

        参数:
            config: 要缓存的配置字典。
        """
        self._cache = config
        self._last_reload_time = time.time()

    def should_reload(self) -> bool:
        """检查是否足够的时间已过，可以考虑重载。

        返回:
            如果自上次重载以来已过重载间隔，返回 True。
            否则返回 False。
        """
        if self._cache is None:
            return True

        elapsed = time.time() - self._last_reload_time
        return elapsed >= self._reload_interval_seconds

    def clear(self) -> None:
        """清除缓存。"""
        self._cache = None
        self._last_reload_time = 0.0
