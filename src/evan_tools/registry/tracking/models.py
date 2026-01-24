"""追踪层数据模型"""

import typing as t
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExecutionRecord:
    """命令执行审计记录"""
    command_name: str
    group: str | None
    timestamp: datetime
    duration_ms: float
    success: bool
    error: str | None
    args: tuple[t.Any, ...]
    kwargs: dict[str, t.Any]


@dataclass
class PerformanceStats:
    """命令性能统计"""
    command_name: str
    call_count: int
    total_duration_ms: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    error_count: int
