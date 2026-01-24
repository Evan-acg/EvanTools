"""配置管理模块 - 向后兼容适配器。

该模块提供向后兼容的 API，委托给新的
基于 SOLID 的 ConfigManager。原始全局函数 API 被保留
用于现有代码。
"""

import logging
import typing as t
from pathlib import Path

from .core.manager import ConfigManager

logger = logging.getLogger(__name__)

T = t.TypeVar("T")

_manager: ConfigManager | None = None


def _get_manager() -> ConfigManager:
    """获取或创建全局 ConfigManager 实例。

    返回:
        全局 ConfigManager 单例。
    """
    global _manager
    if _manager is None:
        _manager = ConfigManager()
    return _manager


def load_config(path: Path | None = None) -> None:
    """从磁盘加载配置。

    参数:
        path: 配置文件或目录的路径。如果为 None，默认为 "config"。
            如果提供目录，则扫描并合并其中所有 YAML 文件。
            如果提供文件，则仅加载该文件。

    抛出:
        FileNotFoundError: 如果配置文件/目录不存在。
        ValueError: 如果文件格式不受支持。
    """
    if path is None:
        path = Path("config")
    else:
        path = Path(path)

    if path.is_dir():
        logger.info(f"Loading configuration from directory: {path}")
        try:
            _get_manager().load(path)
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
        return

    if not path.suffix:
        if (path.parent / f"{path.name}.yaml").exists():
            path = path.parent / f"{path.name}.yaml"
        elif (path.parent / f"{path.name}.yml").exists():
            path = path.parent / f"{path.name}.yml"
        else:
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
    """获取配置值，支持自动热重载。

    参数:
        path: 配置值的点号标记路径（例如 "db.host"）。
            也可以是键的列表。如果为 None，返回整个配置。
        default: 如果路径不存在时返回的默认值。

    返回:
        配置值，如果未找到则返回默认值。

    示例:
        >>> load_config("config.yaml")
        >>> get_config("database.host")
        'localhost'
        >>> get_config(["database", "port"], 5432)
        5432
    """
    manager = _get_manager()

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
    """将当前配置写回文件。

    将内存中的配置持久化到原始配置文件。

    抛出:
        RuntimeError: 如果尚未加载配置。
    """
    logger.info("Syncing configuration to file")

    try:
        _get_manager().sync()
        logger.info("Configuration synced successfully")
    except Exception as e:
        logger.error(f"Failed to sync configuration: {e}")
        raise


__all__ = ["load_config", "get_config", "sync_config"]
