"""数据聚合和统计"""

import typing as t
from ..tracking.tracker import ExecutionTracker


class StatsAggregator:
    """数据聚合和统计"""
    
    def __init__(self, tracker: ExecutionTracker) -> None:
        """初始化聚合器"""
        self._tracker = tracker
    
    def get_execution_records_formatted(self, limit: int = 20) -> list[list[str]]:
        """获取格式化的执行记录"""
        records = self._tracker.get_execution_history(limit=limit)
        rows = []
        
        for record in records:
            status = "✓" if record.success else "✗"
            timestamp = record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            error = record.error or "-"
            
            rows.append([
                timestamp,
                record.group or "-",
                record.command_name,
                status,
                f"{record.duration_ms:.2f}ms",
                    error.split(":")[0] if record.error else "-",
            ])
        
        return rows
    
    def get_performance_stats_formatted(self) -> list[list[str]]:
        """获取格式化的性能统计"""
        store = self._tracker.get_store()
        all_stats = store.get_all_stats()
        rows = []
        
        for cmd_name in sorted(all_stats.keys()):
            stats = all_stats[cmd_name]
            rows.append([
                stats.command_name,
                str(stats.call_count),
                f"{stats.avg_duration_ms:.2f}ms",
                f"{stats.min_duration_ms:.2f}ms",
                f"{stats.max_duration_ms:.2f}ms",
                str(stats.error_count),
            ])
        
        return rows
    
    def get_command_tree_formatted(self, tree: dict[str | None, list[str]]) -> list[list[str]]:
        """获取格式化的命令树"""
        rows = []
        
        for group in sorted(tree.keys()):
            group_name = group if group != "_ungrouped" else "（全局）"
            commands = sorted(tree[group])
            
            for i, cmd in enumerate(commands):
                if i == 0:
                    rows.append([group_name, cmd])
                else:
                    rows.append(["", cmd])
        
        return rows
