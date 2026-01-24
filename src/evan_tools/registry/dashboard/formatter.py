"""表格格式化器"""

from dataclasses import dataclass


@dataclass
class TableConfig:
    """表格配置"""
    padding: int = 2
    border_char: str = "-"
    col_sep: str = "|"


class TableFormatter:
    """表格格式化器"""
    
    def __init__(self, config: TableConfig | None = None) -> None:
        """初始化格式化器"""
        self.config = config or TableConfig()
    
    def format_table(
        self,
        headers: list[str],
        rows: list[list[str]],
    ) -> str:
        """格式化表格"""
        if not headers or not rows:
            if headers and not rows:
                # 只有表头的情况，返回表头
                col_widths = [len(h) + self.config.padding * 2 for h in headers]
                lines = []
                lines.append(self._build_border(col_widths))
                lines.append(self._build_row(headers, col_widths))
                lines.append(self._build_border(col_widths))
                return "\n".join(lines)
            return ""
        
        # 计算列宽
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # 添加填充
        col_widths = [w + self.config.padding * 2 for w in col_widths]
        
        # 构建表格
        lines = []
        
        # 顶部边界
        lines.append(self._build_border(col_widths))
        
        # 表头
        lines.append(self._build_row(headers, col_widths))
        
        # 表头下边界
        lines.append(self._build_border(col_widths))
        
        # 数据行
        for row in rows:
            lines.append(self._build_row(row, col_widths))
        
        # 底部边界
        lines.append(self._build_border(col_widths))
        
        return "\n".join(lines)
    
    def _build_border(self, col_widths: list[int]) -> str:
        """构建边界行"""
        parts = []
        for width in col_widths:
            parts.append(self.config.border_char * width)
        return self.config.col_sep.join(parts)
    
    def _build_row(self, cells: list[str], col_widths: list[int]) -> str:
        """构建数据行"""
        parts = []
        for i, cell in enumerate(cells):
            padding_left = self.config.padding
            padding_right = col_widths[i] - len(str(cell)) - padding_left
            padded = " " * padding_left + str(cell) + " " * padding_right
            parts.append(padded)
        return self.config.col_sep.join(parts)
