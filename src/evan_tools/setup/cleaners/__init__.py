"""Setup 模块清理器组件

提供文件系统清理功能，用于清理项目构建产物和缓存文件。

Classes:
    FileSystemCleaner: 文件系统清理器实现
    CleanerBase: 清理器抽象基类

Examples:
    >>> from evan_tools.setup.cleaners import FileSystemCleaner
    >>> cleaner = FileSystemCleaner(project_root=Path.cwd())
    >>> result = cleaner.clean_all()
    >>> print(result)
    清理成功: dist, build, spec (42 文件, 5120.0 KB)
"""

from .base import CleanerBase
from .filesystem import FileSystemCleaner

__all__ = [
    "CleanerBase",
    "FileSystemCleaner",
]
