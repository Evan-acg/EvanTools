"""Setup 模块异常定义

定义了 setup 模块的异常层次结构，用于表示不同类型的错误。
"""


class SetupError(Exception):
    """Setup 模块基础异常类

    所有 setup 模块的自定义异常都应该继承此类。

    Attributes:
        message: 错误消息
        details: 可选的详细错误信息
    """

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        """初始化 SetupError

        Args:
            message: 错误消息
            details: 可选的详细错误信息字典
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """返回错误的字符串表示"""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class BuildError(SetupError):
    """构建过程中发生的错误

    当项目构建失败时抛出此异常。

    Examples:
        >>> raise BuildError("PyInstaller 构建失败", {"exit_code": 1})
    """

    pass


class DeployError(SetupError):
    """部署过程中发生的错误

    当文件部署失败时抛出此异常。

    Examples:
        >>> raise DeployError("无法写入目标目录", {"target": "/path/to/target"})
    """

    pass


class CleanError(SetupError):
    """清理过程中发生的错误

    当清理构建文件失败时抛出此异常。

    Examples:
        >>> raise CleanError("无法删除构建目录", {"path": "/path/to/build"})
    """

    pass


class ConfigValidationError(SetupError):
    """配置验证失败错误

    当项目配置不符合要求时抛出此异常。

    Examples:
        >>> raise ConfigValidationError("入口文件不存在", {"entry_point": "main.py"})
    """

    pass
