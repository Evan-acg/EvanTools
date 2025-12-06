import hashlib
import typing as t
from pathlib import Path

import humanize
from rich import print


class MD5Result(t.NamedTuple):
    path: Path
    md5: str
    status: bool
    message: str
    file_size: str


def calc_sparse_md5(
    item: Path, buffer_size: int = 8 * 1024 * 1024, segments: int = 10
) -> MD5Result:
    md5_hash = hashlib.md5()
    try:
        file_size: int = item.stat().st_size
        humanized_size: str = humanize.naturalsize(file_size)
        if file_size <= buffer_size * segments:
            with item.open("rb") as f:
                md5_hash.update(f.read())
                return MD5Result(
                    path=item,
                    message="Success",
                    md5=md5_hash.hexdigest(),
                    status=True,
                    file_size=humanized_size,
                )

        effective_size = file_size - buffer_size * 2
        step = effective_size // (segments - 2)

        with item.open("rb") as f:
            md5_hash.update(f.read(buffer_size))

            offset = buffer_size
            for _ in range(segments - 2):
                offset += step
                if offset + buffer_size >= file_size:
                    break

                f.seek(offset)
                md5_hash.update(f.read(buffer_size))

            f.seek(file_size - buffer_size)
            md5_hash.update(f.read(buffer_size))

        return MD5Result(
            path=item,
            message="Success",
            md5=md5_hash.hexdigest(),
            file_size=humanized_size,
            status=True,
        )
    except Exception as e:
        print(f"[red bold][✗]Failed to calculate MD5 for {item}: {e}[/]")
        return MD5Result(
            path=item, message=str(e), md5="", file_size="0 B", status=False
        )


def calc_full_md5(item: Path) -> MD5Result:
    md5_hash = hashlib.md5()
    try:
        file_size: int = item.stat().st_size
        humanized_size: str = humanize.naturalsize(file_size)

        with item.open("rb") as f:
            while chunk := f.read(8 * 1024 * 1024):
                md5_hash.update(chunk)

        return MD5Result(
            path=item,
            message="Success",
            md5=md5_hash.hexdigest(),
            status=True,
            file_size=humanized_size,
        )
    except Exception as e:
        print(f"[red bold][✗]Failed to calculate MD5 for {item}: {e}[/]")
        return MD5Result(
            path=item, message=str(e), md5="", file_size="0 B", status=False
        )
