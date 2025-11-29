import os
import typing as t
from pathlib import Path


def gather_paths(
    path: Path,
    *,
    deep: bool | int = False,
    dir_only: bool = False,
    filter: t.Callable[[Path], bool] | None = None,
) -> t.Iterator[Path]:
    """
    递归或非递归地收集指定路径下的文件或目录。

    参数：
        path (Path): 要搜索的根路径。
        deep (bool | int): 是否进行深度搜索。
            - False: 仅搜索path下的直接子项（默认）
            - True: 递归搜索所有子项，深度无限制
            - int: 递归搜索，最大深度为指定的整数值
        dir_only (bool): 是否仅返回目录。
            - True: 仅返回目录路径
            - False: 仅返回文件路径（默认）
        filter (Callable[[Path], bool] | None): 可选的过滤函数。
            接收Path对象，返回True则该路径被包含在结果中。
            默认为None，表示接受所有路径。

    返回值：
        Iterator[Path]: 满足条件的路径迭代器。

    示例：
        >>> # 获取当前目录的所有直接子目录
        >>> list(gather_paths(Path('.'), dir_only=True))
        >>> # 递归获取所有Python文件
        >>> list(gather_paths(Path('.'), deep=True,
        ...                    filter=lambda p: p.suffix == '.py'))
        >>> # 获取最多2层深度的所有目录
        >>> list(gather_paths(Path('.'), deep=2, dir_only=True))
    """
    filter = filter or (lambda _: True)

    if not deep:
        with os.scandir(path) as entries:
            for entry in entries:
                if (dir_only and entry.is_dir()) or (not dir_only and entry.is_file()):
                    p = Path(entry.path)
                    if filter(p):
                        yield p
    else:
        max_depth = None if deep is True else deep

        for root, dirs, files in os.walk(path):
            rp = Path(root)
            current_depth = len(rp.relative_to(path).parts)
            if max_depth is not None and current_depth >= max_depth:
                dirs.clear()
            items = dirs if dir_only else files

            for name in items:
                p = rp / name
                if filter(p):
                    yield p
