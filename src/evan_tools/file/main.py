import os
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
    
    def _should_include(self, path: Path) -> bool:
        """多层过滤：模式匹配 → 排除规则 → 属性过滤 → 自定义过滤器
        
        参数:
            path: 要检查的路径
        
        返回:
            是否应该包含此路径
        """
        name = path.name
        
        # 1. 模式匹配（如果指定了）
        if self._config.patterns:
            if not any(fnmatch.fnmatch(name, pat) for pat in self._config.patterns):
                return False
        
        # 2. 排除规则
        if self._config.excludes:
            if any(fnmatch.fnmatch(name, pat) for pat in self._config.excludes):
                return False
        
        # 3. 文件属性过滤（仅对文件）
        if path.is_file() and not self._config.dir_only:
            try:
                stat = path.stat()
                
                if self._config.size_min is not None and stat.st_size < self._config.size_min:
                    return False
                if self._config.size_max is not None and stat.st_size > self._config.size_max:
                    return False
                if self._config.mtime_after is not None and stat.st_mtime < self._config.mtime_after:
                    return False
                if self._config.mtime_before is not None and stat.st_mtime > self._config.mtime_before:
                    return False
            except OSError:
                return False
        
        # 4. 自定义过滤器
        if self._config.filter_func and not self._config.filter_func(path):
            return False
        
        return True
    
    def _get_sort_key(self, path: Path):
        """获取排序键
        
        参数:
            path: 路径对象
        
        返回:
            排序键值
        """
        try:
            if self._config.sort_by == SortBy.NAME:
                return path.name.lower()
            elif self._config.sort_by == SortBy.EXTENSION:
                return path.suffix.lower()
            
            stat = path.stat()
            if self._config.sort_by == SortBy.SIZE:
                return stat.st_size
            elif self._config.sort_by == SortBy.MTIME:
                return stat.st_mtime
            elif self._config.sort_by == SortBy.CTIME:
                return stat.st_ctime
        except OSError:
            return 0  # 出错时放在最前面
        
        return 0
    
    def _notify_progress(self, count: int) -> None:
        """通知进度
        
        参数:
            count: 当前已找到的文件数
        """
        if self._config.progress_callback:
            self._config.progress_callback(count)
    
    def _handle_error(self, path: Path, error: Exception) -> None:
        """处理错误
        
        参数:
            path: 出错的路径
            error: 异常对象
        """
        self._errors.append((path, error))
        if self._config.error_handler:
            self._config.error_handler(path, error)
    
    def _gather_flat_optimized(self, path: Path) -> t.Generator[Path, None, None]:
        """平面遍历（非递归）- 使用 scandir 优化性能
        
        参数:
            path: 要遍历的目录路径
        
        生成:
            匹配的路径
        """
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        entry_path = Path(entry.path)
                        
                        # 直接使用 entry 的方法，避免额外的 stat 调用
                        is_target = (
                            (self._config.dir_only and entry.is_dir(follow_symlinks=False))
                            or (not self._config.dir_only and entry.is_file(follow_symlinks=False))
                        )
                        
                        if is_target and self._should_include(entry_path):
                            yield entry_path
                    except OSError as e:
                        self._handle_error(entry_path, e)
        except OSError as e:
            self._handle_error(path, e)
    
    def _gather_recursive_optimized(self, path: Path, max_depth: int) -> t.Generator[Path, None, None]:
        """递归遍历 - 优化版本
        
        参数:
            path: 要遍历的目录路径
            max_depth: 最大深度
        
        生成:
            匹配的路径
        """
        try:
            for root, dirs, files in os.walk(path):
                rp = Path(root)
                
                # 深度计算
                try:
                    depth = len(rp.relative_to(path).parts) if rp != path else 0
                except ValueError:
                    continue
                
                # 深度控制
                if depth >= max_depth:
                    dirs.clear()
                if depth > max_depth:
                    continue

                # 在进入子目录前应用排除规则，避免递归到被排除的目录
                if self._config.excludes:
                    dirs[:] = [
                        d for d in dirs
                        if not any(fnmatch.fnmatch(d, pat) for pat in self._config.excludes)
                    ]
                
                # 选择要处理的项目
                items = dirs if self._config.dir_only else files
                
                for name in items:
                    item_path = rp / name
                    item_depth = depth + 1 if self._config.dir_only else depth
                    
                    try:
                        if item_depth <= max_depth and self._should_include(item_path):
                            yield item_path
                    except OSError as e:
                        self._handle_error(item_path, e)
        except OSError as e:
            self._handle_error(path, e)
    
    def _collect_paths(self, max_depth: int, recursive: bool) -> t.Generator[Path, None, None]:
        """内部收集方法，处理遍历和过滤
        
        参数:
            max_depth: 最大深度
            recursive: 是否递归
        
        生成:
            匹配的路径
        """
        count = 0
        
        for path in self._paths:
            path = Path(path)
            
            # 处理根路径本身
            try:
                if not path.exists():
                    continue

                if path.is_file():
                    if not self._config.dir_only and self._should_include(path):
                        yield path
                        count += 1
                        self._notify_progress(count)
                    continue

                if path.is_dir():
                    if self._config.dir_only and self._should_include(path):
                        yield path
                        count += 1
                        self._notify_progress(count)
            except OSError as e:
                self._handle_error(path, e)
                continue
            
            if not path.is_dir():
                continue
            
            # 遍历子项
            if not recursive:
                for item_path in self._gather_flat_optimized(path):
                    yield item_path
                    count += 1
                    self._notify_progress(count)
            else:
                for item_path in self._gather_recursive_optimized(path, max_depth):
                    yield item_path
                    count += 1
                    self._notify_progress(count)
    
    def gather(self) -> t.Iterable[Path]:
        """执行路径收集
        
        返回:
            路径迭代器。如果设置了排序，返回列表；否则返回生成器以节省内存。
        """
        max_depth, recursive = _process_depth(self._config.deep)
        
        # 第一阶段：收集所有匹配的路径（使用生成器，节省内存）
        collected = self._collect_paths(max_depth, recursive)
        
        # 第二阶段：如果需要排序，必须物化为列表
        if self._config.sort_by:
            collected_list = list(collected)
            collected_list.sort(
                key=lambda p: self._get_sort_key(p),
                reverse=self._config.sort_reverse
            )
            yield from collected_list
        else:
            # 不排序时保持迭代器特性
            yield from collected


# 1. 参数解析 (保持不变)
def _process_depth(deep: bool | int) -> t.Tuple[int, bool]:
    if deep is False:
        return 1, False
    elif deep is True:
        return 10**6, True
    else:
        return deep, True


# 2. 根路径处理
def _handle_root_path(
    path: Path,
    dir_only: bool,
    path_filter: t.Callable[[Path], bool],
) -> t.Iterable[Path]:
    if not path.exists():
        return

    if path.is_file():
        if not dir_only and path_filter(path):
            yield path
    elif path.is_dir():
        if dir_only and path_filter(path):
            yield path


def _gather_flat(
    path: Path,
    dir_only: bool,
    path_filter: t.Callable[[Path], bool],
) -> t.Iterable[Path]:
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                entry_path = Path(entry.path)

                is_target_type = (dir_only and entry.is_dir()) or (
                    not dir_only and entry.is_file()
                )

                if is_target_type and path_filter(entry_path):
                    yield entry_path
    except OSError:
        pass


def _gather_recursive(
    path: Path,
    max_depth: int,
    dir_only: bool,
    path_filter: t.Callable[[Path], bool],
) -> t.Iterable[Path]:
    try:
        for root, dirs, files in os.walk(path):
            rp = Path(root)

            depth = 0
            if rp != path:
                try:
                    depth = len(rp.relative_to(path).parts)
                except ValueError:
                    continue

            if depth >= max_depth:
                dirs.clear()

            if depth > max_depth:
                continue

            items = dirs if dir_only else files

            for name in items:
                item_path = rp / name

                item_depth = depth + 1 if dir_only else depth

                if item_depth <= max_depth and path_filter(item_path):
                    yield item_path

    except OSError:
        pass


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

    path_filter = filter or (lambda _: True)
    max_depth, recursive = _process_depth(deep)

    for path in paths:
        path = Path(path)
        yield from _handle_root_path(path, dir_only, path_filter)

        if not path.is_dir():
            continue

        if not recursive:
            yield from _gather_flat(path, dir_only, path_filter)
        else:
            yield from _gather_recursive(path, max_depth, dir_only, path_filter)
