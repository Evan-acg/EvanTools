"""Setup 模块 - Python 项目构建和部署工具

该模块提供了自动化构建和部署 Python 项目的功能。

主要组件：
- ProjectConfig: 项目配置
- Orchestrator: 编排器（协调构建、部署、清理）
- PyInstallerBuilder: PyInstaller 构建器
- LocalDeployer: 本地文件系统部署器
- FileSystemCleaner: 文件系统清理器

快速开始：
    >>> from evan_tools.setup import ProjectConfig, create_orchestrator
    >>> config = ProjectConfig(name="myapp", entry_point="main.py")
    >>> orchestrator = create_orchestrator(config)
    >>> result = orchestrator.build()

CLI 使用：
    >>> from evan_tools.setup.cli import run_cli
    >>> run_cli(config)  # 启动交互式 CLI
"""

# 核心组件
from .core import (
    BuildError,
    BuildResult,
    BuilderProtocol,
    CleanError,
    CleanerProtocol,
    CleanResult,
    ConfigValidationError,
    DeployError,
    DeployerProtocol,
    DeployResult,
    Orchestrator,
    ProjectConfig,
    SetupError,
)

# 具体实现
from .builders import PyInstallerBuilder
from .cleaners import FileSystemCleaner
from .deployers import LocalDeployer

# CLI
from .cli import create_orchestrator, run_cli

# 向后兼容（deprecated）
from ._legacy import AutoDeployer, run_deployer

__version__ = "2.0.0"

__all__ = [
    # 核心配置
    "ProjectConfig",
    # 编排器
    "Orchestrator",
    "create_orchestrator",
    # 构建器
    "PyInstallerBuilder",
    "BuilderProtocol",
    # 部署器
    "LocalDeployer",
    "DeployerProtocol",
    # 清理器
    "FileSystemCleaner",
    "CleanerProtocol",
    # 结果模型
    "BuildResult",
    "DeployResult",
    "CleanResult",
    # 异常
    "SetupError",
    "BuildError",
    "DeployError",
    "CleanError",
    "ConfigValidationError",
    # CLI
    "run_cli",
    # 向后兼容 (deprecated)
    "AutoDeployer",
    "run_deployer",
]

