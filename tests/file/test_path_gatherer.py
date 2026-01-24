import os
import time
from pathlib import Path

import pytest

from evan_tools.file import PathGatherer, SortBy, gather_paths


@pytest.fixture
def temp_dir(tmp_path):
    now = time.time()
    root = tmp_path / "workspace"
    root.mkdir()

    def write_text(path: Path, content: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def write_bytes(path: Path, content: bytes) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    write_text(root / "a.txt", "a")
    write_text(root / "b.py", "print('b')\n")
    write_text(root / "c.log", "log")
    write_text(root / "small.dat", "s")
    write_text(root / "large.dat", "l" * 64)

    old_time = now - 3600
    old_log = write_text(root / "old.log", "old")
    os.utime(old_log, (old_time, old_time))

    fresh_log = write_text(root / "fresh.log", "fresh")
    os.utime(fresh_log, (now, now))

    write_text(root / "sub1" / "d.txt", "data")
    write_text(root / "sub1" / "e.py", "print('e')\n")
    write_text(root / "sub1" / "nested" / "f.md", "nested")

    write_text(root / "sub2" / "keep.tmp", "tmp")
    write_bytes(root / "sub2" / "big.bin", b"z" * 80)

    return {"root": root, "now": now}


def test_default_flat_gather_files_only(temp_dir):
    root = temp_dir["root"]

    gatherer = PathGatherer([root])
    names = {path.name for path in gatherer.gather()}

    assert names == {
        "a.txt",
        "b.py",
        "c.log",
        "small.dat",
        "large.dat",
        "old.log",
        "fresh.log",
    }


def test_recursive_collects_all_files(temp_dir):
    root = temp_dir["root"]

    gatherer = PathGatherer([root], deep=True)
    names = {path.relative_to(root).as_posix() for path in gatherer.gather()}

    assert names == {
        "a.txt",
        "b.py",
        "c.log",
        "small.dat",
        "large.dat",
        "old.log",
        "fresh.log",
        "sub1/d.txt",
        "sub1/e.py",
        "sub1/nested/f.md",
        "sub2/keep.tmp",
        "sub2/big.bin",
    }


def test_depth_limit_excludes_nested_beyond_max(temp_dir):
    root = temp_dir["root"]

    gatherer = PathGatherer([root], deep=1)
    names = {path.relative_to(root).as_posix() for path in gatherer.gather()}

    assert "sub1/nested/f.md" not in names
    assert "sub1/d.txt" in names
    assert "sub2/big.bin" in names


def test_pattern_filtering(temp_dir):
    root = temp_dir["root"]

    gatherer = PathGatherer([root], deep=True).pattern("*.py")
    names = {path.name for path in gatherer.gather()}

    assert names == {"b.py", "e.py"}


def test_exclude_patterns(temp_dir):
    root = temp_dir["root"]

    gatherer = PathGatherer([root], deep=True).pattern("*.txt", "*.md").exclude("d.txt", "*.md")
    names = {path.name for path in gatherer.gather()}

    assert names == {"a.txt"}


def test_sort_by_name(temp_dir):
    root = temp_dir["root"]

    gatherer = PathGatherer([root]).pattern("*.log").sort_by(SortBy.NAME)
    names = [path.name for path in gatherer.gather()]

    assert names == ["c.log", "fresh.log", "old.log"]


def test_sort_by_size_desc(temp_dir):
    root = temp_dir["root"]

    gatherer = PathGatherer([root]).pattern("*.dat").sort_by(SortBy.SIZE, reverse=True)
    names = [path.name for path in gatherer.gather()]

    assert names == ["large.dat", "small.dat"]


def test_filter_by_size_range(temp_dir):
    root = temp_dir["root"]

    gatherer = (
        PathGatherer([root], deep=True)
        .pattern("*.bin", "*.dat")
        .filter_by(size_min=10, size_max=70)
    )
    names = {path.name for path in gatherer.gather()}

    assert names == {"large.dat"}


def test_filter_by_mtime_range(temp_dir):
    root = temp_dir["root"]
    now = temp_dir["now"]

    gatherer = PathGatherer([root]).pattern("*.log").filter_by(mtime_after=now - 120)
    names = {path.name for path in gatherer.gather()}

    assert names == {"c.log", "fresh.log"}


def test_progress_callback_invoked(temp_dir):
    root = temp_dir["root"]

    counts: list[int] = []

    def on_progress(count: int) -> None:
        counts.append(count)

    gatherer = PathGatherer([root], deep=True).on_progress(on_progress)
    paths = list(gatherer.gather())

    assert counts
    assert counts[-1] == len(paths)
    assert counts == sorted(counts)


def test_chainable_configuration(temp_dir):
    root = temp_dir["root"]

    gatherer = PathGatherer([root], deep=True)
    chained = (
        gatherer
        .pattern("*.py")
        .exclude("e.py")
        .sort_by(SortBy.NAME)
        .filter_by(size_min=0)
        .on_progress(lambda _: None)
    )

    names = [path.name for path in chained.gather()]

    assert chained is gatherer
    assert names == ["b.py"]


def test_gather_paths_backward_compatibility(temp_dir):
    root = temp_dir["root"]

    files = {path.relative_to(root).as_posix() for path in gather_paths([root], deep=True)}
    dirs = {path.relative_to(root).as_posix() for path in gather_paths([root], deep=True, dir_only=True)}
    py_files = {
        path.relative_to(root).as_posix()
        for path in gather_paths([root], deep=True, filter=lambda p: p.suffix == ".py")
    }

    assert "sub1/nested/f.md" in files
    assert "sub1" in dirs and "sub1/nested" in dirs
    assert py_files == {"b.py", "sub1/e.py"}
