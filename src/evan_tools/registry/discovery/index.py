"""命令索引"""

import typing as t
from .metadata import CommandMetadata
from .inspector import CommandInspector
from ..main import get_registry


class CommandIndex:
    """构建和查询命令索引"""
    
    def __init__(self) -> None:
        """初始化索引"""
        self._inspector = CommandInspector()
        self._metadata_cache: list[CommandMetadata] | None = None
    
    def get_all_commands(self) -> list[CommandMetadata]:
        """获取所有已注册的命令"""
        if self._metadata_cache is None:
            self._rebuild_cache()
        return list(self._metadata_cache or [])
    
    def get_commands_by_group(self, group: str) -> list[CommandMetadata]:
        """按组名获取命令"""
        all_commands = self.get_all_commands()
        return [cmd for cmd in all_commands if cmd.group == group]
    
    def get_command_tree(self) -> dict[str | None, list[str]]:
        """获取命令树结构（按组组织）"""
        tree: dict[str | None, list[str]] = {}
        for cmd in self.get_all_commands():
            group = cmd.group or "_ungrouped"
            if group not in tree:
                tree[group] = []
            tree[group].append(cmd.name)
        return tree
    
    def search_commands(self, query: str) -> list[CommandMetadata]:
        """搜索命令（按名称或文档）"""
        query_lower = query.lower()
        all_commands = self.get_all_commands()
        results = []
        
        for cmd in all_commands:
            if query_lower in cmd.name.lower():
                results.append(cmd)
            elif cmd.docstring and query_lower in cmd.docstring.lower():
                results.append(cmd)
        
        return results
    
    def get_command_docs(self) -> str:
        """生成命令文档（Markdown 格式）"""
        lines = ["# 命令列表\n"]
        
        tree = self.get_command_tree()
        for group in sorted(tree.keys()):
            if group == "_ungrouped":
                lines.append("## 全局命令\n")
            else:
                lines.append(f"## 组: {group}\n")
            
            for cmd_name in sorted(tree[group]):
                cmd = next((c for c in self.get_all_commands() if c.name == cmd_name), None)
                if cmd:
                    doc = cmd.docstring or "无文档"
                    lines.append(f"- **{cmd_name}**: {doc}\n")
            
            lines.append("")
        
        return "".join(lines)
    
    def _rebuild_cache(self) -> None:
        """重建元数据缓存"""
        self._metadata_cache = []
        registry = get_registry()
        
        for group, name, func in registry:
            metadata = self._inspector.extract_metadata(
                name=name,
                func=func,
                group=group,
                module=func.__module__,
            )
            self._metadata_cache.append(metadata)
