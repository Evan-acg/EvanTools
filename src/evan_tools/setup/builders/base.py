"""构建器基类定义

定义了所有构建器的抽象基类和通用辅助方法。
"""

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path

from ..core.config import ProjectConfig
from ..core.models import BuildResult
from ..core.protocols import BuilderProtocol


class BuilderBase(ABC, BuilderProtocol):
    """构建器抽象基类

    实现了 BuilderProtocol，提供了通用的辅助方法和部分实现。
    所有具体的构建器都应该继承此类并实现 `build()` 和 `prepare_command()` 方法。

    Attributes:
        work_dir: 工作目录路径，默认为当前目录
        output_dir: 输出目录路径，默认为 'dist'
        logger: 日志记录器实例

    Examples:
        >>> class MyBuilder(BuilderBase):
        ...     def build(self, config: ProjectConfig) -> BuildResult:
        ...         # 实现构建逻辑
        ...         pass
        ...     def prepare_command(self, config: ProjectConfig) -> list[str]:
        ...         # 准备构建命令
        ...         pass
    """

    def __init__(
        self,
        work_dir: Path | None = None,
        output_dir: Path | None = None,
    ) -> None:
        """初始化构建器基类

        Args:
            work_dir: 工作目录，默认为当前目录
            output_dir: 输出目录，默认为 'dist'
        """
        self.work_dir = Path(work_dir) if work_dir else Path.cwd()
        self.output_dir = Path(output_dir) if output_dir else Path("dist")
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def build(self, config: ProjectConfig) -> BuildResult:
        """构建项目

        这是一个抽象方法，必须在子类中实现。

        Args:
            config: 项目配置对象

        Returns:
            BuildResult: 构建结果对象

        Raises:
            BuildError: 构建失败时抛出
        """
        ...

    @abstractmethod
    def prepare_command(self, config: ProjectConfig) -> list[str]:
        """准备构建命令

        这是一个抽象方法，必须在子类中实现。

        Args:
            config: 项目配置对象

        Returns:
            构建命令的字符串列表

        Raises:
            ConfigValidationError: 配置无效时抛出
        """
        ...

    def _measure_time(self, func, *args, **kwargs):
        """测量函数执行时间的辅助方法

        Args:
            func: 要执行的函数
            *args: 函数的位置参数
            **kwargs: 函数的关键字参数

        Returns:
            元组 (执行结果, 执行时间秒数)

        Examples:
            >>> def slow_func():
            ...     time.sleep(0.1)
            ...     return "done"
            >>> result, duration = builder._measure_time(slow_func)
            >>> print(f"耗时: {duration:.2f}s")
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        return result, duration

    def _log_command(self, command: list[str]) -> None:
        """记录构建命令

        Args:
            command: 构建命令列表
        """
        cmd_str = " ".join(str(c) for c in command)
        self.logger.info(f"执行命令: {cmd_str}")
