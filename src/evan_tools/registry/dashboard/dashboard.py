"""注册表仪表板"""

import typing as t
from ..tracking.tracker import ExecutionTracker
from ..discovery.index import CommandIndex
from .formatter import TableFormatter, TableConfig
from .aggregator import StatsAggregator


class RegistryDashboard:
    """注册表仪表板 - 显示命令树、执行历史和性能统计"""
    
    def __init__(self, tracker: ExecutionTracker, cmd_index: CommandIndex) -> None:
        """初始化仪表板"""
        self._tracker = tracker
        self._cmd_index = cmd_index
        self._aggregator = StatsAggregator(tracker)
        self._formatter = TableFormatter()
    
    def show_command_tree(self) -> str:
        """显示命令树"""
        tree = self._cmd_index.get_command_tree()
        rows = self._aggregator.get_command_tree_formatted(tree)
        
        headers = ["组", "命令"]
        return self._formatter.format_table(headers, rows)
    
    def show_execution_history(self, limit: int = 20) -> str:
        """显示执行历史"""
        rows = self._aggregator.get_execution_records_formatted(limit=limit)
        
        headers = ["时间", "组", "命令", "状态", "耗时", "错误"]
        return self._formatter.format_table(headers, rows)
    
    def show_performance_stats(self) -> str:
        """显示性能统计"""
        rows = self._aggregator.get_performance_stats_formatted()
        
        headers = ["命令", "调用数", "平均时间", "最小时间", "最大时间", "错误数"]
        return self._formatter.format_table(headers, rows)
