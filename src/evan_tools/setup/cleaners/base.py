"""清理器抽象基类模块

定义了清理器的基础实现，提供通用的辅助方法和模板方法。
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from time import time
from typing import Callable

from ..core.models import CleanResult
from ..core.protocols import CleanerProtocol


logger = logging.getLogger(__name__)


class CleanerBase(ABC):
    """清理器抽象基类

    提供了清理器的通用实现，包括路径管理和结果跟踪。
    所有具体的清理器实现应该继承此类并实现 CleanerProtocol。

    Attributes:
        project_root: 项目根目录路径
        _start_time: 清理操作的开始时间戳

    Examples:
        >>> class MyCleaner(CleanerBase):
        ...     def clean_dist(self) -> CleanResult:
        ...         return self._clean_directory(self.project_root / "dist")
        ...
        ...     def clean_build(self) -> CleanResult:
        ...         return self._clean_directory(self.project_root / "build")
        ...
        ...     def clean_spec(self) -> CleanResult:
        ...         return self._clean_directory(self.project_root / "spec")
        ...
        ...     def clean_all(self) -> CleanResult:
        ...         results = [
        ...             self.clean_dist(),
        ...             self.clean_build(),
        ...             self.clean_spec(),
        ...         ]
        ...         return self._merge_results(results)
    """

    def __init__(self, project_root: Path) -> None:
        """初始化清理器

        Args:
            project_root: 项目根目录路径
        """
        self.project_root = project_root
        self._start_time: float = 0.0

    @abstractmethod
    def clean_dist(self) -> CleanResult:
        """清理 dist 目录

        Returns:
            CleanResult: 清理结果对象

        Raises:
            CleanError: 清理失败时抛出
        """
        ...

    @abstractmethod
    def clean_build(self) -> CleanResult:
        """清理 build 目录

        Returns:
            CleanResult: 清理结果对象

        Raises:
            CleanError: 清理失败时抛出
        """
        ...

    @abstractmethod
    def clean_spec(self) -> CleanResult:
        """清理 spec 文件

        Returns:
            CleanResult: 清理结果对象

        Raises:
            CleanError: 清理失败时抛出
        """
        ...

    @abstractmethod
    def clean_all(self) -> CleanResult:
        """清理所有构建产物

        Returns:
            CleanResult: 清理结果对象

        Raises:
            CleanError: 清理失败时抛出
        """
        ...

    def _start_timing(self) -> None:
        """开始计时

        记录操作的开始时间。
        """
        self._start_time = time()

    def _get_duration(self) -> float:
        """获取操作耗时（秒）

        Returns:
            浮点数表示的耗时（秒）
        """
        return time() - self._start_time

    def _clean_directory(
        self,
        directory: Path,
        *,
        ignore_missing: bool = True,
    ) -> CleanResult:
        """清理目录的通用方法

        删除指定目录及其所有内容，并跟踪统计信息。
        如果目录不存在且 ignore_missing 为 True，则视为成功。

        Args:
            directory: 要清理的目录路径
            ignore_missing: 是否忽略不存在的目录（默认 True）

        Returns:
            CleanResult: 包含清理统计的结果对象
        """
        self._start_timing()
        result = CleanResult(success=True)

        if not directory.exists():
            if not ignore_missing:
                error_msg = f"目录不存在: {directory}"
                logger.warning(error_msg)
                result.errors.append(error_msg)
                result.success = False
            else:
                logger.debug(f"目录不存在，跳过清理: {directory}")
            result.duration_seconds = self._get_duration()
            return result

        try:
            # 收集统计信息
            files_removed, bytes_freed = self._collect_directory_stats(directory)

            # 删除目录
            self._remove_directory_tree(directory)

            # 记录结果
            result.cleaned_paths.append(directory)
            result.files_removed = files_removed
            result.bytes_freed = bytes_freed
            result.success = True

            logger.info(
                f"清理成功: {directory} ({files_removed} 文件, {bytes_freed / 1024:.1f} KB)"
            )

        except Exception as e:
            error_msg = f"清理 {directory} 时出错: {e}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)
            result.success = False

        result.duration_seconds = self._get_duration()
        return result

    def _remove_directory_tree(self, directory: Path) -> None:
        """递归删除目录树

        Args:
            directory: 要删除的目录路径
        """
        if directory.is_dir():
            for item in directory.iterdir():
                if item.is_dir():
                    self._remove_directory_tree(item)
                else:
                    item.unlink()
            directory.rmdir()

    def _collect_directory_stats(self, directory: Path) -> tuple[int, int]:
        """收集目录的统计信息

        递归遍历目录，计算文件数和总大小。

        Args:
            directory: 要统计的目录路径

        Returns:
            元组 (文件数, 总字节数)
        """
        files_count = 0
        bytes_total = 0

        if directory.is_dir():
            for item in directory.rglob("*"):
                if item.is_file():
                    files_count += 1
                    try:
                        bytes_total += item.stat().st_size
                    except OSError as e:
                        logger.warning(f"无法获取文件大小: {item} - {e}")

        return files_count, bytes_total

    def _merge_results(self, results: list[CleanResult]) -> CleanResult:
        """合并多个清理结果

        将多个 CleanResult 对象合并成一个，汇总统计信息。

        Args:
            results: CleanResult 对象列表

        Returns:
            合并后的 CleanResult 对象
        """
        self._start_timing()

        merged = CleanResult(
            success=all(r.success for r in results),
            cleaned_paths=[],
            files_removed=sum(r.files_removed for r in results),
            bytes_freed=sum(r.bytes_freed for r in results),
            errors=[],
        )

        for result in results:
            merged.cleaned_paths.extend(result.cleaned_paths)
            merged.errors.extend(result.errors)

        merged.duration_seconds = self._get_duration()
        return merged

    def _apply_to_paths(
        self,
        paths: list[Path],
        operation: Callable[[Path], CleanResult],
    ) -> CleanResult:
        """对路径列表应用操作

        依次对路径列表中的每个路径执行指定的操作，并合并结果。

        Args:
            paths: 路径列表
            operation: 对单个路径执行的操作函数

        Returns:
            合并后的 CleanResult 对象
        """
        results = [operation(path) for path in paths]
        return self._merge_results(results)
