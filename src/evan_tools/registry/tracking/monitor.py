"""性能监控器"""

from .tracker import ExecutionTracker
from .models import PerformanceStats


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, tracker: ExecutionTracker) -> None:
        """初始化监控器"""
        self._tracker = tracker
    
    def get_stats(self, command_name: str) -> PerformanceStats | None:
        """获取指定命令的性能统计"""
        return self._tracker.get_store().calculate_stats(command_name)
    
    def get_all_stats(self) -> dict[str, PerformanceStats]:
        """获取所有命令的性能统计"""
        return self._tracker.get_store().get_all_stats()
    
    def reset_stats(self) -> None:
        """重置所有统计"""
        self._tracker.clear_history()
