import typing as t
from enum import Enum
from pathlib import Path


class SortBy(Enum):
    """文件排序方式枚举。"""

    NAME = "name"
    SIZE = "size"
    MTIME = "mtime"
    CTIME = "ctime"
    EXTENSION = "ext"


def _make_sort_key(sort_by: SortBy | None) -> t.Callable[[Path], t.Any]:
    """创建排序键函数。"""

    def _sort_key(path: Path) -> t.Any:
        try:
            if sort_by == SortBy.NAME:
                return path.name.lower()
            if sort_by == SortBy.EXTENSION:
                return path.suffix.lower()

            stat = path.stat()
            if sort_by == SortBy.SIZE:
                return stat.st_size
            if sort_by == SortBy.MTIME:
                return stat.st_mtime
            if sort_by == SortBy.CTIME:
                return stat.st_ctime
        except OSError:
            return 0

        return 0

    return _sort_key


__all__ = [
    "SortBy",
    "_make_sort_key",
]
