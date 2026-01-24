"""Setup 模块核心组件

该包包含 setup 模块的核心抽象和数据模型。
"""

from .config import ProjectConfig
from .exceptions import (
    BuildError,
    CleanError,
    ConfigValidationError,
    DeployError,
    SetupError,
)
from .models import BuildResult, CleanResult, DeployResult
from .protocols import BuilderProtocol, CleanerProtocol, DeployerProtocol

__all__ = [
    # 配置
    "ProjectConfig",
    # 异常
    "SetupError",
    "BuildError",
    "DeployError",
    "CleanError",
    "ConfigValidationError",
    # 模型
    "BuildResult",
    "DeployResult",
    "CleanResult",
    # 协议
    "BuilderProtocol",
    "DeployerProtocol",
    "CleanerProtocol",
]
