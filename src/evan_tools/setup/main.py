"""向后兼容模块 - 重定向到新 API

警告：此模块已弃用。请不要直接从 main.py 导入。
请使用以下导入：

    from evan_tools.setup import ProjectConfig, create_orchestrator, run_cli

迁移指南：docs/SETUP_MIGRATION_GUIDE.md
"""

# 重定向到向后兼容层
from ._legacy import AutoDeployer, run_deployer
from .core import ProjectConfig

__all__ = ["AutoDeployer", "ProjectConfig", "run_deployer"]
