"""Setup 模块数据模型

定义了 setup 模块的核心数据模型，用于表示操作结果。
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class BuildResult:
    """构建结果数据类

    封装了项目构建操作的结果信息。

    Attributes:
        success: 构建是否成功
        output_path: 构建输出路径（如 dist/myapp）
        duration_seconds: 构建耗时（秒）
        command: 执行的构建命令
        stdout: 标准输出
        stderr: 标准错误输出
        timestamp: 构建时间戳
        metadata: 额外的元数据

    Examples:
        >>> result = BuildResult(
        ...     success=True,
        ...     output_path=Path("dist/myapp"),
        ...     duration_seconds=45.2,
        ...     command=["pyinstaller", "--onefile", "main.py"]
        ... )
    """

    success: bool
    output_path: Path | None = None
    duration_seconds: float = 0.0
    command: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, object] = field(default_factory=dict)

    def __str__(self) -> str:
        """返回构建结果的字符串表示"""
        status = "成功" if self.success else "失败"
        if self.output_path:
            return f"构建{status}: {self.output_path} (耗时 {self.duration_seconds:.2f}s)"
        return f"构建{status} (耗时 {self.duration_seconds:.2f}s)"


@dataclass
class DeployResult:
    """部署结果数据类

    封装了文件部署操作的结果信息。

    Attributes:
        success: 部署是否成功
        source: 源路径
        target: 目标路径
        files_copied: 复制的文件数量
        bytes_copied: 复制的字节数
        duration_seconds: 部署耗时（秒）
        cleaned_old: 是否清理了旧文件
        timestamp: 部署时间戳
        metadata: 额外的元数据

    Examples:
        >>> result = DeployResult(
        ...     success=True,
        ...     source=Path("dist/myapp"),
        ...     target=Path("C:/Tools/myapp"),
        ...     files_copied=15,
        ...     bytes_copied=1024000
        ... )
    """

    success: bool
    source: Path | None = None
    target: Path | None = None
    files_copied: int = 0
    bytes_copied: int = 0
    duration_seconds: float = 0.0
    cleaned_old: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, object] = field(default_factory=dict)

    def __str__(self) -> str:
        """返回部署结果的字符串表示"""
        status = "成功" if self.success else "失败"
        if self.source and self.target:
            return (
                f"部署{status}: {self.source} → {self.target} "
                f"({self.files_copied} 文件, {self.bytes_copied / 1024:.1f} KB)"
            )
        return f"部署{status}"


@dataclass
class CleanResult:
    """清理结果数据类

    封装了文件清理操作的结果信息。

    Attributes:
        success: 清理是否成功
        cleaned_paths: 已清理的路径列表
        files_removed: 删除的文件数量
        bytes_freed: 释放的字节数
        duration_seconds: 清理耗时（秒）
        timestamp: 清理时间戳
        errors: 清理过程中的错误列表
        metadata: 额外的元数据

    Examples:
        >>> result = CleanResult(
        ...     success=True,
        ...     cleaned_paths=[Path("dist"), Path("build")],
        ...     files_removed=42,
        ...     bytes_freed=5242880
        ... )
    """

    success: bool
    cleaned_paths: list[Path] = field(default_factory=list)
    files_removed: int = 0
    bytes_freed: int = 0
    duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    def __str__(self) -> str:
        """返回清理结果的字符串表示"""
        status = "成功" if self.success else "失败"
        if self.cleaned_paths:
            paths_str = ", ".join(str(p) for p in self.cleaned_paths)
            return (
                f"清理{status}: {paths_str} "
                f"({self.files_removed} 文件, {self.bytes_freed / 1024:.1f} KB)"
            )
        return f"清理{status}"
