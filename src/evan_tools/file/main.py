import os
import typing as t
from pathlib import Path


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
