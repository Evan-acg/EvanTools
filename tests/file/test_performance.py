import time
from pathlib import Path

from evan_tools.file import PathGatherer, SortBy


def _populate_tree(root: Path, keep_dirs: int = 30, skip_dirs: int = 5, files_per_dir: int = 20) -> int:
    for idx in range(keep_dirs):
        batch_dir = root / f"batch_{idx}"
        batch_dir.mkdir(parents=True, exist_ok=True)
        for file_idx in range(files_per_dir):
            (batch_dir / f"file_{idx}_{file_idx}.txt").write_text("x" * 64)

    for idx in range(skip_dirs):
        skip_dir = root / f"skip_{idx}"
        skip_dir.mkdir(parents=True, exist_ok=True)
        for file_idx in range(files_per_dir):
            (skip_dir / f"skip_{idx}_{file_idx}.txt").write_text("y" * 64)

    return keep_dirs * files_per_dir


def test_path_gatherer_performance(tmp_path):
    dataset_root = tmp_path / "dataset"
    expected_count = _populate_tree(dataset_root)

    baseline = PathGatherer([dataset_root], deep=True).exclude("skip_*")
    start = time.perf_counter()
    paths = list(baseline.gather())
    elapsed = time.perf_counter() - start

    sorted_gatherer = PathGatherer([dataset_root], deep=True).exclude("skip_*").sort_by(SortBy.NAME)
    start_sorted = time.perf_counter()
    sorted_paths = list(sorted_gatherer.gather())
    elapsed_sorted = time.perf_counter() - start_sorted

    assert len(paths) == expected_count
    assert len(sorted_paths) == expected_count
    assert elapsed < 2.5
    assert elapsed_sorted < 3.0
