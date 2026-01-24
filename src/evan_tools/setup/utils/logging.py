"""Setup 模块日志配置工具

提供日志配置和日志记录器获取的工具函数。
"""

import logging
import sys
from typing import Optional


def get_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """获取配置好的日志记录器

    获取或创建一个名为 `name` 的日志记录器，并为其配置标准的日志格式。

    Args:
        name: 日志记录器的名称，通常为 `__name__`
        level: 日志级别，默认为 INFO
        format_string: 自定义的日志格式字符串，如果为 None 则使用默认格式

    Returns:
        配置好的 logging.Logger 实例

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条信息日志")
        >>> logger = get_logger("my_module", level=logging.DEBUG)
        >>> logger.debug("调试信息")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 使用默认格式如果没有提供自定义格式
    if format_string is None:
        format_string = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"

    formatter = logging.Formatter(format_string)

    # 创建控制台处理器
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger
