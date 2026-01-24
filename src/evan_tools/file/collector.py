import fnmatch
import os
import typing as t
from pathlib import Path

from .config import TraversalOptions
from .filters import PathFilter


class PathCollector:
    """路径收集器类。"""

    def __init__(
        self,
        options: TraversalOptions,
        path_filter: PathFilter,
        errors: list[tuple[Path, Exception]] | None = None,
    ) -> None:
        self._options = options
        self._filter = path_filter
        self._errors = errors if errors is not None else []

    @property
    def errors(self) -> list[tuple[Path, Exception]]:
        return self._errors

    def collect(self, paths: t.Iterable[Path | str]) -> t.Iterable[Path]:
        count = 0

        for raw_path in paths:
            path = Path(raw_path)

            if not path.exists():
                self._handle_error(path, FileNotFoundError(path))
                continue

            try:
                if path.is_file():
                    if not self._options.dir_only and self._filter(path):
                        count += 1
                        self._notify_progress(count)
                        yield path
                    continue

                if not path.is_dir():
                    continue

                if self._options.recursive:
                    count = yield from self._yield_recursive(path, count)
                else:
                    count = yield from self._yield_flat(path, count)
            except OSError as exc:
                self._handle_error(path, exc)

    def _notify_progress(self, count: int) -> None:
        if self._options.progress_callback:
            self._options.progress_callback(count)

    def _handle_error(self, path: Path, error: Exception) -> None:
        self._errors.append((path, error))
        if self._options.error_handler:
            self._options.error_handler(path, error)

    def _yield_flat(self, path: Path, count: int) -> t.Generator[Path, None, int]:
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    entry_path = Path(entry.path)
                    try:
                        if self._options.dir_only:
                            is_target = entry.is_dir(follow_symlinks=False)
                        else:
                            is_target = entry.is_file(follow_symlinks=False)

                        if is_target and self._filter(entry_path):
                            count += 1
                            self._notify_progress(count)
                            yield entry_path
                    except OSError as exc:
                        self._handle_error(entry_path, exc)
        except OSError as exc:
            self._handle_error(path, exc)

        return count

    def _should_descend(self, dir_name: str) -> bool:
        if not self._filter.rules.excludes:
            return True

        return not any(
            fnmatch.fnmatch(dir_name, pat) for pat in self._filter.rules.excludes
        )

    def _yield_recursive(self, path: Path, count: int) -> t.Generator[Path, None, int]:
        try:
            for root, dirs, files in os.walk(path):
                rp = Path(root)

                try:
                    depth = len(rp.relative_to(path).parts) if rp != path else 0
                except ValueError:
                    continue
                if depth > self._options.max_depth:
                    continue
                if depth == self._options.max_depth:
                    dirs.clear()

                if self._filter.rules.excludes:
                    dirs[:] = [d for d in dirs if self._should_descend(d)]

                items = dirs if self._options.dir_only else files

                for name in items:
                    item_path = rp / name
                    item_depth = depth + 1 if self._options.dir_only else depth

                    try:
                        if item_depth <= self._options.max_depth and self._filter(
                            item_path
                        ):
                            count += 1
                            self._notify_progress(count)
                            yield item_path
                    except OSError as exc:
                        self._handle_error(item_path, exc)
        except OSError as exc:
            self._handle_error(path, exc)

        return count


__all__ = ["PathCollector"]
