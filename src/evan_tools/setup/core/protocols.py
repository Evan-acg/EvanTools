"""Setup 模块协议定义

定义了 setup 模块的核心接口协议，用于实现依赖注入和解耦。
"""

from pathlib import Path
from typing import Protocol

from .config import ProjectConfig
from .models import BuildResult, CleanResult, DeployResult


class BuilderProtocol(Protocol):
    """构建器协议

    定义了项目构建器的接口规范。任何构建器实现都应该遵循此协议。

    Examples:
        >>> class MyBuilder:
        ...     def build(self, config: ProjectConfig) -> BuildResult:
        ...         # 实现构建逻辑
        ...         pass
    """

    def build(self, config: ProjectConfig) -> BuildResult:
        """构建项目

        Args:
            config: 项目配置对象

        Returns:
            BuildResult: 构建结果对象

        Raises:
            BuildError: 构建失败时抛出
        """
        ...

    def prepare_command(self, config: ProjectConfig) -> list[str]:
        """准备构建命令

        Args:
            config: 项目配置对象

        Returns:
            构建命令的字符串列表

        Raises:
            ConfigValidationError: 配置无效时抛出
        """
        ...


class DeployerProtocol(Protocol):
    """部署器协议

    定义了文件部署器的接口规范。任何部署器实现都应该遵循此协议。

    Examples:
        >>> class MyDeployer:
        ...     def deploy(self, source: Path, target: Path) -> DeployResult:
        ...         # 实现部署逻辑
        ...         pass
    """

    def deploy(
        self, source: Path, target: Path, *, clean_old: bool = True
    ) -> DeployResult:
        """部署文件到目标位置

        Args:
            source: 源文件或目录路径
            target: 目标目录路径
            clean_old: 是否清理旧的部署文件

        Returns:
            DeployResult: 部署结果对象

        Raises:
            DeployError: 部署失败时抛出
        """
        ...

    def validate(self, target: Path) -> bool:
        """验证部署是否成功

        Args:
            target: 目标目录路径

        Returns:
            部署是否有效
        """
        ...


class CleanerProtocol(Protocol):
    """清理器协议

    定义了文件清理器的接口规范。任何清理器实现都应该遵循此协议。

    Examples:
        >>> class MyCleaner:
        ...     def clean_all(self) -> CleanResult:
        ...         # 实现清理逻辑
        ...         pass
    """

    def clean_dist(self) -> CleanResult:
        """清理 dist 目录

        Returns:
            CleanResult: 清理结果对象

        Raises:
            CleanError: 清理失败时抛出
        """
        ...

    def clean_build(self) -> CleanResult:
        """清理 build 目录

        Returns:
            CleanResult: 清理结果对象

        Raises:
            CleanError: 清理失败时抛出
        """
        ...

    def clean_spec(self) -> CleanResult:
        """清理 spec 文件

        Returns:
            CleanResult: 清理结果对象

        Raises:
            CleanError: 清理失败时抛出
        """
        ...

    def clean_all(self) -> CleanResult:
        """清理所有构建产物

        Returns:
            CleanResult: 清理结果对象

        Raises:
            CleanError: 清理失败时抛出
        """
        ...
