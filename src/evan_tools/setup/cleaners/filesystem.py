"""文件系统清理器实现

提供对项目构建产物（dist、build、spec）的清理功能。
"""

import logging
from pathlib import Path

from ..core.models import CleanResult
from .base import CleanerBase


logger = logging.getLogger(__name__)


class FileSystemCleaner(CleanerBase):
    """文件系统清理器

    实现对 PyInstaller 和其他构建系统生成的产物的清理。
    支持清理 dist、build 和 spec 目录。

    Attributes:
        dist_dir: dist 目录相对路径（默认 "dist"）
        build_dir: build 目录相对路径（默认 "build"）
        spec_pattern: spec 文件模式（默认 "*.spec"）

    Examples:
        >>> from pathlib import Path
        >>> from evan_tools.setup.cleaners import FileSystemCleaner
        >>>
        >>> cleaner = FileSystemCleaner(project_root=Path.cwd())
        >>> result = cleaner.clean_dist()
        >>> print(result)
        清理成功: dist (42 文件, 5120.0 KB)
        >>>
        >>> # 清理所有产物
        >>> result = cleaner.clean_all()
        >>> if result.success:
        ...     print(f"已删除 {result.files_removed} 个文件，释放 {result.bytes_freed / 1024:.1f} KB")
    """

    def __init__(
        self,
        project_root: Path,
        *,
        dist_dir: str = "dist",
        build_dir: str = "build",
        spec_pattern: str = "*.spec",
    ) -> None:
        """初始化文件系统清理器

        Args:
            project_root: 项目根目录路径
            dist_dir: dist 目录相对路径（默认 "dist"）
            build_dir: build 目录相对路径（默认 "build"）
            spec_pattern: spec 文件模式（默认 "*.spec"）
        """
        super().__init__(project_root)
        self.dist_dir = dist_dir
        self.build_dir = build_dir
        self.spec_pattern = spec_pattern

    def clean_dist(self) -> CleanResult:
        """清理 dist 目录

        删除 dist 目录及其所有内容。
        如果目录不存在，返回成功（不报错）。

        Returns:
            CleanResult: 清理结果对象

        Examples:
            >>> cleaner = FileSystemCleaner(project_root=Path.cwd())
            >>> result = cleaner.clean_dist()
            >>> if result.success:
            ...     print(f"已删除 {result.files_removed} 个文件")
        """
        logger.debug(f"清理 dist 目录: {self.project_root / self.dist_dir}")
        return self._clean_directory(self.project_root / self.dist_dir)

    def clean_build(self) -> CleanResult:
        """清理 build 目录

        删除 build 目录及其所有内容。
        如果目录不存在，返回成功（不报错）。

        Returns:
            CleanResult: 清理结果对象

        Examples:
            >>> cleaner = FileSystemCleaner(project_root=Path.cwd())
            >>> result = cleaner.clean_build()
            >>> if result.success:
            ...     print(f"已删除 {result.files_removed} 个文件")
        """
        logger.debug(f"清理 build 目录: {self.project_root / self.build_dir}")
        return self._clean_directory(self.project_root / self.build_dir)

    def clean_spec(self) -> CleanResult:
        """清理 spec 文件

        删除所有与构建相关的 .spec 文件。
        如果没有找到 spec 文件，返回成功（不报错）。

        Returns:
            CleanResult: 清理结果对象

        Examples:
            >>> cleaner = FileSystemCleaner(project_root=Path.cwd())
            >>> result = cleaner.clean_spec()
            >>> if result.success:
            ...     print(f"已删除 {result.files_removed} 个 spec 文件")
        """
        logger.debug(f"清理 spec 文件: {self.spec_pattern}")
        self._start_timing()
        result = CleanResult(success=True)

        try:
            # 查找所有匹配的 spec 文件
            spec_files = list(self.project_root.glob(self.spec_pattern))

            if not spec_files:
                logger.debug(f"未找到 spec 文件: {self.spec_pattern}")
                result.duration_seconds = self._get_duration()
                return result

            # 删除每个 spec 文件
            total_size = 0
            for spec_file in spec_files:
                try:
                    size = spec_file.stat().st_size
                    total_size += size
                    spec_file.unlink()
                    logger.debug(f"已删除 spec 文件: {spec_file}")
                except OSError as e:
                    error_msg = f"无法删除 spec 文件 {spec_file}: {e}"
                    logger.error(error_msg, exc_info=True)
                    result.errors.append(error_msg)

            result.cleaned_paths.extend(spec_files)
            result.files_removed = len(spec_files)
            result.bytes_freed = total_size
            result.success = len(result.errors) == 0

            if result.success:
                logger.info(
                    f"清理成功: 删除 {len(spec_files)} 个 spec 文件 "
                    f"({total_size / 1024:.1f} KB)"
                )

        except Exception as e:
            error_msg = f"清理 spec 文件时出错: {e}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)
            result.success = False

        result.duration_seconds = self._get_duration()
        return result

    def clean_all(self) -> CleanResult:
        """清理所有构建产物

        依次清理 dist、build 和 spec，并合并结果。
        如果任何一步失败，success 为 False，但会继续清理其他项。

        Returns:
            CleanResult: 合并后的清理结果对象

        Examples:
            >>> cleaner = FileSystemCleaner(project_root=Path.cwd())
            >>> result = cleaner.clean_all()
            >>> print(result)
            清理成功: dist, build (42 文件, 5120.0 KB)
        """
        logger.info("开始清理所有构建产物")
        self._start_timing()

        # 清理各个目录
        results = [
            self.clean_dist(),
            self.clean_build(),
            self.clean_spec(),
        ]

        # 合并结果
        merged = CleanResult(
            success=all(r.success for r in results),
            cleaned_paths=[],
            files_removed=sum(r.files_removed for r in results),
            bytes_freed=sum(r.bytes_freed for r in results),
            errors=[],
        )

        # 汇总信息
        for result in results:
            merged.cleaned_paths.extend(result.cleaned_paths)
            merged.errors.extend(result.errors)

        merged.duration_seconds = self._get_duration()

        if merged.success:
            logger.info(
                f"全部清理完成: 删除 {merged.files_removed} 个文件, "
                f"释放 {merged.bytes_freed / 1024:.1f} KB (耗时 {merged.duration_seconds:.2f}s)"
            )
        else:
            logger.warning(
                f"清理过程中发生 {len(merged.errors)} 个错误, "
                f"已删除 {merged.files_removed} 个文件"
            )

        return merged
