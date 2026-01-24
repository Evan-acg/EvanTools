"""命令执行追踪器"""

import typing as t
from datetime import datetime
from ..storage.memory_store import InMemoryStore
from .models import ExecutionRecord


class ExecutionTracker:
    """命令执行追踪器"""
    
    def __init__(self, store: InMemoryStore | None = None) -> None:
        """初始化追踪器"""
        self._store = store or InMemoryStore()
        self._is_tracking = False
    
    def start_tracking(self) -> None:
        """启用追踪"""
        self._is_tracking = True
    
    def stop_tracking(self) -> None:
        """禁用追踪"""
        self._is_tracking = False
    
    def is_tracking(self) -> bool:
        """检查是否启用追踪"""
        return self._is_tracking
    
    def record_execution(
        self,
        command_name: str,
        group: str | None,
        duration_ms: float,
        success: bool,
        error: str | None,
        args: tuple[t.Any, ...],
        kwargs: dict[str, t.Any],
    ) -> None:
        """记录命令执行"""
        if not self._is_tracking:
            return
        
        record = ExecutionRecord(
            command_name=command_name,
            group=group,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            success=success,
            error=error,
            args=args,
            kwargs=kwargs,
        )
        
        self._store.add_record(record)
    
    def get_execution_history(self, limit: int = 100) -> list[ExecutionRecord]:
        """获取执行历史"""
        return self._store.get_recent_records(limit=limit)
    
    def clear_history(self) -> None:
        """清空历史"""
        self._store.clear()
    
    def get_store(self) -> InMemoryStore:
        """获取存储实例"""
        return self._store
