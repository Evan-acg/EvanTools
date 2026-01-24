import os
import sys
import typing as t
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
import fnmatch


class SortBy(Enum):
    """文件排序方式枚举
    
    定义 PathGatherer 支持的排序键类型。
    """
    NAME = "name"          # 按文件名（不区分大小写）
    SIZE = "size"          # 按文件大小（字节）
    MTIME = "mtime"        # 按修改时间（Unix 时间戳）
    CTIME = "ctime"        # 按创建时间（Unix 时间戳）
    EXTENSION = "ext"      # 按扩展名（不区分大小写）


@dataclass
class GatherConfig:
    """路径收集配置
    
    属性:
        deep: 递归深度控制
            - False: 仅扫描直接子项（默认）
            - True: 无限递归
            - int: 限定递归深度
        dir_only: 是否仅返回目录（False 表示仅返回文件）
        patterns: 包含模式列表（glob 语法，如 '*.py'）
        excludes: 排除模式列表（glob 语法，如 '*.pyc'）
        filter_func: 自定义过滤函数，接收 Path 返回 bool
        sort_by: 排序方式（SortBy 枚举）
        sort_reverse: 是否倒序排序
        size_min: 最小文件大小（字节），None 表示不限制
        size_max: 最大文件大小（字节），None 表示不限制
        mtime_after: 修改时间下限（Unix 时间戳），仅包含此时间之后修改的文件
        mtime_before: 修改时间上限（Unix 时间戳），仅包含此时间之前修改的文件
        progress_callback: 进度回调函数，参数为已找到的文件总数（int）
        error_handler: 错误处理回调函数，参数为 (路径: Path, 异常: Exception)
    """
    deep: bool | int = False
    dir_only: bool = False
    patterns: list[str] = field(default_factory=list)
    excludes: list[str] = field(default_factory=list)
    filter_func: t.Callable[[Path], bool] | None = None
    sort_by: SortBy | None = None
    sort_reverse: bool = False
    # 文件属性过滤
    size_min: int | None = None
    size_max: int | None = None
    mtime_after: float | None = None
    mtime_before: float | None = None
    # 回调
    progress_callback: t.Callable[[int], None] | None = None
    error_handler: t.Callable[[Path, Exception], None] | None = None


@dataclass(frozen=True)
class FilterRules:
    patterns: tuple[str, ...] = ()
    excludes: tuple[str, ...] = ()
    size_min: int | None = None
    size_max: int | None = None
    mtime_after: float | None = None
    mtime_before: float | None = None
    custom: t.Callable[[Path], bool] | None = None


@dataclass(frozen=True)
class TraversalOptions:
    max_depth: int
    recursive: bool
    dir_only: bool
    sort_by: SortBy | None = None
    sort_reverse: bool = False
    progress_callback: t.Callable[[int], None] | None = None
    error_handler: t.Callable[[Path, Exception], None] | None = None


def _make_sort_key(sort_by: SortBy | None) -> t.Callable[[Path], t.Any]:
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


class PathFilter:
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


class PathCollector:
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

    def _yield_recursive(
        self, path: Path, count: int
    ) -> t.Generator[Path, None, int]:
        try:
            for root, dirs, files in os.walk(path):
                rp = Path(root)

                try:
                    depth = len(rp.relative_to(path).parts) if rp != path else 0
                except ValueError:
                    continue

                # 超过最大深度时跳过当前层
                if depth > self._options.max_depth:
                    continue

                # 达到最大深度时，清空dirs防止进一步递归
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


class PathGatherer:
    """路径收集器 - 链式调用构建器
    
    提供灵活的文件/目录收集功能，支持模式匹配、排序、属性过滤等高级特性。
    使用链式调用构建配置，最后调用 gather() 执行收集。
    
    示例:
        # 查找所有 Python 文件，按大小排序
        gatherer = (PathGatherer(["."], deep=True)
            .pattern("*.py")
            .exclude("*.pyc")
            .sort_by(SortBy.SIZE, reverse=True))
        
        for path in gatherer.gather():
            print(path)
    """
    
    def __init__(self, paths: t.Iterable[Path | str], *, deep: bool | int = False):
        """初始化收集器
        
        参数:
            paths: 要搜索的根路径列表
            deep: 递归深度控制
                - False: 仅扫描直接子项（默认）
                - True: 无限递归
                - int: 限定递归深度
        """
        self._paths = [Path(p) for p in paths]
        self._config = GatherConfig(deep=deep)
        self._errors: list[tuple[Path, Exception]] = []
    
    def pattern(self, *patterns: str) -> "PathGatherer":
        """添加匹配模式，支持 glob 语法
        
        参数:
            patterns: glob 模式 (如 *.py, test_*.txt)
        
        返回:
            self (支持链式调用)
        """
        self._config.patterns.extend(patterns)
        return self
    
    def exclude(self, *patterns: str) -> "PathGatherer":
        """添加排除模式，支持 glob 语法
        
        参数:
            patterns: glob 模式 (如 *.pyc, __pycache__)
        
        返回:
            self (支持链式调用)
        """
        self._config.excludes.extend(patterns)
        return self
    
    def directories_only(self, enable: bool = True) -> "PathGatherer":
        """仅返回目录而非文件。"""

        self._config.dir_only = enable
        return self

    def sort_by(self, key: SortBy, *, reverse: bool = False) -> "PathGatherer":
        """设置排序方式
        
        参数:
            key: 排序键 (SortBy 枚举)
            reverse: 是否倒序
        
        返回:
            self (支持链式调用)
        """
        self._config.sort_by = key
        self._config.sort_reverse = reverse
        return self
    
    def filter_by(
        self, 
        *, 
        size_min: int | None = None,
        size_max: int | None = None,
        mtime_after: float | None = None,
        mtime_before: float | None = None
    ) -> "PathGatherer":
        """按文件属性过滤
        
        参数:
            size_min: 最小文件大小（字节）
            size_max: 最大文件大小（字节）
            mtime_after: 修改时间下限（Unix 时间戳）
            mtime_before: 修改时间上限（Unix 时间戳）
        
        返回:
            self (支持链式调用)
        """
        if size_min is not None:
            self._config.size_min = size_min
        if size_max is not None:
            self._config.size_max = size_max
        if mtime_after is not None:
            self._config.mtime_after = mtime_after
        if mtime_before is not None:
            self._config.mtime_before = mtime_before
        return self

    def custom_filter(self, func: t.Callable[[Path], bool]) -> "PathGatherer":
        """设置自定义过滤函数。"""

        self._config.filter_func = func
        return self
    
    def on_progress(self, callback: t.Callable[[int], None]) -> "PathGatherer":
        """设置进度回调
        
        参数:
            callback: 回调函数，参数为已找到的文件数
        
        返回:
            self (支持链式调用)
        """
        self._config.progress_callback = callback
        return self
    
    @property
    def errors(self) -> list[tuple[Path, Exception]]:
        """获取收集过程中遇到的错误
        
        返回:
            错误列表，每项为 (路径, 异常) 元组
        """
        return self._errors.copy()
    
    def gather(self) -> t.Iterable[Path]:
        """执行路径收集
        
        返回:
            路径迭代器。如果设置了排序，返回列表；否则返回生成器以节省内存。
        """
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


def _process_depth(deep: bool | int) -> t.Tuple[int, bool]:
    if deep is False:
        return 1, False
    elif deep is True:
        return sys.maxsize, True
    else:
        return deep, True


def gather_paths(
    paths: t.Iterable[Path | str],
    *,
    deep: bool | int = False,
    dir_only: bool = False,
    filter: t.Callable[[Path], bool] | None = None,
) -> t.Iterable[Path]:
    """
    递归或非递归地收集指定路径下的文件或目录。

    参数：
        paths (t.Iterator[Path]): 要搜索的根路径。
        deep (bool | int): 是否进行深度搜索。
            - False: 仅搜索path下的直接子项（默认）
            - True: 递归搜索所有子项，深度无限制
            - int: 递归搜索，最大深度为指定的整数值
        dir_only (bool): 是否仅返回目录。
            - True: 仅返回目录路径
            - False: 仅返回文件路径（默认）
        filter (Callable[[Path], bool] | None): 可选的过滤函数。
            接收Path对象，返回True则该路径被包含在结果中。

    返回值：
        t.Iterable[Path]: 满足条件的路径迭代器。
    """
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
