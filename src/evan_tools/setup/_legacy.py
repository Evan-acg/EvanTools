"""向后兼容层 - 已弃用的 API

警告：此模块中的 API 已弃用，将在未来版本中移除。
请使用新的 API：
- 使用 Orchestrator 代替 AutoDeployer
- 使用 run_cli 代替 run_deployer

迁移指南：docs/SETUP_MIGRATION_GUIDE.md
"""

import warnings
from pathlib import Path

from .cli import create_orchestrator
from .core import ProjectConfig


class AutoDeployer:
    """旧版 AutoDeployer 类 - 已弃用

    警告:
        此类已弃用，将在 3.0.0 版本中移除。
        请使用 Orchestrator 类代替。

    Examples:
        >>> # 旧代码 (deprecated)
        >>> deployer = AutoDeployer(config)
        >>> deployer.build()
        >>>
        >>> # 新代码 (推荐)
        >>> from evan_tools.setup import create_orchestrator
        >>> orchestrator = create_orchestrator(config)
        >>> orchestrator.build()
    """

    def __init__(self, config: ProjectConfig):
        """初始化 AutoDeployer（已弃用）

        Args:
            config: 项目配置
        """
        warnings.warn(
            "AutoDeployer 已弃用，请使用 Orchestrator。"
            "详见迁移指南: docs/SETUP_MIGRATION_GUIDE.md",
            DeprecationWarning,
            stacklevel=2,
        )
        self._orchestrator = create_orchestrator(config)
        self.config = config

    def clean(self) -> None:
        """清理构建文件（已弃用）

        警告:
            此方法已弃用，请使用 orchestrator.cleaner.clean_all()
        """
        warnings.warn(
            "AutoDeployer.clean() 已弃用，请使用 orchestrator.cleaner.clean_all()",
            DeprecationWarning,
            stacklevel=2,
        )
        self._orchestrator.cleaner.clean_all()

    def build(self) -> None:
        """构建项目（已弃用）

        警告:
            此方法已弃用，请使用 orchestrator.build()
        """
        warnings.warn(
            "AutoDeployer.build() 已弃用，请使用 orchestrator.build()",
            DeprecationWarning,
            stacklevel=2,
        )
        self._orchestrator.build()

    def deploy(self, target_folder: Path, *, clean_dist: bool = True) -> None:
        """部署项目（已弃用）

        Args:
            target_folder: 目标文件夹
            clean_dist: 是否清理 dist 目录

        警告:
            此方法已弃用，请使用 orchestrator.deploy()
        """
        warnings.warn(
            "AutoDeployer.deploy() 已弃用，请使用 orchestrator.deploy()",
            DeprecationWarning,
            stacklevel=2,
        )
        self._orchestrator.deploy(target_folder, clean_dist=clean_dist)


def run_deployer(config: ProjectConfig) -> None:
    """运行部署器 CLI（已弃用）

    Args:
        config: 项目配置

    警告:
        此函数已弃用，将在 3.0.0 版本中移除。
        请使用 run_cli(config) 代替。

    Examples:
        >>> # 旧代码 (deprecated)
        >>> run_deployer(config)
        >>>
        >>> # 新代码 (推荐)
        >>> from evan_tools.setup.cli import run_cli
        >>> run_cli(config)
    """
    warnings.warn(
        "run_deployer() 已弃用，请使用 run_cli()。"
        "详见迁移指南: docs/SETUP_MIGRATION_GUIDE.md",
        DeprecationWarning,
        stacklevel=2,
    )

    from .cli import run_cli

    run_cli(config)
