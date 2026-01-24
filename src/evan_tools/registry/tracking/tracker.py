"""命令执行追踪器"""

import typing as t
from datetime import datetime
from .models import ExecutionRecord


class ExecutionTracker:
    """命令执行追踪器"""
    
    def __init__(self, store: t.Any | None = None) -> None:
        """初始化追踪器
        
        Args:
            store: InMemoryStore 实例，如果为 None 会在首次使用时创建
        """
        self._store = store
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
        
        # 延迟导入避免循环依赖
        if self._store is None:
            from ..storage.memory_store import InMemoryStore
            self._store = InMemoryStore()
        
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
        if self._store is None:
            return []
        return self._store.get_recent_records(limit=limit)
    
    def clear_history(self) -> None:
        """清空历史"""
        if self._store is None:
            return
        self._store.clear()
    
    def get_store(self) -> t.Any:
        """获取存储实例"""
        if self._store is None:
            from ..storage.memory_store import InMemoryStore
            self._store = InMemoryStore()
        return self._store
