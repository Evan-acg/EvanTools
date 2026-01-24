from dataclasses import dataclass, field
from pathlib import Path
import typing as t

from .sorting import SortBy


@dataclass
class GatherConfig:
    """路径收集配置类。

    用于配置 PathGatherer 的行为，包括递归深度、过滤规则、排序方式等。
    """

    deep: bool | int = False
    dir_only: bool = False
    patterns: list[str] = field(default_factory=list)
    excludes: list[str] = field(default_factory=list)
    filter_func: t.Callable[[Path], bool] | None = None
    sort_by: SortBy | None = None
    sort_reverse: bool = False
    size_min: int | None = None
    size_max: int | None = None
    mtime_after: float | None = None
    mtime_before: float | None = None
    progress_callback: t.Callable[[int], None] | None = None
    error_handler: t.Callable[[Path, Exception], None] | None = None


@dataclass(frozen=True)
class FilterRules:
    """不可变的过滤规则配置类。

    封装路径过滤所需的各种规则，包括模式匹配、大小和时间范围过滤等。
    """

    patterns: tuple[str, ...] = ()
    excludes: tuple[str, ...] = ()
    size_min: int | None = None
    size_max: int | None = None
    mtime_after: float | None = None
    mtime_before: float | None = None
    custom: t.Callable[[Path], bool] | None = None


@dataclass(frozen=True)
class TraversalOptions:
    """不可变的遍历选项配置类。

    封装路径遍历所需的配置选项，包括深度控制、递归模式、目标类型等。
    """

    max_depth: int
    recursive: bool
    dir_only: bool
    sort_by: SortBy | None = None
    sort_reverse: bool = False
    progress_callback: t.Callable[[int], None] | None = None
    error_handler: t.Callable[[Path, Exception], None] | None = None


__all__ = [
    "GatherConfig",
    "FilterRules",
    "TraversalOptions",
]
