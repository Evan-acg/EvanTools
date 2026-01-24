"""Setup 模块 CLI 层

提供命令行接口，用于与编排器交互。
"""

from .commands import create_orchestrator, run_cli

__all__ = ["create_orchestrator", "run_cli"]

