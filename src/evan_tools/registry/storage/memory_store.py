"""内存存储实现"""

import typing as t
from ..tracking.models import ExecutionRecord, PerformanceStats


class InMemoryStore:
    """内存存储实现"""
    
    def __init__(self, max_records: int = 10000) -> None:
        """初始化存储"""
        self._records: list[ExecutionRecord] = []
        self._max_records = max_records
    
    def add_record(self, record: ExecutionRecord) -> None:
        """添加执行记录"""
        self._records.append(record)
        
        # 限制记录数量，防止内存溢出
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]
    
    def get_all_records(self) -> list[ExecutionRecord]:
        """获取所有记录"""
        return list(self._records)
    
    def get_recent_records(self, limit: int = 100) -> list[ExecutionRecord]:
        """获取最近的记录"""
        return list(self._records[-limit:])
    
    def get_records_by_command(self, command_name: str) -> list[ExecutionRecord]:
        """按命令名获取记录"""
        return [r for r in self._records if r.command_name == command_name]
    
    def clear(self) -> None:
        """清空存储"""
        self._records.clear()
    
    def calculate_stats(self, command_name: str) -> PerformanceStats | None:
        """计算命令的性能统计"""
        records = self.get_records_by_command(command_name)
        
        if not records:
            return None
        
        durations = [r.duration_ms for r in records]
        error_count = sum(1 for r in records if not r.success)
        
        return PerformanceStats(
            command_name=command_name,
            call_count=len(records),
            total_duration_ms=sum(durations),
            avg_duration_ms=sum(durations) / len(durations),
            min_duration_ms=min(durations),
            max_duration_ms=max(durations),
            error_count=error_count,
        )
    
    def get_all_stats(self) -> dict[str, PerformanceStats]:
        """获取所有命令的统计"""
        command_names = set(r.command_name for r in self._records)
        stats_dict: dict[str, PerformanceStats] = {}
        for cmd in command_names:
            stat = self.calculate_stats(cmd)
            if stat is not None:
                stats_dict[cmd] = stat
        return stats_dict
