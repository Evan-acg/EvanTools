# PathGatherer usage

This module provides two entry points:
- `PathGatherer`: chainable builder for advanced filtering, sorting, and callbacks.
- `gather_paths`: lightweight helper kept for backward compatibility and quick scans.

## Quick start

```python
from evan_tools.file import PathGatherer, SortBy

paths = (
    PathGatherer(["./data"], deep=True)
    .pattern("*.py", "*.md")
    .exclude("__pycache__", "*.pyc")
    .filter_by(size_min=512)
    .sort_by(SortBy.MTIME, reverse=True)
    .gather()
)

for path in paths:
    print(path)
```

## Configuration reference

- `deep`: `False` for flat scan, `True` for unlimited recursion, or an `int` depth limit.
- `pattern(*patterns)`: include-only glob patterns (example: `"*.py"`, `"test_*.txt"`).
- `exclude(*patterns)`: glob patterns to skip (directories matching these are also pruned in recursive mode).
- `sort_by(key, reverse=False)`: order results by `SortBy.NAME`, `SIZE`, `MTIME`, `CTIME`, or `EXTENSION`.
- `filter_by(...)`: filter by size (`size_min`, `size_max`) or modification time (`mtime_after`, `mtime_before`).
- `on_progress(callback)`: receive progress counts as results are yielded.
- `errors`: list of `(Path, Exception)` collected during traversal (non-blocking).

## Common recipes

### Collect recent files under a limit

```python
from evan_tools.file import PathGatherer, SortBy
import time

one_day_ago = time.time() - 24 * 3600
recent = (
    PathGatherer(["./logs"], deep=True)
    .pattern("*.log")
    .filter_by(mtime_after=one_day_ago, size_max=5_000_000)
    .sort_by(SortBy.MTIME, reverse=True)
)

for path in recent.gather():
    print(path)
```

### Show progress while scanning

```python
def show_progress(count: int) -> None:
    if count % 500 == 0:
        print(f"found {count} files so far")

finder = PathGatherer(["/var/data"], deep=True).on_progress(show_progress)
files = list(finder.gather())

if finder.errors:
    print(f"encountered {len(finder.errors)} errors")
```

### Backward compatibility

`gather_paths` retains the original simple interface:

```python
from evan_tools.file import gather_paths

# flat scan
flat = list(gather_paths(["."]))

# recursive directories only, with a quick filter
folders = list(gather_paths(["./data"], deep=True, dir_only=True))
py_files = list(gather_paths(["./data"], deep=2, filter=lambda p: p.suffix == ".py"))
```

## Performance tips

- Prefer `exclude()` to prune large subtrees early.
- Avoid `sort_by` when order is irrelevant; it materializes the entire result set.
- Use numeric `deep` limits for wide trees to reduce traversal.
- Keep callbacks light; they run for every emitted path.
