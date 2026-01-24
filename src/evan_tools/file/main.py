import fnmatch
import os
import sys
import typing as t
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class SortBy(Enum):
    """文件排序方式枚举。

    定义 PathGatherer 支持的排序键类型。

    Attributes:
        NAME: 按文件名排序（不区分大小写）
        SIZE: 按文件大小排序（字节）
        MTIME: 按修改时间排序（Unix时间戳）
        CTIME: 按创建时间排序（Unix时间戳）
        EXTENSION: 按扩展名排序（不区分大小写）
    """

    NAME = "name"
    SIZE = "size"
    MTIME = "mtime"
    CTIME = "ctime"
    EXTENSION = "ext"


@dataclass
class GatherConfig:
    """路径收集配置类。

    用于配置PathGatherer的行为，包括递归深度、过滤规则、排序方式等。

    Attributes:
        deep: 递归深度控制，False表示仅扫描直接子项，True表示无限递归，
            int表示限定递归深度
        dir_only: 是否仅返回目录，False表示仅返回文件
        patterns: 包含模式列表，使用glob语法（如'*.py'）
        excludes: 排除模式列表，使用glob语法（如'*.pyc'）
        filter_func: 自定义过滤函数，接收Path返回bool
        sort_by: 排序方式，使用SortBy枚举
        sort_reverse: 是否倒序排序
        size_min: 最小文件大小（字节），None表示不限制
        size_max: 最大文件大小（字节），None表示不限制
        mtime_after: 修改时间下限（Unix时间戳），仅包含此时间之后修改的文件
        mtime_before: 修改时间上限（Unix时间戳），仅包含此时间之前修改的文件
        progress_callback: 进度回调函数，参数为已找到的文件总数
        error_handler: 错误处理回调函数，参数为(路径, 异常)元组
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

    Attributes:
        patterns: 包含模式元组，使用glob语法
        excludes: 排除模式元组，使用glob语法
        size_min: 最小文件大小（字节）
        size_max: 最大文件大小（字节）
        mtime_after: 修改时间下限（Unix时间戳）
        mtime_before: 修改时间上限（Unix时间戳）
        custom: 自定义过滤函数
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

    Attributes:
        max_depth: 最大递归深度
        recursive: 是否递归遍历
        dir_only: 是否仅返回目录
        sort_by: 排序方式
        sort_reverse: 是否倒序排序
        progress_callback: 进度回调函数
        error_handler: 错误处理回调函数
    """

    max_depth: int
    recursive: bool
    dir_only: bool
    sort_by: SortBy | None = None
    sort_reverse: bool = False
    progress_callback: t.Callable[[int], None] | None = None
    error_handler: t.Callable[[Path, Exception], None] | None = None


def _make_sort_key(sort_by: SortBy | None) -> t.Callable[[Path], t.Any]:
    """创建排序键函数。

    根据指定的排序方式，生成用于提取路径排序键的函数。
    对于OSError异常，返回0作为默认值。

    Args:
        sort_by: 排序方式枚举，指定按哪个属性排序

    Returns:
        一个函数，接收Path对象，返回可比较的排序键值
    """
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
    """路径过滤器类。

    封装路径过滤逻辑，包括模式匹配、排除规则、文件属性过滤和自定义过滤。

    Attributes:
        _rules: 过滤规则对象
        _dir_only: 是否仅处理目录
    """

    def __init__(self, rules: FilterRules, *, dir_only: bool) -> None:
        """初始化路径过滤器。

        Args:
            rules: 过滤规则配置对象
            dir_only: 是否仅处理目录
        """
        self._rules = rules
        self._dir_only = dir_only

    @property
    def rules(self) -> FilterRules:
        """获取过滤规则。

        Returns:
            当前的过滤规则对象
        """
        return self._rules

    def __call__(self, path: Path) -> bool:
        """检查路径是否符合过滤条件。

        按顺序执行：模式匹配、排除规则、文件属性过滤、自定义过滤。

        Args:
            path: 要检查的路径对象

        Returns:
            如果路径符合所有过滤条件则返回True，否则返回False
        """
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
    """路径收集器类。

    负责遍历文件系统并收集符合条件的路径，支持递归和非递归模式。
    集成进度回调和错误处理机制。

    Attributes:
        _options: 遍历选项配置
        _filter: 路径过滤器
        _errors: 错误记录列表
    """

    def __init__(
        self,
        options: TraversalOptions,
        path_filter: PathFilter,
        errors: list[tuple[Path, Exception]] | None = None,
    ) -> None:
        """初始化路径收集器。

        Args:
            options: 遍历选项配置对象
            path_filter: 路径过滤器对象
            errors: 可选的错误列表，用于共享错误记录
        """
        self._options = options
        self._filter = path_filter
        self._errors = errors if errors is not None else []

    @property
    def errors(self) -> list[tuple[Path, Exception]]:
        """获取错误记录列表。

        Returns:
            包含(路径, 异常)元组的列表
        """
        return self._errors

    def collect(self, paths: t.Iterable[Path | str]) -> t.Iterable[Path]:
        """收集符合条件的路径。

        遍历指定的路径列表，根据配置选项执行递归或非递归扫描。

        Args:
            paths: 要扫描的路径列表

        Yields:
            符合过滤条件的Path对象
        """
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
        """通知进度回调函数。

        Args:
            count: 当前已找到的路径数量
        """
        if self._options.progress_callback:
            self._options.progress_callback(count)

    def _handle_error(self, path: Path, error: Exception) -> None:
        """处理错误。

        记录错误并调用错误处理回调函数（如果配置了）。

        Args:
            path: 出错的路径
            error: 异常对象
        """
        self._errors.append((path, error))
        if self._options.error_handler:
            self._options.error_handler(path, error)

    def _yield_flat(self, path: Path, count: int) -> t.Generator[Path, None, int]:
        """非递归扫描目录。

        仅扫描目录的直接子项，不进入子目录。

        Args:
            path: 要扫描的目录路径
            count: 当前计数

        Yields:
            符合条件的路径

        Returns:
            更新后的计数值
        """
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
        """检查是否应该进入指定目录。

        根据排除规则判断是否应该递归进入某个目录。

        Args:
            dir_name: 目录名称

        Returns:
            如果应该进入该目录则返回True，否则返回False
        """
        if not self._filter.rules.excludes:
            return True

        return not any(
            fnmatch.fnmatch(dir_name, pat) for pat in self._filter.rules.excludes
        )

    def _yield_recursive(self, path: Path, count: int) -> t.Generator[Path, None, int]:
        """递归扫描目录。

        递归遍历目录树，根据深度限制和过滤规则收集路径。

        Args:
            path: 要扫描的目录路径
            count: 当前计数

        Yields:
            符合条件的路径

        Returns:
            更新后的计数值
        """
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


class PathGatherer:
    """路径收集器 - 链式调用构建器。

    提供灵活的文件/目录收集功能，支持模式匹配、排序、属性过滤等高级特性。
    使用链式调用构建配置，最后调用gather()执行收集。

    Attributes:
        _paths: 要搜索的根路径列表
        _config: 收集配置对象
        _errors: 错误记录列表

    Examples:
        查找所有Python文件，按大小排序::

            gatherer = (PathGatherer(["."], deep=True)
                .pattern("*.py")
                .exclude("*.pyc")
                .sort_by(SortBy.SIZE, reverse=True))

            for path in gatherer.gather():
                print(path)
    """

    def __init__(self, paths: t.Iterable[Path | str], *, deep: bool | int = False):
        """初始化收集器。

        Args:
            paths: 要搜索的根路径列表
            deep: 递归深度控制，False表示仅扫描直接子项，True表示无限递归，
                int表示限定递归深度
        """
        self._paths = [Path(p) for p in paths]
        self._config = GatherConfig(deep=deep)
        self._errors: list[tuple[Path, Exception]] = []

    def pattern(self, *patterns: str) -> "PathGatherer":
        """添加匹配模式。

        支持glob语法进行模式匹配。

        Args:
            patterns: glob模式，如'*.py'、'test_*.txt'

        Returns:
            self，支持链式调用
        """
        self._config.patterns.extend(patterns)
        return self

    def exclude(self, *patterns: str) -> "PathGatherer":
        """添加排除模式。

        支持glob语法进行模式匹配。

        Args:
            patterns: glob模式，如'*.pyc'、'__pycache__'

        Returns:
            self，支持链式调用
        """
        self._config.excludes.extend(patterns)
        return self

    def sort_by(self, key: SortBy, *, reverse: bool = False) -> "PathGatherer":
        """设置排序方式。

        Args:
            key: 排序键，使用SortBy枚举
            reverse: 是否倒序

        Returns:
            self，支持链式调用
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
        mtime_before: float | None = None,
    ) -> "PathGatherer":
        """按文件属性过滤。

        Args:
            size_min: 最小文件大小，单位字节
            size_max: 最大文件大小，单位字节
            mtime_after: 修改时间下限，Unix时间戳
            mtime_before: 修改时间上限，Unix时间戳

        Returns:
            self，支持链式调用
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

    def on_progress(self, callback: t.Callable[[int], None]) -> "PathGatherer":
        """设置进度回调。

        Args:
            callback: 回调函数，接收已找到的文件数作为参数

        Returns:
            self，支持链式调用
        """
        self._config.progress_callback = callback
        return self

    @property
    def errors(self) -> list[tuple[Path, Exception]]:
        """获取收集过程中遇到的错误。

        Returns:
            错误列表，每项为(路径, 异常)元组
        """
        return self._errors.copy()

    def gather(self) -> t.Iterable[Path]:
        """执行路径收集。

        Returns:
            路径迭代器，如果设置了排序则返回列表，否则返回生成器以节省内存
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
    """处理深度参数。

    将用户提供的深度参数转换为内部使用的格式。

    Args:
        deep: 深度控制参数，False表示仅直接子项，True表示无限递归，
            int表示指定深度

    Returns:
        元组(max_depth, recursive)，其中max_depth为最大深度，
        recursive为是否递归
    """
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
    """递归或非递归地收集指定路径下的文件或目录。

    Args:
        paths: 要搜索的根路径
        deep: 深度控制，False表示仅搜索直接子项，True表示无限递归，
            int表示指定最大深度
        dir_only: 是否仅返回目录，True表示仅返回目录，False表示仅返回文件
        filter: 可选的过滤函数，接收Path对象，返回True则包含该路径

    Returns:
        满足条件的路径迭代器
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
