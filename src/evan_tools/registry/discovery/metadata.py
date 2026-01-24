"""命令元数据定义"""

import inspect
import typing as t
from dataclasses import dataclass


@dataclass
class CommandMetadata:
    """命令元数据信息"""
    name: str
    group: str | None
    func: t.Callable[..., None]
    docstring: str | None
    module: str
    signature: inspect.Signature
    
    def __post_init__(self) -> None:
        """验证数据有效性"""
        if not self.name:
            raise ValueError("Command name cannot be empty")
        if not self.module:
            raise ValueError("Module cannot be empty")
