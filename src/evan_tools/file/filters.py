import fnmatch
from pathlib import Path

from .config import FilterRules


class PathFilter:
    """路径过滤器类。"""

    def __init__(self, rules: FilterRules, *, dir_only: bool) -> None:
        self._rules = rules
        self._dir_only = dir_only

    @property
    def rules(self) -> FilterRules:
        return self._rules

    def __call__(self, path: Path) -> bool:
        name = path.name

        if self._rules.patterns and not any(
            fnmatch.fnmatch(name, pat) for pat in self._rules.patterns
        ):
            return False

        if self._rules.excludes and any(
            fnmatch.fnmatch(name, pat) for pat in self._rules.excludes
        ):
            return False

        if path.is_file() and not self._dir_only:
            try:
                stat = path.stat()
            except OSError:
                return False

            if self._rules.size_min is not None and stat.st_size < self._rules.size_min:
                return False
            if self._rules.size_max is not None and stat.st_size > self._rules.size_max:
                return False
            if (
                self._rules.mtime_after is not None
                and stat.st_mtime < self._rules.mtime_after
            ):
                return False
            if (
                self._rules.mtime_before is not None
                and stat.st_mtime > self._rules.mtime_before
            ):
                return False

        if self._rules.custom and not self._rules.custom(path):
            return False

        return True


__all__ = ["PathFilter"]
