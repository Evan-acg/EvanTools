"""命令检查器。

负责从可调用对象提取命令元数据，供索引与文档生成使用。
"""

import inspect
import typing as t
from .metadata import CommandMetadata


class CommandInspector:
    """提取并分析命令元数据。"""
    
    def extract_metadata(
        self,
        name: str,
        func: t.Callable[..., None],
        group: str | None,
        module: str,
    ) -> CommandMetadata:
        """从函数提取命令元数据。

        Args:
            name: 命令名称。
            func: 需要注册的可调用对象。
            group: 分组名称，可选。
            module: 模块名称。

        Returns:
            命令元数据对象，包含签名与文档摘要。
        """
        signature = inspect.signature(func)
        docstring = self._extract_first_line_of_docstring(func)
        
        return CommandMetadata(
            name=name,
            group=group,
            func=func,
            docstring=docstring,
            module=module,
            signature=signature,
        )
    
    @staticmethod
    def _extract_first_line_of_docstring(func: t.Callable[..., None]) -> str | None:
        """提取函数文档字符串的第一行作为摘要。"""
        doc = inspect.getdoc(func)
        if not doc:
            return None
        
        first_line = doc.split('\n')[0].strip()
        return first_line if first_line else None
