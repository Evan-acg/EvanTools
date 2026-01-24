"""命令注册表的公开接口。

对外导出注册、加载与 Typer 集成工具。
"""

from .main import (
    get_registry,
    load_commands,
    register_command,
    register_with_typer,
    RegistryManager,
)

__all__ = [
    "register_command",
    "get_registry",
    "register_with_typer",
    "load_commands",
    "RegistryManager",
]
