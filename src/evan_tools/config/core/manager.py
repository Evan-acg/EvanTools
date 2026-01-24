"""统一的配置管理器，协调所有组件。"""

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
    """线程安全的配置管理器，支持热重载。

    使用依赖注入协调配置加载、缓存、合并和热重载。
    所有组件都可替换用于测试。

    属性:
        _source: 用于读写文件的配置源。
        _cache: 具有时间窗口失效的配置缓存。
        _reload_controller: 追踪文件修改以实现热重载。
        _merger: 合并多个配置字典。
        _lock: 读写锁用于线程安全访问。
        _config_path: 主配置文件的路径。
        _base_path: 用于解析相对路径的基目录。
        _default_config: 与加载的配置合并的默认配置。
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
        """初始化配置管理器。

        参数:
            source: 配置源。默认为 DirectoryConfigSource。
            cache: 配置缓存。默认为新的 ConfigCache。
            reload_controller: 重载控制器。默认为新的 ReloadController。
            merger: 配置合并器。默认为 ConfigMerger。
            lock: 读写锁。默认为新的 RWLock。
            reload_interval_seconds: 重载检查的最小间隔秒数。
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
        """从文件加载配置。

        加载配置文件并将其与默认配置合并。
        为此配置文件设置热重载跟踪。

        参数:
            config_path: 配置文件的路径。
            base_path: 用于解析相对路径的基目录。
                如果为 None，使用 config_path 的父目录。
            default_config: 与加载的配置合并的默认配置。
                后来的值（来自文件）覆盖默认值。

        返回:
            加载并合并的配置字典。

        抛出:
            FileNotFoundError: 如果配置文件不存在。
            ValueError: 如果源不支持该文件格式。
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
            loaded_config = self._source.read(config_path, base_path)

            if default_config:
                final_config = self._merger.merge(default_config, loaded_config)
            else:
                final_config = loaded_config

            self._cache.set(final_config)

            resolved_path = (
                config_path if config_path.is_absolute() else base_path / config_path
            )
            self._reload_controller.set_config_path(resolved_path.resolve())

            self._config_path = config_path
            self._base_path = base_path
            self._default_config = default_config or {}

            logger.info(f"Configuration loaded: {config_path}")
            return final_config

        finally:
            self._lock.release_write()

    def get(self, query: Optional[str] = None, default: Any = None) -> Any:
        """获取配置值，支持热重载。

        如果文件已更改且重载间隔已过，则自动重载配置。
        使用 pydash 进行嵌套查询。

        参数:
            query: 配置值的点号标记路径（例如 "db.host"）。
                如果为 None，返回整个配置。
            default: 如果查询不匹配任何内容时的默认值。

        返回:
            配置值，或如果未找到则返回默认值。

        示例:
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
        """设置配置值，可选择同步到文件。

        使用 pydash.set_ 更新内存中的配置。
        不会自动写入文件 - 调用 sync() 来持久化。

        参数:
            query: 要设置的点号标记路径（例如 "db.host"）。
            value: 要设置的值。

        示例:
            >>> manager.set("database.host", "prod.example.com")
            >>> manager.sync()
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
        """将当前配置写回文件。

        将内存中的配置持久化到原始配置文件。
        需要先调用 load() 才能使用。

        抛出:
            RuntimeError: 如果尚未加载配置。
        """
        if self._config_path is None:
            raise RuntimeError("No configuration loaded. Call load() before sync().")

        self._lock.acquire_read()
        try:
            config = self._cache.get()
            if config is None:
                raise RuntimeError("No configuration in cache.")

            self._source.write(self._config_path, config, self._base_path)

            logger.info(f"Configuration synced to {self._config_path}")

        finally:
            self._lock.release_read()

    def reload(self) -> dict[str, Any]:
        """强制立即从文件重载配置。

        绕过缓存和重载间隔检查。用于测试或
        当已知配置文件已更改时使用。

        返回:
            重载的配置字典。

        抛出:
            RuntimeError: 如果尚未加载配置。
        """
        if self._config_path is None:
            raise RuntimeError("No configuration loaded. Call load() before reload().")

        return self.load(self._config_path, self._base_path, self._default_config)

    def _reload_if_needed(self) -> None:
        """检查是否需要重载并在必要时执行。

        重载发生在以下情况：
        1. 缓存表示重载间隔已过
        2. ReloadController 检测到文件修改
        """
        if not self._cache.should_reload():
            return

        if self._reload_controller.has_file_changed():
            logger.info("Configuration file changed, reloading...")
            self.reload()
