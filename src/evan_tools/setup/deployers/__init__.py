"""Setup 模块部署器

提供本地文件系统部署的实现，包括文件复制、验证和回滚机制。

Examples:
    >>> from pathlib import Path
    >>> from .local import LocalDeployer
    >>> deployer = LocalDeployer()
    >>> result = deployer.deploy(Path("dist/myapp"), Path("/target"))
    >>> if result.success:
    ...     print(f"部署成功")

Exports:
    LocalDeployer: 本地文件系统部署器
    DeployerBase: 部署器抽象基类
"""

from .base import DeployerBase
from .local import LocalDeployer

__all__ = [
    "DeployerBase",
    "LocalDeployer",
]
