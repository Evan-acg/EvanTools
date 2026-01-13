import typing as t
from pathlib import Path


def remove_empty_folders(paths: list[Path]) -> t.Generator[Path, None, None]:
    """
    递归删除指定路径列表中的所有空文件夹。

    参数：
        paths (list[Path]): 要检查和删除空文件夹的路径列表。
    """

    for path in paths:
        if not path.is_dir():
            continue

        try:
            for child in path.iterdir():
                if child.is_dir():
                    remove_empty_folders([child])

            if not any(path.iterdir()):
                yield path
                path.rmdir()
        except OSError:
            pass
