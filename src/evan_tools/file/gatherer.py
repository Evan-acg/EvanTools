import sys
import typing as t
from pathlib import Path

from .collector import PathCollector
from .config import GatherConfig, FilterRules, TraversalOptions
from .filters import PathFilter
from .sorting import SortBy, _make_sort_key


def _process_depth(deep: bool | int) -> tuple[int, bool]:
    if deep is False:
        return 1, False
    if deep is True:
        return sys.maxsize, True
    return deep, True


class PathGatherer:
    """路径收集器 - 链式调用构建器。"""

    def __init__(self, paths: t.Iterable[Path | str], *, deep: bool | int = False):
        self._paths = [Path(p) for p in paths]
        self._config = GatherConfig(deep=deep)
        self._errors: list[tuple[Path, Exception]] = []

    def pattern(self, *patterns: str) -> "PathGatherer":
        self._config.patterns.extend(patterns)
        return self

    def exclude(self, *patterns: str) -> "PathGatherer":
        self._config.excludes.extend(patterns)
        return self

    def sort_by(self, key: SortBy, *, reverse: bool = False) -> "PathGatherer":
        self._config.sort_by = key
        self._config.sort_reverse = reverse
        return self

    def filter_by(
        self,
        *,
        size_min: int | None = None,
        size_max: int | None = None,
        mtime_after: float | None = None,
        mtime_before: float | None = None,
    ) -> "PathGatherer":
        if size_min is not None:
            self._config.size_min = size_min
        if size_max is not None:
            self._config.size_max = size_max
        if mtime_after is not None:
            self._config.mtime_after = mtime_after
        if mtime_before is not None:
            self._config.mtime_before = mtime_before
        return self

    def on_progress(self, callback: t.Callable[[int], None]) -> "PathGatherer":
        self._config.progress_callback = callback
        return self

    @property
    def errors(self) -> list[tuple[Path, Exception]]:
        return self._errors.copy()

    def gather(self) -> t.Iterable[Path]:
        max_depth, recursive = _process_depth(self._config.deep)
        options = TraversalOptions(
            max_depth=max_depth,
            recursive=recursive,
            dir_only=self._config.dir_only,
            sort_by=self._config.sort_by,
            sort_reverse=self._config.sort_reverse,
            progress_callback=self._config.progress_callback,
            error_handler=self._config.error_handler,
        )
        rules = FilterRules(
            patterns=tuple(self._config.patterns),
            excludes=tuple(self._config.excludes),
            size_min=self._config.size_min,
            size_max=self._config.size_max,
            mtime_after=self._config.mtime_after,
            mtime_before=self._config.mtime_before,
            custom=self._config.filter_func,
        )
        path_filter = PathFilter(rules, dir_only=self._config.dir_only)
        collector = PathCollector(options, path_filter, errors=self._errors)
        collected = collector.collect(self._paths)

        if self._config.sort_by:
            sort_key = _make_sort_key(self._config.sort_by)
            collected_list = list(collected)
            collected_list.sort(key=sort_key, reverse=self._config.sort_reverse)
            yield from collected_list
        else:
            yield from collected


def gather_paths(
    paths: t.Iterable[Path | str],
    *,
    deep: bool | int = False,
    dir_only: bool = False,
    filter: t.Callable[[Path], bool] | None = None,
) -> t.Iterable[Path]:
    max_depth, recursive = _process_depth(deep)
    rules = FilterRules(custom=filter)
    path_filter = PathFilter(rules, dir_only=dir_only)
    options = TraversalOptions(
        max_depth=max_depth,
        recursive=recursive,
        dir_only=dir_only,
    )
    collector = PathCollector(options, path_filter)

    yield from collector.collect(paths)


__all__ = [
    "PathGatherer",
    "gather_paths",
    "_process_depth",
]
