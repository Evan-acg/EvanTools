"""Setup 模块部署器基类

定义了部署器的抽象基类，提供通用的部署功能和辅助方法。
"""

import logging
import shutil
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..core.models import DeployResult
from ..core.protocols import DeployerProtocol

logger = logging.getLogger(__name__)


class DeployerBase(ABC):
    """部署器抽象基类

    为所有部署器实现提供通用的基础功能，包括部署、验证、计时和统计等。

    Attributes:
        logger: 用于记录日志的 logger 对象

    Examples:
        >>> class MyDeployer(DeployerBase):
        ...     def deploy(self, source: Path, target: Path, *, clean_old: bool = True) -> DeployResult:
        ...         # 实现自定义部署逻辑
        ...         pass
    """

    def __init__(self) -> None:
        """初始化部署器基类

        设置日志记录器和通用属性。
        """
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def deploy(
        self, source: Path, target: Path, *, clean_old: bool = True
    ) -> DeployResult:
        """部署文件到目标位置

        实现类必须实现此方法以提供具体的部署逻辑。

        Args:
            source: 源文件或目录路径
            target: 目标目录路径
            clean_old: 是否清理旧的部署文件，默认为 True

        Returns:
            DeployResult: 包含部署结果信息的对象

        Raises:
            FileNotFoundError: 源文件不存在时抛出
            OSError: 部署过程中发生系统错误时抛出
        """
        ...

    @abstractmethod
    def validate(self, target: Path) -> bool:
        """验证部署是否成功

        实现类必须实现此方法以验证部署结果。

        Args:
            target: 目标目录路径

        Returns:
            True 表示部署有效，False 表示部署无效
        """
        ...

    def _copy_tree(
        self, source: Path, target: Path, *, exist_ok: bool = True
    ) -> tuple[int, int]:
        """递归复制目录树

        此方法提供了通用的目录复制功能，并收集统计信息。

        Args:
            source: 源目录路径
            target: 目标目录路径
            exist_ok: 是否允许目标目录已存在

        Returns:
            (文件数, 字节数) 的元组

        Raises:
            FileNotFoundError: 源目录不存在时抛出
            IsADirectoryError: 目标是文件而非目录时抛出
        """
        if not source.exists():
            raise FileNotFoundError(f"源路径不存在: {source}")

        if source.is_file():
            # 处理单个文件
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            return 1, source.stat().st_size

        # 处理目录
        shutil.copytree(source, target, dirs_exist_ok=exist_ok)

        # 统计复制的文件数和字节数
        files_count = 0
        bytes_total = 0
        for path in target.rglob("*"):
            if path.is_file():
                files_count += 1
                bytes_total += path.stat().st_size

        return files_count, bytes_total

    def _calculate_size(self, path: Path) -> int:
        """计算路径的总大小（字节）

        递归计算给定路径（文件或目录）的总大小。

        Args:
            path: 文件或目录路径

        Returns:
            总大小（字节）
        """
        if not path.exists():
            return 0

        if path.is_file():
            return path.stat().st_size

        total_size = 0
        for item in path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
        return total_size

    def _count_files(self, path: Path) -> int:
        """计算目录中的文件数量

        递归计算给定路径（文件或目录）中的文件总数。

        Args:
            path: 文件或目录路径

        Returns:
            文件总数
        """
        if not path.exists():
            return 0

        if path.is_file():
            return 1

        count = 0
        for item in path.rglob("*"):
            if item.is_file():
                count += 1
        return count

    def _with_timing(self, func, *args, **kwargs) -> tuple[Any, float]:
        """执行函数并记录耗时

        此方法用于测量函数执行时间。

        Args:
            func: 要执行的函数
            *args: 函数的位置参数
            **kwargs: 函数的关键字参数

        Returns:
            (函数返回值, 耗时秒数) 的元组
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        return result, duration
