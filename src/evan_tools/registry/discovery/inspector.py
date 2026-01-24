"""命令检查器"""

import inspect
import typing as t
from .metadata import CommandMetadata


class CommandInspector:
    """提取和分析命令元数据的检查器"""
    
    def extract_metadata(
        self,
        name: str,
        func: t.Callable[..., None],
        group: str | None,
        module: str,
    ) -> CommandMetadata:
        """从函数提取元数据"""
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
        """提取函数文档字符串的第一行"""
        doc = inspect.getdoc(func)
        if not doc:
            return None
        
        first_line = doc.split('\n')[0].strip()
        return first_line if first_line else None
