"""命令元数据定义。

封装命令的名称、分组、文档与签名信息。
"""

import inspect
import typing as t
from dataclasses import dataclass


@dataclass
class CommandMetadata:
    """命令元数据信息，供索引与展示使用。"""
    name: str
    group: str | None
    func: t.Callable[..., None]
    docstring: str | None
    module: str
    signature: inspect.Signature
    
    def __post_init__(self) -> None:
        """验证必要字段，确保元数据有效。"""
        if not self.name:
            raise ValueError("Command name cannot be empty")
        if not self.module:
            raise ValueError("Module cannot be empty")
